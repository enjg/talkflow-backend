"""认证 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.domain.schemas.auth import RegisterRequest, LoginRequest, RefreshRequest
from app.services.auth_service import auth_service

router = APIRouter()


@router.post("/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """用户注册"""
    try:
        result = await auth_service.register(db, req.nickname, req.password, req.wechat_openid)
        return {"code": 0, "message": "注册成功", "data": {
            "user_id": str(result["user_id"]),
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": "bearer",
        }}
    except ValueError as e:
        return {"code": 400, "message": str(e), "data": None}


@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    try:
        result = await auth_service.login(db, req.nickname, req.password)
        return {"code": 0, "message": "登录成功", "data": {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": "bearer",
            "expires_in": 86400,
        }}
    except ValueError as e:
        return {"code": 400, "message": str(e), "data": None}


@router.post("/refresh")
async def refresh(req: RefreshRequest):
    """刷新 Token"""
    try:
        result = auth_service.refresh(req.refresh_token)
        return {"code": 0, "message": "刷新成功", "data": result}
    except ValueError as e:
        return {"code": 400, "message": str(e), "data": None}
