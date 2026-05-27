"""用户 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.domain.schemas.user import UserUpdateRequest
from app.middleware.auth_middleware import get_current_user
from app.services.user_service import user_service

router = APIRouter()


@router.get("/me")
async def get_me(current_user=Depends(get_current_user)):
    """获取当前用户信息"""
    return {"code": 0, "data": {
        "id": str(current_user.id), "nickname": current_user.nickname,
        "avatar_url": current_user.avatar_url, "target_lang": current_user.target_lang,
        "native_lang": current_user.native_lang, "level": current_user.level,
        "created_at": current_user.created_at.isoformat(),
    }}


@router.patch("/me")
async def update_me(
    req: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """更新用户信息"""
    update_data = req.model_dump(exclude_unset=True)
    user = await user_service.update_profile(db, current_user.id, **update_data)
    return {"code": 0, "data": {"id": str(user.id), "nickname": user.nickname}}


@router.get("/me/stats")
async def get_stats(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取学习统计"""
    stats = await user_service.get_stats(db, current_user.id, days)
    return {"code": 0, "data": stats}
