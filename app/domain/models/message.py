"""消息模型"""
import uuid
from datetime import datetime
from sqlalchemy import String, Text, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, UUIDPrimaryKeyMixin


class Message(UUIDPrimaryKeyMixin, Base):
    """对话消息模型"""
    __tablename__ = "messages"

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(10), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    lang: Mapped[str | None] = mapped_column(String(10), nullable=True)
    emotion: Mapped[str | None] = mapped_column(String(20), nullable=True)
    audio_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session = relationship("Session", back_populates="messages")
