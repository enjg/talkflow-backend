"""会话服务"""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from ..repositories.session_repo import SessionRepository


class SessionService:
    """会话管理服务"""

    async def create(self, session: AsyncSession, user_id, title="新对话", topic=None, reply_lang="auto"):
        repo = SessionRepository(session)
        uid = user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
        return await repo.create(user_id=uid, title=title, topic=topic, reply_lang=reply_lang)

    async def list_sessions(self, session: AsyncSession, user_id, page=1, size=20):
        repo = SessionRepository(session)
        uid = user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
        return await repo.get_user_sessions(uid, page, size)

    async def get(self, session: AsyncSession, session_id):
        repo = SessionRepository(session)
        sid = session_id if isinstance(session_id, uuid.UUID) else uuid.UUID(str(session_id))
        return await repo.get_by_id(sid)

    async def delete(self, session: AsyncSession, session_id):
        repo = SessionRepository(session)
        sid = session_id if isinstance(session_id, uuid.UUID) else uuid.UUID(str(session_id))
        return await repo.delete(sid)


session_service = SessionService()
