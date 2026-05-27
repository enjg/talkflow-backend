"""自定义角色模型"""
import uuid
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserCharacter(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """用户自定义角色"""
    __tablename__ = "user_characters"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar: Mapped[str] = mapped_column(String(10), default="🎭")
    description: Mapped[str] = mapped_column(String(500), default="")
    language: Mapped[str] = mapped_column(String(10), default="zh")
    system_prompt: Mapped[str] = mapped_column(Text, default="")
    voice_id_zh: Mapped[str] = mapped_column(String(50), default="白桦")
    voice_id_en: Mapped[str] = mapped_column(String(50), default="Guy")
    tts_style_zh: Mapped[str] = mapped_column(String(500), default="")
    tts_style_en: Mapped[str] = mapped_column(String(500), default="")

    # 关系
    user = relationship("User", back_populates="characters")

    def __repr__(self) -> str:
        return f"<UserCharacter {self.name}>"
