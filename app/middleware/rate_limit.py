"""Redis 滑动窗口频率限制"""
import time
import logging
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """基于 Redis 的滑动窗口频率限制
    
    默认限制每分钟 60 次请求。
    """

    def __init__(self, app, redis_client=None, limit: int = 60, window: int = 60):
        super().__init__(app)
        self.redis = redis_client
        self.limit = limit
        self.window = window

    async def dispatch(self, request: Request, call_next):
        """检查请求频率"""
        if not self.redis:
            return await call_next(request)

        # 获取客户端标识
        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:{client_ip}"

        try:
            now = time.time()
            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(key, 0, now - self.window)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, self.window)
            results = await pipe.execute()

            request_count = results[1]
            if request_count >= self.limit:
                raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")

        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"限流检查失败，放行请求: {e}")

        response = await call_next(request)
        return response
