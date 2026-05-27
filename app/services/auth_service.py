"""认证服务"""
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from ..config import settings
from ..repositories.user_repo import UserRepository
from ..domain.models.user import User

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """用户认证服务"""

    def hash_password(self, password: str) -> str:
        """哈希密码"""
        return pwd_context.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain, hashed)

    def create_token(self, user_id: str, expires_delta: timedelta | None = None) -> str:
        """创建 JWT Token"""
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES))
        payload = {"sub": user_id, "exp": expire}
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    def verify_token(self, token: str) -> str | None:
        """验证 Token，返回 user_id"""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            return payload.get("sub")
        except JWTError:
            return None

    async def register(self, session: AsyncSession, nickname: str, password: str, wechat_openid: str | None = None) -> dict:
        """用户注册"""
        repo = UserRepository(session)
        if await repo.nickname_exists(nickname):
            raise ValueError("昵称已存在")
        user = await repo.create(
            nickname=nickname,
            hashed_password=self.hash_password(password),
            wechat_openid=wechat_openid,
        )
        access_token = self.create_token(str(user.id))
        refresh_token = self.create_token(str(user.id), timedelta(days=7))
        return {"user_id": user.id, "access_token": access_token, "refresh_token": refresh_token}

    async def login(self, session: AsyncSession, nickname: str, password: str) -> dict:
        """用户登录"""
        repo = UserRepository(session)
        user = await repo.get_by_nickname(nickname)
        if not user or not self.verify_password(password, user.hashed_password):
            raise ValueError("用户名或密码错误")
        access_token = self.create_token(str(user.id))
        refresh_token = self.create_token(str(user.id), timedelta(days=7))
        return {"user_id": user.id, "access_token": access_token, "refresh_token": refresh_token}

    def refresh(self, refresh_token: str) -> dict:
        """刷新 Token"""
        user_id = self.verify_token(refresh_token)
        if not user_id:
            raise ValueError("Token 无效或已过期")
        new_access = self.create_token(user_id)
        new_refresh = self.create_token(user_id, timedelta(days=7))
        return {"access_token": new_access, "refresh_token": new_refresh}


# 全局单例
auth_service = AuthService()
