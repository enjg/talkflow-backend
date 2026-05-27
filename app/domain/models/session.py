"""会话模型"""
import uuid
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Session(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """对话会话模型"""
    __tablename__ = "sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), default="新对话")
    character_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    topic: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reply_lang: Mapped[str] = mapped_column(String(10), default="auto")
    voice_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 关系
    user = relationship("User", back_populates="sessions")
    messages = relationship(
        "Message", back_populates="session", lazy="selectin",
        order_by="Message.created_at"
    )

    def __repr__(self) -> str:
        return f"<Session {self.title}>"
