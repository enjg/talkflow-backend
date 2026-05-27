"""健康检查 API"""
from fastapi import APIRouter
from sqlalchemy import text
from app.dependencies import async_session_factory

router = APIRouter()


@router.get("/health")
async def health_check():
    """健康检查"""
    services = {"database": "unknown", "api": "ok"}
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        services["database"] = "connected"
    except Exception as e:
        services["database"] = f"error: {e}"
    return {"code": 0, "data": {"status": "healthy", "version": "1.0.0", "services": services}}
