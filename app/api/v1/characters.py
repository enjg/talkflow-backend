"""角色 API — 内置角色 + 用户自定义角色"""
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from app.dependencies import get_db
from app.middleware.auth_middleware import get_current_user
from app.services.ai.characters import get_character_list, get_character, get_character_prompt, get_character_voice, get_character_tts_style
from app.domain.models.user_character import UserCharacter

router = APIRouter()


# ===== Schemas =====
class CustomCharacterCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    avatar: str = Field(default="🎭", max_length=10)
    description: str = Field(default="", max_length=500)
    language: str = Field(default="zh", max_length=10)
    system_prompt: str = Field(default="", max_length=5000)
    voice_id_zh: str = Field(default="白桦", max_length=50)
    voice_id_en: str = Field(default="Guy", max_length=50)
    tts_style_zh: str = Field(default="", max_length=500)
    tts_style_en: str = Field(default="", max_length=500)


class CustomCharacterUpdate(BaseModel):
    name: str | None = None
    avatar: str | None = None
    description: str | None = None
    language: str | None = None
    system_prompt: str | None = None
    voice_id_zh: str | None = None
    voice_id_en: str | None = None
    tts_style_zh: str | None = None
    tts_style_en: str | None = None


# ===== 内置角色 =====
@router.get("/characters")
async def list_characters(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取所有角色（内置 + 用户自定义）"""
    # 内置角色
    builtin = get_character_list()
    for c in builtin:
        c["type"] = "builtin"

    # 用户自定义角色
    result = await db.execute(
        select(UserCharacter).where(UserCharacter.user_id == current_user.id)
    )
    custom_chars = result.scalars().all()
    custom = [
        {
            "id": f"custom_{c.id}",
            "name": c.name,
            "description": c.description,
            "avatar": c.avatar,
            "language": c.language,
            "type": "custom",
        }
        for c in custom_chars
    ]

    return {"code": 0, "data": builtin + custom}


@router.get("/characters/{character_id}")
async def get_character_detail(
    character_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取角色详情（内置或自定义）"""
    # 自定义角色
    if character_id.startswith("custom_"):
        real_id = character_id.replace("custom_", "")
        try:
            uid = uuid.UUID(real_id)
        except ValueError:
            return {"code": 404, "message": "角色不存在"}

        result = await db.execute(
            select(UserCharacter).where(
                UserCharacter.id == uid,
                UserCharacter.user_id == current_user.id,
            )
        )
        c = result.scalar_one_or_none()
        if not c:
            return {"code": 404, "message": "角色不存在"}

        return {
            "code": 0,
            "data": {
                "id": f"custom_{c.id}",
                "name": c.name,
                "description": c.description,
                "avatar": c.avatar,
                "language": c.language,
                "type": "custom",
                "voice_id": {"zh": c.voice_id_zh, "en": c.voice_id_en},
                "tts_style": {"zh": c.tts_style_zh, "en": c.tts_style_en},
                "system_prompt": c.system_prompt,
            },
        }

    # 内置角色
    char = get_character(character_id)
    if not char:
        return {"code": 404, "message": "角色不存在"}

    return {
        "code": 0,
        "data": {
            "id": character_id,
            "name": char["name"],
            "description": char["description"],
            "avatar": char["avatar"],
            "language": char["language"],
            "type": "builtin",
            "voice_id": char["voice_id"],
            "tts_style": char["tts_style"],
        },
    }


# ===== 自定义角色 CRUD =====
@router.post("/characters/custom")
async def create_custom_character(
    req: CustomCharacterCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """创建自定义角色"""
    char = UserCharacter(
        user_id=current_user.id,
        name=req.name,
        avatar=req.avatar,
        description=req.description,
        language=req.language,
        system_prompt=req.system_prompt,
        voice_id_zh=req.voice_id_zh,
        voice_id_en=req.voice_id_en,
        tts_style_zh=req.tts_style_zh,
        tts_style_en=req.tts_style_en,
    )
    db.add(char)
    await db.commit()
    await db.refresh(char)

    return {
        "code": 0,
        "data": {
            "id": f"custom_{char.id}",
            "name": char.name,
            "avatar": char.avatar,
            "description": char.description,
            "language": char.language,
            "type": "custom",
        },
    }


@router.put("/characters/custom/{character_id}")
async def update_custom_character(
    character_id: str,
    req: CustomCharacterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """更新自定义角色"""
    try:
        uid = uuid.UUID(character_id)
    except ValueError:
        return {"code": 404, "message": "角色不存在"}

    result = await db.execute(
        select(UserCharacter).where(
            UserCharacter.id == uid,
            UserCharacter.user_id == current_user.id,
        )
    )
    char = result.scalar_one_or_none()
    if not char:
        return {"code": 404, "message": "角色不存在"}

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(char, field, value)

    await db.commit()
    return {"code": 0, "message": "更新成功"}


@router.delete("/characters/custom/{character_id}")
async def delete_custom_character(
    character_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """删除自定义角色"""
    try:
        uid = uuid.UUID(character_id)
    except ValueError:
        return {"code": 404, "message": "角色不存在"}

    result = await db.execute(
        select(UserCharacter).where(
            UserCharacter.id == uid,
            UserCharacter.user_id == current_user.id,
        )
    )
    char = result.scalar_one_or_none()
    if not char:
        return {"code": 404, "message": "角色不存在"}

    await db.delete(char)
    await db.commit()
    return {"code": 0, "message": "删除成功"}


# ===== 辅助接口 =====
@router.get("/characters/voices/list")
async def list_voices():
    """获取可用音色列表"""
    return {
        "code": 0,
        "data": {
            "zh": ["白桦", "云希", "云扬", "晓晓", "晓依"],
            "en": ["Guy", "Andrew", "Emma"],
        },
    }
