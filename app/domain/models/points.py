"""积分模型"""
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PointsRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """积分规则"""
    __tablename__ = "points_rules"

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="规则名称")
    type: Mapped[str] = mapped_column(String(50), nullable=False, comment="规则类型: daily_signin/chat/message/invite")
    gain_or_consume: Mapped[str] = mapped_column(String(10), nullable=False, comment="gain=获取 consume=消耗")
    points: Mapped[int] = mapped_column(Integer, nullable=False, comment="积分数量")
    daily_limit: Mapped[int] = mapped_column(Integer, default=0, comment="每日上限,0=不限")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<PointsRule {self.name}>"


class Package(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """积分套餐"""
    __tablename__ = "packages"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    points: Mapped[int] = mapped_column(Integer, nullable=False, comment="包含积分")
    price: Mapped[int] = mapped_column(Integer, nullable=False, comment="价格(分)")
    duration_days: Mapped[int] = mapped_column(Integer, default=0, comment="有效期天数,0=永久")
    status: Mapped[int] = mapped_column(Integer, default=1, comment="1=上架 0=下架")

    def __repr__(self) -> str:
        return f"<Package {self.name}>"


class ActivationCode(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """激活码"""
    __tablename__ = "activation_codes"

    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    package_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, comment="关联套餐ID")
    status: Mapped[int] = mapped_column(Integer, default=0, comment="0=未使用 1=已使用 2=已过期")
    used_by: Mapped[str | None] = mapped_column(String(36), nullable=True, comment="使用用户ID")
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<ActivationCode {self.code}>"


class PointsLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """积分流水"""
    __tablename__ = "points_logs"

    member_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, comment="会员ID")
    type: Mapped[str] = mapped_column(String(20), nullable=False, comment="gain/consume")
    points: Mapped[int] = mapped_column(Integer, nullable=False, comment="积分变动")
    balance: Mapped[int] = mapped_column(Integer, nullable=False, comment="变动后余额")
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)

    def __repr__(self) -> str:
        return f"<PointsLog member={self.member_id} {self.type} {self.points}>"
