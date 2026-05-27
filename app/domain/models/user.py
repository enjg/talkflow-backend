"""用户模型"""
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """用户模型"""
    __tablename__ = "users"

    nickname: Mapped[str] = mapped_column(String(50), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    wechat_openid: Mapped[str | None] = mapped_column(
        String(100), unique=True, nullable=True, index=True
    )
    target_lang: Mapped[str] = mapped_column(String(10), default="en")
    native_lang: Mapped[str] = mapped_column(String(10), default="zh")
    level: Mapped[str] = mapped_column(String(20), default="intermediate")
    hashed_password: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    # 关系
    sessions = relationship("Session", back_populates="user", lazy="selectin")
    stats = relationship("UserStats", back_populates="user", lazy="selectin")
    characters = relationship("UserCharacter", back_populates="user", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User {self.nickname}>"
