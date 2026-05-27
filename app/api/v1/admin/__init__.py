"""管理端API模块"""
from fastapi import APIRouter
from app.api.v1.admin.admin_users import router as users_router
from app.api.v1.admin.admin_characters import router as characters_router
from app.api.v1.admin.admin_conversations import router as conversations_router
from app.api.v1.admin.admin_logs import router as logs_router
from app.api.v1.admin.stats import router as stats_router
from app.api.v1.admin.monitor import router as monitor_router

admin_router = APIRouter()
admin_router.include_router(users_router, prefix="/users", tags=["管理-用户"])
admin_router.include_router(characters_router, prefix="/characters", tags=["管理-角色"])
admin_router.include_router(conversations_router, prefix="/conversations", tags=["管理-对话"])
admin_router.include_router(logs_router, prefix="/logs", tags=["管理-日志"])
admin_router.include_router(stats_router, prefix="/stats", tags=["管理-统计"])
admin_router.include_router(monitor_router, prefix="/monitor", tags=["管理-监控"])
