"""会员模型"""
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Member(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """会员信息"""
    __tablename__ = "members"

    user_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True, comment="关联用户ID")
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    points_balance: Mapped[int] = mapped_column(Integer, default=0, comment="积分余额")
    level: Mapped[int] = mapped_column(Integer, default=1, comment="会员等级")
    status: Mapped[int] = mapped_column(Integer, default=1, comment="1=正常 0=冻结")

    def __repr__(self) -> str:
        return f"<Member user={self.user_id}>"
