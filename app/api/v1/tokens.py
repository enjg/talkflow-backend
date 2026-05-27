"""Token 用量统计 API"""
from fastapi import APIRouter
from app.services.ai.token_tracker import get_today_summary, get_all_stats, get_today_stats

router = APIRouter(prefix="/tokens", tags=["Token统计"])


@router.get("/today")
async def today_tokens():
    """获取今日各角色 token 用量汇总"""
    return {
        "summary": get_today_summary(),
        "detail": get_today_stats(),
    }


@router.get("/all")
async def all_tokens():
    """获取全部 token 统计数据"""
    return get_all_stats()
