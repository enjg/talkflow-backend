"""
自定义异常模块 - 统一的业务异常体系。
"""
from typing import Any, Optional


class AppException(Exception):
    """应用基础异常。"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        detail: Optional[Any] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)


class NotFoundException(AppException):
    """资源不存在异常。"""

    def __init__(self, resource: str = "资源", resource_id: str = ""):
        detail = f"{resource} '{resource_id}' 不存在" if resource_id else f"{resource}不存在"
        super().__init__(message=detail, status_code=404)


class UnauthorizedException(AppException):
    """未授权异常。"""

    def __init__(self, message: str = "未授权访问"):
        super().__init__(message=message, status_code=401)


class ForbiddenException(AppException):
    """禁止访问异常。"""

    def __init__(self, message: str = "无权执行此操作"):
        super().__init__(message=message, status_code=403)


class ValidationException(AppException):
    """数据验证异常。"""

    def __init__(self, message: str = "数据验证失败", detail: Optional[Any] = None):
        super().__init__(message=message, status_code=422, detail=detail)


class RateLimitException(AppException):
    """频率限制异常。"""

    def __init__(self, message: str = "请求过于频繁，请稍后再试"):
        super().__init__(message=message, status_code=429)


class AIException(AppException):
    """AI 服务异常。"""

    def __init__(self, message: str = "AI 服务暂时不可用", detail: Optional[Any] = None):
        super().__init__(message=message, status_code=503, detail=detail)
