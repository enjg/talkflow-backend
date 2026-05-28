"""管理端 - 角色管理"""
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from ....dependencies import get_db
from ....domain.models.role import Role
from ..deps import require_admin

router = APIRouter()


@router.get("/roles")
async def list_roles(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
):
    """角色列表"""
    total = (await db.execute(select(func.count(Role.id)))).scalar() or 0
    result = await db.execute(select(Role).order_by(Role.created_at.desc()).offset((page - 1) * size).limit(size))
    roles = result.scalars().all()
    return {
        "total": total,
        "page": page,
        "size": size,
        "items": [
            {
                "id": str(r.id),
                "name": r.name,
                "code": r.code,
                "status": r.status,
                "description": r.description,
                "menu_ids": json.loads(r.menu_ids) if r.menu_ids else [],
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in roles
        ],
    }


@router.post("/roles")
async def create_role(data: dict, db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    """创建角色"""
    role = Role(
        name=data["name"],
        code=data["code"],
        status=data.get("status", 1),
        description=data.get("description"),
        menu_ids=json.dumps(data.get("menu_ids", [])),
    )
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return {"id": str(role.id), "ok": True}


@router.put("/roles/{role_id}")
async def update_role(role_id: str, data: dict, db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    """更新角色"""
    from uuid import UUID
    role = await db.get(Role, UUID(role_id))
    if not role:
        raise HTTPException(404, "角色不存在")
    if "name" in data:
        role.name = data["name"]
    if "code" in data:
        role.code = data["code"]
    if "status" in data:
        role.status = data["status"]
    if "description" in data:
        role.description = data["description"]
    if "menu_ids" in data:
        role.menu_ids = json.dumps(data["menu_ids"])
    await db.commit()
    return {"ok": True}


@router.delete("/roles/{role_id}")
async def delete_role(role_id: str, db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    """删除角色"""
    from uuid import UUID
    role = await db.get(Role, UUID(role_id))
    if not role:
        raise HTTPException(404, "角色不存在")
    await db.delete(role)
    await db.commit()
    return {"ok": True}
