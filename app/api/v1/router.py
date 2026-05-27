"""v1 路由汇总"""
from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.sessions import router as sessions_router
from app.api.v1.user import router as user_router
from app.api.v1.health import router as health_router
from app.api.v1.characters import router as characters_router
from app.api.v1.tokens import router as tokens_router

# 管理端API
from app.api.v1.admin.users import router as admin_users_router
from app.api.v1.admin.characters import router as admin_chars_router
from app.api.v1.admin.conversations import router as admin_convos_router
from app.api.v1.admin.stats import router as admin_stats_router
from app.api.v1.admin.monitor import router as admin_monitor_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["健康检查"])
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(chat_router, prefix="/chat", tags=["对话"])
api_router.include_router(sessions_router, prefix="/sessions", tags=["会话"])
api_router.include_router(user_router, prefix="/users", tags=["用户"])
api_router.include_router(characters_router, tags=["角色"])
api_router.include_router(tokens_router, tags=["Token统计"])

# 管理端路由
api_router.include_router(admin_users_router, prefix="/admin", tags=["管理-用户"])
api_router.include_router(admin_chars_router, prefix="/admin", tags=["管理-角色"])
api_router.include_router(admin_convos_router, prefix="/admin", tags=["管理-对话"])
api_router.include_router(admin_stats_router, prefix="/admin", tags=["管理-统计"])
api_router.include_router(admin_monitor_router, prefix="/admin", tags=["管理-监控"])
