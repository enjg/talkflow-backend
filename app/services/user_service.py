"""用户服务"""
import uuid
from datetime import date, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from ..repositories.user_repo import UserRepository
from ..domain.models.user_stats import UserStats


class UserService:
    """用户信息服务"""

    async def get_profile(self, session: AsyncSession, user_id: uuid.UUID):
        """获取用户信息"""
        repo = UserRepository(session)
        return await repo.get_by_id(user_id)

    async def update_profile(self, session: AsyncSession, user_id: uuid.UUID, **kwargs):
        """更新用户信息"""
        repo = UserRepository(session)
        return await repo.update(user_id, **kwargs)

    async def get_stats(self, session: AsyncSession, user_id: uuid.UUID, days: int = 7):
        """获取学习统计"""
        start_date = date.today() - timedelta(days=days)
        result = await session.execute(
            select(UserStats)
            .where(UserStats.user_id == user_id, UserStats.date >= start_date)
            .order_by(UserStats.date.desc())
        )
        stats = result.scalars().all()

        total_duration = sum(s.duration_seconds for s in stats)
        total_messages = sum(s.message_count for s in stats)
        # 连续天数
        streak = 0
        today = date.today()
        for i in range(days):
            d = today - timedelta(days=i)
            if any(s.date == d for s in stats):
                streak += 1
            else:
                break

        daily = [{"date": str(s.date), "duration": s.duration_seconds, "messages": s.message_count} for s in stats]
        return {"total_duration": total_duration, "total_messages": total_messages, "streak_days": streak, "daily": daily}


user_service = UserService()
