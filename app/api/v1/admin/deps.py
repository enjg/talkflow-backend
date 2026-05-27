"""管理端权限验证"""
from fastapi import HTTPException, Depends
from app.middleware.auth_middleware import get_current_user


async def require_admin(current_user=Depends(get_current_user)):
    """验证当前用户是否为管理员"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user
