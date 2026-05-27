"""管理端 - 角色管理"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from ....dependencies import get_db
from ....domain.models.user_character import UserCharacter
from ....services.ai.characters import CHARACTERS

router = APIRouter()

# 角色数据目前是硬编码在 characters.py 中，管理端提供查看和自定义覆盖


@router.get("/characters")
async def list_characters():
    """获取所有AI角色"""
    return {
        "items": [
            {
                "id": c["id"],
                "name": c["name"],
                "avatar": c.get("avatar", ""),
                "description": c.get("description", ""),
                "language": c.get("language", "en"),
                "personality": c.get("personality", ""),
                "level": c.get("level", "intermediate"),
            }
            for c in CHARACTERS
        ],
        "total": len(CHARACTERS),
    }


@router.get("/characters/usage")
async def character_usage(db: AsyncSession = Depends(get_db)):
    """角色使用统计"""
    result = await db.execute(
        select(
            UserCharacter.character_id,
            func.count(UserCharacter.id).label("usage_count"),
        ).group_by(UserCharacter.character_id)
    )
    usage_map = {row[0]: row[1] for row in result.all()}

    return {
        "items": [
            {
                "id": c["id"],
                "name": c["name"],
                "usage_count": usage_map.get(c["id"], 0),
            }
            for c in CHARACTERS
        ]
    }
