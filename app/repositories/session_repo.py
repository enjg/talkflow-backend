"""会话数据仓库"""
import uuid
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from .base import BaseRepository
from ..domain.models.session import Session
from ..domain.models.message import Message


class SessionRepository(BaseRepository[Session]):
    """会话仓库"""

    def __init__(self, session: AsyncSession):
        super().__init__(Session, session)

    async def get_user_sessions(
        self, user_id: uuid.UUID, page: int = 1, size: int = 20
    ) -> tuple[list[dict], int]:
        """获取用户的会话列表（带最后一条消息和消息数）"""
        # 总数
        count_result = await self.session.execute(
            select(func.count()).select_from(Session).where(
                Session.user_id == user_id, Session.is_active == True
            )
        )
        total = count_result.scalar() or 0

        # 会话列表
        result = await self.session.execute(
            select(Session)
            .where(Session.user_id == user_id, Session.is_active == True)
            .order_by(desc(Session.updated_at))
            .offset((page - 1) * size)
            .limit(size)
        )
        sessions = result.scalars().all()

        items = []
        for s in sessions:
            # 获取最后一条消息
            last_msg_result = await self.session.execute(
                select(Message.content)
                .where(Message.session_id == s.id)
                .order_by(desc(Message.created_at))
                .limit(1)
            )
            last_msg = last_msg_result.scalar_one_or_none()

            # 获取消息数
            msg_count_result = await self.session.execute(
                select(func.count()).select_from(Message).where(
                    Message.session_id == s.id
                )
            )
            msg_count = msg_count_result.scalar() or 0

            items.append({
                "id": s.id,
                "title": s.title,
                "topic": s.topic,
                "reply_lang": s.reply_lang,
                "message_count": msg_count,
                "last_message": last_msg,
                "updated_at": s.updated_at,
            })

        return items, total
