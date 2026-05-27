"""消息数据仓库"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from .base import BaseRepository
from ..domain.models.message import Message


class MessageRepository(BaseRepository[Message]):
    """消息仓库"""

    def __init__(self, session: AsyncSession):
        super().__init__(Message, session)

    async def get_session_messages(
        self, session_id: uuid.UUID, page: int = 1, size: int = 50
    ) -> tuple[list[Message], int]:
        """获取会话的消息列表（按时间正序）"""
        count_result = await self.session.execute(
            select(func.count()).select_from(Message).where(
                Message.session_id == session_id
            )
        )
        total = count_result.scalar() or 0

        result = await self.session.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at)
            .offset((page - 1) * size)
            .limit(size)
        )
        messages = result.scalars().all()
        return list(messages), total

    async def get_recent_messages(
        self, session_id: uuid.UUID, limit: int = 20
    ) -> list[Message]:
        """获取最近 N 条消息（用于 AI 上下文窗口）
        
        返回正序列表（从旧到新）
        """
        result = await self.session.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(desc(Message.created_at))
            .limit(limit)
        )
        messages = list(result.scalars().all())
        messages.reverse()  # 转为正序
        return messages
