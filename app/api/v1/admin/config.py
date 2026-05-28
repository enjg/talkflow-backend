"""管理端 - 系统配置"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ....dependencies import get_db
from ....domain.models.admin_settings import AdminSetting
from ..deps import require_admin

router = APIRouter()

# 配置key常量
CONFIG_KEYS = {
    "ai_characters": "AI角色列表(JSON)",
    "ai_models": "可用模型列表(JSON)",
    "points_consume": "积分消耗配置(JSON)",
    "system_notice": "系统公告",
    "default_points_per_chat": "每次对话消耗积分",
    "welcome_bonus_points": "新用户赠送积分",
}


@router.get("/config")
async def list_config(db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    """获取所有配置"""
    result = await db.execute(select(AdminSetting))
    settings = result.scalars().all()
    settings_map = {s.key: s.value for s in settings}
    return {
        key: {
            "key": key,
            "label": label,
            "value": settings_map.get(key, ""),
        }
        for key, label in CONFIG_KEYS.items()
    }


@router.get("/config/{key}")
async def get_config(key: str, db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    """获取单个配置"""
    result = await db.execute(select(AdminSetting).where(AdminSetting.key == key))
    setting = result.scalar_one_or_none()
    if not setting:
        return {"key": key, "label": CONFIG_KEYS.get(key, key), "value": ""}
    return {"key": setting.key, "label": CONFIG_KEYS.get(key, key), "value": setting.value}


@router.put("/config/{key}")
async def update_config(key: str, data: dict, db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    """更新配置"""
    value = data.get("value", "")
    result = await db.execute(select(AdminSetting).where(AdminSetting.key == key))
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    else:
        db.add(AdminSetting(key=key, value=value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)))
    await db.commit()
    return {"ok": True, "key": key}
