"""对话管理 API"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.domain.models.session import Session
from app.domain.models.message import Message
from app.api.v1.admin.deps import require_admin

router = APIRouter()


def _session_dict(s: Session) -> dict:
    """序列化会话"""
    return {
        "id": str(s.id),
        "user_id": str(s.user_id),
        "title": s.title,
        "character_id": s.character_id,
        "topic": s.topic,
        "reply_lang": s.reply_lang,
        "is_active": s.is_active,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


def _msg_dict(m: Message) -> dict:
    """序列化消息"""
    return {
        "id": str(m.id),
        "role": m.role,
        "content": m.content,
        "lang": m.lang,
        "emotion": m.emotion,
        "audio_url": m.audio_url,
        "tokens_used": m.tokens_used,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


# ===== Endpoints =====
@router.get("")
async def list_conversations(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: Optional[uuid.UUID] = None,
    character_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """对话列表（分页）"""
    query = select(Session)
    count_query = select(func.count()).select_from(Session)

    if user_id:
        query = query.where(Session.user_id == user_id)
        count_query = count_query.where(Session.user_id == user_id)
    if character_id:
        query = query.where(Session.character_id == character_id)
        count_query = count_query.where(Session.character_id == character_id)

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(Session.updated_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    sessions = result.scalars().all()

    return {
        "code": 0,
        "data": {
            "items": [_session_dict(s) for s in sessions],
            "total": total,
            "page": page,
            "size": size,
        },
    }


@router.get("/{session_id}")
async def get_conversation(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """对话详情 + 消息列表"""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        return {"code": 404, "message": "对话不存在"}

    # 获取消息
    msg_result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )
    messages = msg_result.scalars().all()

    data = _session_dict(session)
    data["messages"] = [_msg_dict(m) for m in messages]
    data["message_count"] = len(messages)

    return {"code": 0, "data": data}


@router.delete("/{session_id}")
async def delete_conversation(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """删除对话"""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        return {"code": 404, "message": "对话不存在"}

    await db.delete(session)
    await db.commit()
    return {"code": 0, "message": "对话已删除"}
