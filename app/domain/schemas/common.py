"""通用响应模型"""
from typing import Any, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应格式"""
    code: int = 0
    message: str = "success"
    data: T | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""
    items: list[T]
    total: int
    page: int
    size: int


class ErrorResponse(BaseModel):
    """错误响应"""
    code: int
    message: str
    data: None = None


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    services: dict
