"""用户学习统计模型"""
import uuid
from datetime import date, datetime
from sqlalchemy import String, Date, Integer, JSON, ForeignKey, UniqueConstraint, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, UUIDPrimaryKeyMixin


class UserStats(UUIDPrimaryKeyMixin, Base):
    """用户每日学习统计"""
    __tablename__ = "user_stats"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_user_stats_date"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    words_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user = relationship("User", back_populates="stats")
