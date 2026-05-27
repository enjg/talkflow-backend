"""角色管理 API"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from app.dependencies import get_db
from app.domain.models.user_character import UserCharacter
from app.api.v1.admin.deps import require_admin

router = APIRouter()


# ===== Schemas =====
class CharacterCreateRequest(BaseModel):
    """创建角色请求"""
    user_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=100)
    avatar: str = Field(default="🎭", max_length=10)
    description: str = Field(default="", max_length=500)
    language: str = Field(default="zh", max_length=10)
    system_prompt: str = Field(default="", max_length=5000)
    voice_id_zh: str = Field(default="白桦", max_length=50)
    voice_id_en: str = Field(default="Guy", max_length=50)
    tts_style_zh: str = Field(default="", max_length=500)
    tts_style_en: str = Field(default="", max_length=500)


class CharacterUpdateRequest(BaseModel):
    """更新角色请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    avatar: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    system_prompt: Optional[str] = None
    voice_id_zh: Optional[str] = None
    voice_id_en: Optional[str] = None
    tts_style_zh: Optional[str] = None
    tts_style_en: Optional[str] = None


def _char_dict(c: UserCharacter) -> dict:
    """序列化角色"""
    return {
        "id": str(c.id),
        "user_id": str(c.user_id),
        "name": c.name,
        "avatar": c.avatar,
        "description": c.description,
        "language": c.language,
        "system_prompt": c.system_prompt,
        "voice_id_zh": c.voice_id_zh,
        "voice_id_en": c.voice_id_en,
        "tts_style_zh": c.tts_style_zh,
        "tts_style_en": c.tts_style_en,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


# ===== Endpoints =====
@router.get("")
async def list_characters(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: Optional[uuid.UUID] = None,
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """角色列表"""
    query = select(UserCharacter)
    count_query = select(func.count()).select_from(UserCharacter)

    if user_id:
        query = query.where(UserCharacter.user_id == user_id)
        count_query = count_query.where(UserCharacter.user_id == user_id)
    if keyword:
        like = f"%{keyword}%"
        query = query.where(UserCharacter.name.ilike(like))
        count_query = count_query.where(UserCharacter.name.ilike(like))

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(UserCharacter.created_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    chars = result.scalars().all()

    return {
        "code": 0,
        "data": {
            "items": [_char_dict(c) for c in chars],
            "total": total,
            "page": page,
            "size": size,
        },
    }


@router.post("")
async def create_character(
    req: CharacterCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """创建角色"""
    char = UserCharacter(
        user_id=req.user_id,
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
    return {"code": 0, "message": "创建成功", "data": _char_dict(char)}


@router.put("/{character_id}")
async def update_character(
    character_id: uuid.UUID,
    req: CharacterUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """更新角色"""
    result = await db.execute(
        select(UserCharacter).where(UserCharacter.id == character_id)
    )
    char = result.scalar_one_or_none()
    if not char:
        return {"code": 404, "message": "角色不存在"}

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(char, field, value)

    await db.commit()
    await db.refresh(char)
    return {"code": 0, "message": "更新成功", "data": _char_dict(char)}


@router.delete("/{character_id}")
async def delete_character(
    character_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """删除角色"""
    result = await db.execute(
        select(UserCharacter).where(UserCharacter.id == character_id)
    )
    char = result.scalar_one_or_none()
    if not char:
        return {"code": 404, "message": "角色不存在"}

    await db.delete(char)
    await db.commit()
    return {"code": 0, "message": "角色已删除"}
