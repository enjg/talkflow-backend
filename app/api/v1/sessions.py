"""会话管理 API"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.domain.schemas.session import SessionCreateRequest
from app.middleware.auth_middleware import get_current_user
from app.services.session_service import session_service

router = APIRouter()


@router.get("")
async def list_sessions(
    page: int = 1, size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取会话列表"""
    items, total = await session_service.list_sessions(db, current_user.id, page, size)
    return {"code": 0, "data": {"items": items, "total": total, "page": page, "size": size}}


@router.post("")
async def create_session(
    req: SessionCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """创建新会话"""
    session = await session_service.create(db, current_user.id, req.title, req.topic, req.reply_lang)
    return {"code": 0, "data": {
        "id": str(session.id), "title": session.title,
        "topic": session.topic, "reply_lang": session.reply_lang,
        "updated_at": session.updated_at.isoformat(),
    }}


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取单个会话"""
    session = await session_service.get(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"code": 0, "data": {"id": str(session.id), "title": session.title, "topic": session.topic}}


@router.delete("/{session_id}")
async def delete_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """删除会话"""
    await session_service.delete(db, session_id)
    return {"code": 0, "message": "已删除"}
