"""
WebSocket 处理器 - 实时对话连接管理。
"""
import json
import asyncio
import structlog
from typing import Dict, Set, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.security import decode_access_token
from app.core.events import get_db_session
from app.repositories.user_repo import UserRepository
from app.repositories.session_repo import SessionRepository
from app.repositories.message_repo import MessageRepository
from app.repositories.stats_repo import StatsRepository
from app.services.chat_service import ChatService
from app.services.ai.chat_engine import ChatEngine
from app.services.ai.stt_service import STTService
from app.services.ai.tts_service import TTSService
from app.services.ai.prompts import PromptManager

logger = structlog.get_logger()
router = APIRouter()

# 连接管理: session_id -> set of websockets
rooms: Dict[str, Set[WebSocket]] = {}


async def authenticate_ws(token: str) -> Optional[str]:
    """验证 WebSocket 连接的 JWT 令牌，返回用户 ID。"""
    payload = decode_access_token(token)
    if payload is None:
        return None
    return payload.get("sub")


@router.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    token: str = Query(...),
    session_id: str = Query(...),
):
    """
    WebSocket 实时对话端点。
    客户端发送: text_message, audio_message, config_update, interrupt
    服务端推送: text_chunk, audio_chunk, emotion, done, error
    """
    user_id = await authenticate_ws(token)
    if user_id is None:
        await websocket.close(code=4001, reason="认证失败")
        return

    await websocket.accept()

    # 加入房间
    if session_id not in rooms:
        rooms[session_id] = set()
    rooms[session_id].add(websocket)

    logger.info("WebSocket 连接建立", user_id=user_id, session_id=session_id)

    # 发送心跳
    heartbeat_task = asyncio.create_task(
        _heartbeat(websocket, session_id)
    )

    try:
        async with get_db_session() as db:
            user_repo = UserRepository(db)
            user = await user_repo.get_by_id(user_id)
            if user is None:
                await websocket.close(code=4001, reason="用户不存在")
                return

            chat_service = ChatService(
                db=db,
                user=user,
                message_repo=MessageRepository(db),
                session_repo=SessionRepository(db),
                stats_repo=StatsRepository(db),
                chat_engine=ChatEngine(),
                stt_service=STTService(),
                tts_service=TTSService(),
                prompt_manager=PromptManager(),
            )

            while True:
                data = await websocket.receive_json()
                msg_type = data.get("type")

                if msg_type == "text_message":
                    content = data.get("content", "")
                    async for chunk in chat_service.stream_text_reply(
                        session_id=session_id,
                        user_message=content,
                    ):
                        await websocket.send_json({
                            "type": "text_chunk",
                            "content": chunk,
                        })
                    await websocket.send_json({"type": "done"})

                elif msg_type == "audio_message":
                    import base64
                    audio_b64 = data.get("audio", "")
                    audio_data = base64.b64decode(audio_b64)
                    content_type = data.get("content_type", "audio/webm")
                    async for chunk in chat_service.stream_audio_reply(
                        session_id=session_id,
                        audio_data=audio_data,
                        content_type=content_type,
                    ):
                        await websocket.send_json({
                            "type": "text_chunk",
                            "content": chunk,
                        })
                    await websocket.send_json({"type": "done"})

                elif msg_type == "config_update":
                    # 更新会话配置（如语音、语言等）
                    await websocket.send_json({
                        "type": "config_updated",
                        "config": data.get("config", {}),
                    })

                elif msg_type == "interrupt":
                    # 中断当前回复（客户端请求中断）
                    await websocket.send_json({"type": "interrupted"})

    except WebSocketDisconnect:
        logger.info("WebSocket 断开", user_id=user_id, session_id=session_id)
    except Exception as e:
        logger.error("WebSocket 错误", error=str(e), exc_info=True)
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        heartbeat_task.cancel()
        rooms.get(session_id, set()).discard(websocket)
        if session_id in rooms and not rooms[session_id]:
            del rooms[session_id]
        try:
            await websocket.close()
        except Exception:
            pass


async def _heartbeat(websocket: WebSocket, session_id: str):
    """定期发送心跳保持连接。"""
    try:
        while True:
            await asyncio.sleep(30)
            await websocket.send_json({"type": "heartbeat"})
    except Exception:
        pass


websocket_router = router
