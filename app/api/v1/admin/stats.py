"""管理端 - 统计数据"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from ....dependencies import get_db
from ....domain.models.user import User
from ....domain.models.session import Session
from ....domain.models.message import Message

router = APIRouter()
CST = timezone(timedelta(hours=8))


@router.get("/stats/overview")
async def stats_overview(db: AsyncSession = Depends(get_db)):
    """统计总览"""
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    active_users = (await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )).scalar() or 0
    total_sessions = (await db.execute(select(func.count(Session.id)))).scalar() or 0
    total_messages = (await db.execute(select(func.count(Message.id)))).scalar() or 0

    # 今日新增
    today = datetime.now(CST).replace(hour=0, minute=0, second=0, microsecond=0)
    new_users_today = (await db.execute(
        select(func.count(User.id)).where(User.created_at >= today)
    )).scalar() or 0
    new_sessions_today = (await db.execute(
        select(func.count(Session.id)).where(Session.created_at >= today)
    )).scalar() or 0

    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_sessions": total_sessions,
        "total_messages": total_messages,
        "new_users_today": new_users_today,
        "new_sessions_today": new_sessions_today,
    }


@router.get("/stats/daily")
async def stats_daily(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """每日趋势"""
    start = datetime.now(CST) - timedelta(days=days)

    # 每日新用户
    result = await db.execute(
        select(
            cast(User.created_at, Date).label("date"),
            func.count(User.id).label("count"),
        )
        .where(User.created_at >= start)
        .group_by(cast(User.created_at, Date))
        .order_by(cast(User.created_at, Date))
    )
    daily_users = [{"date": str(r[0]), "count": r[1]} for r in result.all()]

    # 每日新会话
    result = await db.execute(
        select(
            cast(Session.created_at, Date).label("date"),
            func.count(Session.id).label("count"),
        )
        .where(Session.created_at >= start)
        .group_by(cast(Session.created_at, Date))
        .order_by(cast(Session.created_at, Date))
    )
    daily_sessions = [{"date": str(r[0]), "count": r[1]} for r in result.all()]

    # 每日消息
    result = await db.execute(
        select(
            cast(Message.created_at, Date).label("date"),
            func.count(Message.id).label("count"),
        )
        .where(Message.created_at >= start)
        .group_by(cast(Message.created_at, Date))
        .order_by(cast(Message.created_at, Date))
    )
    daily_messages = [{"date": str(r[0]), "count": r[1]} for r in result.all()]

    return {
        "daily_users": daily_users,
        "daily_sessions": daily_sessions,
        "daily_messages": daily_messages,
    }
