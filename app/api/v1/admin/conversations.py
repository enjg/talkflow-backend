"""管理端 - 对话管理"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from ....dependencies import get_db
from ....domain.models.session import Session
from ....domain.models.message import Message
from ....domain.models.user import User

router = APIRouter()


@router.get("/conversations")
async def list_conversations(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    keyword: str = Query("", description="搜索关键词"),
    db: AsyncSession = Depends(get_db),
):
    """对话列表"""
    query = select(Session)
    count_query = select(func.count(Session.id))

    if keyword:
        filter_cond = or_(
            Session.title.contains(keyword),
            Session.character_id.contains(keyword),
        )
        query = query.where(filter_cond)
        count_query = count_query.where(filter_cond)

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(Session.created_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    sessions = result.scalars().all()

    # 获取关联用户信息
    items = []
    for s in sessions:
        user = await db.get(User, s.user_id)
        # 获取消息数
        msg_count = (await db.execute(
            select(func.count(Message.id)).where(Message.session_id == s.id)
        )).scalar() or 0

        items.append({
            "id": str(s.id),
            "title": s.title,
            "character_id": s.character_id,
            "user_nickname": user.nickname if user else "未知",
            "message_count": msg_count,
            "is_active": s.is_active,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })

    return {"total": total, "page": page, "size": size, "items": items}


@router.get("/conversations/{session_id}")
async def get_conversation(session_id: str, db: AsyncSession = Depends(get_db)):
    """对话详情 + 消息列表"""
    from uuid import UUID
    session = await db.get(Session, UUID(session_id))
    if not session:
        raise HTTPException(404, "会话不存在")

    # 获取消息
    result = await db.execute(
        select(Message).where(Message.session_id == session.id).order_by(Message.created_at)
    )
    messages = result.scalars().all()

    return {
        "session": {
            "id": str(session.id),
            "title": session.title,
            "character_id": session.character_id,
            "topic": session.topic,
            "created_at": session.created_at.isoformat() if session.created_at else None,
        },
        "messages": [
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "lang": m.lang,
                "emotion": m.emotion,
                "tokens_used": m.tokens_used,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ],
    }


@router.delete("/conversations/{session_id}")
async def delete_conversation(session_id: str, db: AsyncSession = Depends(get_db)):
    """删除对话"""
    from uuid import UUID
    session = await db.get(Session, UUID(session_id))
    if not session:
        raise HTTPException(404, "会话不存在")
    await db.delete(session)
    await db.commit()
    return {"ok": True}
