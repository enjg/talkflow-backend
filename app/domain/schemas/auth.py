"""认证相关 Schema"""
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    """注册请求"""
    nickname: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    wechat_openid: str | None = None


class LoginRequest(BaseModel):
    """登录请求"""
    nickname: str
    password: str


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 86400


class RefreshRequest(BaseModel):
    """刷新 Token 请求"""
    refresh_token: str
