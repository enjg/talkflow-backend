"""用户数据仓库"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .base import BaseRepository
from ..domain.models.user import User


class UserRepository(BaseRepository[User]):
    """用户仓库，提供用户相关查询"""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_nickname(self, nickname: str) -> User | None:
        """根据昵称查询用户"""
        result = await self.session.execute(
            select(User).where(User.nickname == nickname)
        )
        return result.scalar_one_or_none()

    async def get_by_wechat(self, openid: str) -> User | None:
        """根据微信 OpenID 查询用户"""
        result = await self.session.execute(
            select(User).where(User.wechat_openid == openid)
        )
        return result.scalar_one_or_none()

    async def nickname_exists(self, nickname: str) -> bool:
        """检查昵称是否已存在"""
        result = await self.session.execute(
            select(User.id).where(User.nickname == nickname)
        )
        return result.scalar_one_or_none() is not None
