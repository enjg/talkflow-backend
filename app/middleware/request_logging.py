"""请求日志中间件"""
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("talkflow.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """结构化请求日志
    
    记录每个请求的方法、路径、状态码、耗时。
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"

        response = await call_next(request)
        duration = time.time() - start_time
        status = response.status_code

        # 只记录 API 请求，忽略静态文件
        if path.startswith("/api"):
            logger.info(
                f"{method} {path} → {status} ({duration:.3f}s) [{client_ip}]"
            )

        # 添加响应头
        response.headers["X-Process-Time"] = f"{duration:.3f}"
        return response
