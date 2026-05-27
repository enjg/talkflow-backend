"""用户相关 Schema"""
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


class UserResponse(BaseModel):
    """用户信息响应"""
    id: UUID
    nickname: str
    avatar_url: str | None = None
    target_lang: str = "en"
    native_lang: str = "zh"
    level: str = "intermediate"
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    """用户更新请求"""
    nickname: str | None = Field(None, min_length=2, max_length=50)
    avatar_url: str | None = None
    target_lang: str | None = None
    native_lang: str | None = None
    level: str | None = None


class UserStatsResponse(BaseModel):
    """用户统计响应"""
    total_duration: int = 0
    total_messages: int = 0
    streak_days: int = 0
    daily: list[dict] = []
