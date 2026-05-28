"""角色模型"""
from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Role(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """系统角色"""
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    status: Mapped[int] = mapped_column(Integer, default=1, comment="1=启用 0=禁用")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    menu_ids: Mapped[str | None] = mapped_column(Text, nullable=True, comment="JSON数组,关联菜单ID")

    def __repr__(self) -> str:
        return f"<Role {self.name}>"
