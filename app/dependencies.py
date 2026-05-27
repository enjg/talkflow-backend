"""依赖注入"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from .config import settings

if "sqlite" in settings.DATABASE_URL:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
else:
    engine = create_async_engine(
        settings.DATABASE_URL, echo=False, pool_size=10, max_overflow=20,
    )

async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    """获取数据库会话"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
