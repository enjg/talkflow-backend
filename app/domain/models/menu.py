"""菜单模型"""
import uuid
from sqlalchemy import String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Menu(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """系统菜单"""
    __tablename__ = "menus"

    parent_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    path: Mapped[str | None] = mapped_column(String(200), nullable=True)
    component: Mapped[str | None] = mapped_column(String(200), nullable=True)
    icon: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sort: Mapped[int] = mapped_column(Integer, default=0)
    visible: Mapped[bool] = mapped_column(Boolean, default=True)
    type: Mapped[str] = mapped_column(String(20), default="menu", comment="menu/button")
    permission: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="权限标识")

    def __repr__(self) -> str:
        return f"<Menu {self.name}>"
