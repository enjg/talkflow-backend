"""会话相关 Schema"""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from .common import PaginatedResponse


class SessionCreateRequest(BaseModel):
    """创建会话请求"""
    title: str = Field(default="新对话", max_length=200)
    character_id: str | None = None
    topic: str | None = None
    reply_lang: str = "auto"


class SessionResponse(BaseModel):
    """会话响应"""
    id: UUID
    title: str
    character_id: str | None = None
    topic: str | None = None
    reply_lang: str = "auto"
    message_count: int = 0
    last_message: str | None = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class SessionListResponse(PaginatedResponse[SessionResponse]):
    """会话列表响应"""
    pass
