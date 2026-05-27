"""系统设置模型"""
from sqlalchemy import String, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AdminSettings(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """系统设置模型"""
    __tablename__ = "admin_settings"

    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    value_type: Mapped[str] = mapped_column(String(20), default="string")  # string, int, bool, json
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否可公开访问

    def __repr__(self) -> str:
        return f"<AdminSettings {self.key}={self.value}>"
