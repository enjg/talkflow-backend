"""管理端 - 用户管理"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from ....dependencies import get_db
from ....domain.models.user import User

router = APIRouter()


@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    keyword: str = Query("", description="搜索关键词"),
    is_active: bool | None = Query(None, description="状态筛选"),
    db: AsyncSession = Depends(get_db),
):
    """用户列表（分页/搜索/筛选）"""
    query = select(User)
    count_query = select(func.count(User.id))

    if keyword:
        filter_cond = or_(
            User.nickname.contains(keyword),
            User.wechat_openid.contains(keyword),
        )
        query = query.where(filter_cond)
        count_query = count_query.where(filter_cond)

    if is_active is not None:
        query = query.where(User.is_active == is_active)
        count_query = count_query.where(User.is_active == is_active)

    # 总数
    total = (await db.execute(count_query)).scalar() or 0

    # 分页
    query = query.order_by(User.created_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    users = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "size": size,
        "items": [
            {
                "id": str(u.id),
                "nickname": u.nickname,
                "avatar_url": u.avatar_url,
                "wechat_openid": u.wechat_openid,
                "target_lang": u.target_lang,
                "native_lang": u.native_lang,
                "level": u.level,
                "is_active": u.is_active,
                "is_admin": u.is_admin,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
    }


@router.get("/users/{user_id}")
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    """用户详情"""
    from uuid import UUID
    user = await db.get(User, UUID(user_id))
    if not user:
        raise HTTPException(404, "用户不存在")
    return {
        "id": str(user.id),
        "nickname": user.nickname,
        "avatar_url": user.avatar_url,
        "wechat_openid": user.wechat_openid,
        "target_lang": user.target_lang,
        "native_lang": user.native_lang,
        "level": user.level,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.put("/users/{user_id}/status")
async def toggle_user_status(
    user_id: str,
    is_active: bool = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """启用/禁用用户"""
    from uuid import UUID
    user = await db.get(User, UUID(user_id))
    if not user:
        raise HTTPException(404, "用户不存在")
    user.is_active = is_active
    await db.commit()
    return {"ok": True, "is_active": user.is_active}
