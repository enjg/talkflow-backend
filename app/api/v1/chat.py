"""对话 API — SSE 流式对话"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.domain.schemas.chat import ChatSendRequest
from app.middleware.auth_middleware import get_current_user
from app.services.chat_service import chat_service
from app.repositories.message_repo import MessageRepository

router = APIRouter()

@router.get("/history/{session_id}")
async def get_history(
    session_id: str,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取会话消息历史"""
    from uuid import UUID
    repo = MessageRepository(db)
    messages, total = await repo.get_session_messages(UUID(session_id), page, page_size)
    return {
        "code": 0,
        "data": {
            "messages": [
                {
                    "id": str(m.id),
                    "role": m.role,
                    "content": m.content,
                    "lang": m.lang,
                    "emotion": getattr(m, "emotion", None),
                    "created_at": str(m.created_at),
                }
                for m in messages
            ],
            "total": total,
        },
    }


@router.post("/send")
async def send_message(
    req: ChatSendRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """发送文字消息（SSE 流式响应）"""
    async def event_generator():
        async for chunk in chat_service.send_text_message(
            session=db, session_id=str(req.session_id),
            user_id=current_user.id, message=req.message,
            reply_lang=req.reply_lang,
            enable_voice=req.enable_voice,
            voice_id=req.voice_id,
        ):
            yield chunk

    return StreamingResponse(
        event_generator(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/audio")
async def send_audio(
    session_id: str = Form(...),
    reply_lang: str = Form(None),
    audio: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """发送语音消息"""
    audio_bytes = await audio.read()

    async def event_generator():
        async for chunk in chat_service.send_audio_message(
            session=db, session_id=UUID(session_id),
            user_id=current_user.id, audio_bytes=audio_bytes,
            reply_lang=reply_lang,
        ):
            yield chunk

    return StreamingResponse(
        event_generator(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
