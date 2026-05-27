"""统计分析 API"""
from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.domain.models.user import User
from app.domain.models.session import Session
from app.domain.models.message import Message
from app.domain.models.user_stats import UserStats
from app.api.v1.admin.deps import require_admin

router = APIRouter()


@router.get("/overview")
async def stats_overview(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """统计总览"""
    # 用户总数
    total_users = (await db.execute(
        select(func.count()).select_from(User)
    )).scalar() or 0

    # 活跃用户数
    active_users = (await db.execute(
        select(func.count()).select_from(User).where(User.is_active == True)
    )).scalar() or 0

    # 今日新增用户
    today = date.today()
    today_new_users = (await db.execute(
        select(func.count()).select_from(User)
        .where(cast(User.created_at, Date) == today)
    )).scalar() or 0

    # 会话总数
    total_sessions = (await db.execute(
        select(func.count()).select_from(Session)
    )).scalar() or 0

    # 今日新增会话
    today_sessions = (await db.execute(
        select(func.count()).select_from(Session)
        .where(cast(Session.created_at, Date) == today)
    )).scalar() or 0

    # 消息总数
    total_messages = (await db.execute(
        select(func.count()).select_from(Message)
    )).scalar() or 0

    # 今日消息数
    today_messages = (await db.execute(
        select(func.count()).select_from(Message)
        .where(cast(Message.created_at, Date) == today)
    )).scalar() or 0

    # 总 token 消耗
    total_tokens = (await db.execute(
        select(func.coalesce(func.sum(Message.tokens_used), 0))
    )).scalar() or 0

    # 今日 token 消耗
    today_tokens = (await db.execute(
        select(func.coalesce(func.sum(Message.tokens_used), 0))
        .where(cast(Message.created_at, Date) == today)
    )).scalar() or 0

    # 平均每会话消息数
    avg_messages = round(total_messages / total_sessions, 1) if total_sessions > 0 else 0

    return {
        "code": 0,
        "data": {
            "users": {
                "total": total_users,
                "active": active_users,
                "today_new": today_new_users,
            },
            "sessions": {
                "total": total_sessions,
                "today_new": today_sessions,
            },
            "messages": {
                "total": total_messages,
                "today": today_messages,
                "avg_per_session": avg_messages,
            },
            "tokens": {
                "total": total_tokens,
                "today": today_tokens,
            },
        },
    }


@router.get("/daily")
async def stats_daily(
    days: int = Query(7, ge=1, le=90, description="查询天数"),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """每日趋势数据"""
    today = date.today()
    start_date = today - timedelta(days=days - 1)

    # 每日新用户
    new_users_result = await db.execute(
        select(
            cast(User.created_at, Date).label("day"),
            func.count().label("count"),
        )
        .where(cast(User.created_at, Date) >= start_date)
        .group_by("day")
        .order_by("day")
    )
    new_users_map = {str(row.day): row.count for row in new_users_result}

    # 每日会话数
    sessions_result = await db.execute(
        select(
            cast(Session.created_at, Date).label("day"),
            func.count().label("count"),
        )
        .where(cast(Session.created_at, Date) >= start_date)
        .group_by("day")
        .order_by("day")
    )
    sessions_map = {str(row.day): row.count for row in sessions_result}

    # 每日消息数 & token 消耗
    messages_result = await db.execute(
        select(
            cast(Message.created_at, Date).label("day"),
            func.count().label("count"),
            func.coalesce(func.sum(Message.tokens_used), 0).label("tokens"),
        )
        .where(cast(Message.created_at, Date) >= start_date)
        .group_by("day")
        .order_by("day")
    )
    messages_map = {}
    tokens_map = {}
    for row in messages_result:
        day_str = str(row.day)
        messages_map[day_str] = row.count
        tokens_map[day_str] = row.tokens

    # 组装每日数据
    daily_data = []
    for i in range(days):
        d = start_date + timedelta(days=i)
        day_str = str(d)
        daily_data.append({
            "date": day_str,
            "new_users": new_users_map.get(day_str, 0),
            "sessions": sessions_map.get(day_str, 0),
            "messages": messages_map.get(day_str, 0),
            "tokens": tokens_map.get(day_str, 0),
        })

    return {
        "code": 0,
        "data": {
            "days": days,
            "items": daily_data,
        },
    }
