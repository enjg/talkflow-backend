"""
应用事件模块 - 启动和关闭时的初始化/清理操作。
"""
import structlog
from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from fastapi import FastAPI

from app.config import settings

logger = structlog.get_logger()

# 全局引擎和会话工厂
_engine = None
_session_factory = None
_redis: Optional["aioredis.Redis"] = None


def get_engine():
    """获取或创建数据库引擎（单例）。"""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_pre_ping=True,
            echo=settings.DEBUG,
        )
    return _engine


def get_session_factory():
    """获取或创建会话工厂（单例）。"""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话上下文管理器。"""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


def get_redis():
    """获取 Redis 客户端实例。"""
    global _redis
    return _redis


async def startup(app: FastAPI):
    """应用启动时执行的初始化操作。"""
    global _redis

    # 配置结构化日志
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer() if not settings.DEBUG else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            structlog.get_config()["wrapper_class"].level if structlog.get_config().get("wrapper_class") else 20
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # 初始化数据库引擎
    get_engine()
    logger.info("数据库引擎初始化完成", url=settings.DATABASE_URL.split("@")[-1])

    # 初始化 Redis
    try:
        import aioredis
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        await _redis.ping()
        logger.info("Redis 连接建立", url=settings.REDIS_URL.split("@")[-1] if "@" in settings.REDIS_URL else settings.REDIS_URL)
    except Exception as e:
        logger.warning("Redis 连接失败，频率限制将不可用", error=str(e))
        _redis = None

    # 初始化 HTTP 客户端（供 AI 服务使用）
    import httpx
    app.state.http_client = httpx.AsyncClient(
        limits=httpx.Limits(
            max_connections=settings.HTTP_POOL_SIZE,
            max_keepalive_connections=settings.HTTP_POOL_SIZE // 2,
        ),
        timeout=httpx.Timeout(60.0, connect=10.0),
    )
    logger.info("HTTP 客户端初始化完成")


async def shutdown(app: FastAPI):
    """应用关闭时执行的清理操作。"""
    global _engine, _redis

    # 关闭 HTTP 客户端
    if hasattr(app.state, "http_client"):
        await app.state.http_client.aclose()
        logger.info("HTTP 客户端关闭")

    # 关闭 Redis
    if _redis:
        await _redis.close()
        _redis = None
        logger.info("Redis 连接关闭")

    # 关闭数据库引擎
    if _engine:
        await _engine.dispose()
        _engine = None
        logger.info("数据库引擎关闭")
