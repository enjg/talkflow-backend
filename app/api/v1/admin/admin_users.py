"""用户管理 API"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from app.dependencies import get_db
from app.domain.models.user import User
from app.api.v1.admin.deps import require_admin

router = APIRouter()


# ===== Schemas =====
class UserUpdateRequest(BaseModel):
    """管理员更新用户请求"""
    nickname: Optional[str] = Field(None, min_length=1, max_length=50)
    avatar_url: Optional[str] = None
    target_lang: Optional[str] = None
    native_lang: Optional[str] = None
    level: Optional[str] = None
    is_admin: Optional[bool] = None


class UserStatusRequest(BaseModel):
    """用户状态切换请求"""
    is_active: bool


def _user_dict(u: User) -> dict:
    """序列化用户"""
    return {
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
        "updated_at": u.updated_at.isoformat() if u.updated_at else None,
    }


# ===== Endpoints =====
@router.get("")
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_admin: Optional[bool] = None,
    level: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """用户列表（分页/搜索/筛选）"""
    query = select(User)
    count_query = select(func.count()).select_from(User)

    # 搜索
    if keyword:
        like = f"%{keyword}%"
        filter_cond = or_(User.nickname.ilike(like), User.wechat_openid.ilike(like))
        query = query.where(filter_cond)
        count_query = count_query.where(filter_cond)

    # 筛选
    if is_active is not None:
        query = query.where(User.is_active == is_active)
        count_query = count_query.where(User.is_active == is_active)
    if is_admin is not None:
        query = query.where(User.is_admin == is_admin)
        count_query = count_query.where(User.is_admin == is_admin)
    if level:
        query = query.where(User.level == level)
        count_query = count_query.where(User.level == level)

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(User.created_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    users = result.scalars().all()

    return {
        "code": 0,
        "data": {
            "items": [_user_dict(u) for u in users],
            "total": total,
            "page": page,
            "size": size,
        },
    }


@router.get("/{user_id}")
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """用户详情"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return {"code": 404, "message": "用户不存在"}
    return {"code": 0, "data": _user_dict(user)}


@router.put("/{user_id}")
async def update_user(
    user_id: uuid.UUID,
    req: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """更新用户信息"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return {"code": 404, "message": "用户不存在"}

    update_data = req.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return {"code": 0, "message": "更新成功", "data": _user_dict(user)}


@router.put("/{user_id}/status")
async def toggle_user_status(
    user_id: uuid.UUID,
    req: UserStatusRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """启用/禁用用户"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return {"code": 404, "message": "用户不存在"}

    user.is_active = req.is_active
    await db.commit()
    status = "启用" if req.is_active else "禁用"
    return {"code": 0, "message": f"用户已{status}"}


@router.delete("/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """删除用户"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return {"code": 404, "message": "用户不存在"}

    await db.delete(user)
    await db.commit()
    return {"code": 0, "message": "用户已删除"}
