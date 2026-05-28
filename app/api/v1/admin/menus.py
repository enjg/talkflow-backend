"""管理端 - 菜单管理"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ....dependencies import get_db
from ....domain.models.menu import Menu
from ..deps import require_admin

router = APIRouter()


@router.get("/menus")
async def list_menus(db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    """获取菜单树"""
    result = await db.execute(select(Menu).order_by(Menu.sort))
    menus = result.scalars().all()
    return [
        {
            "id": str(m.id),
            "parentId": m.parent_id,
            "name": m.name,
            "path": m.path,
            "component": m.component,
            "icon": m.icon,
            "sort": m.sort,
            "visible": m.visible,
            "type": m.type,
            "permission": m.permission,
        }
        for m in menus
    ]


@router.post("/menus")
async def create_menu(data: dict, db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    """创建菜单"""
    menu = Menu(
        parent_id=data.get("parentId"),
        name=data["name"],
        path=data.get("path"),
        component=data.get("component"),
        icon=data.get("icon"),
        sort=data.get("sort", 0),
        visible=data.get("visible", True),
        type=data.get("type", "menu"),
        permission=data.get("permission"),
    )
    db.add(menu)
    await db.commit()
    await db.refresh(menu)
    return {"id": str(menu.id), "ok": True}


@router.put("/menus/{menu_id}")
async def update_menu(menu_id: str, data: dict, db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    """更新菜单"""
    from uuid import UUID
    menu = await db.get(Menu, UUID(menu_id))
    if not menu:
        raise HTTPException(404, "菜单不存在")
    for field in ["parent_id", "name", "path", "component", "icon", "sort", "visible", "type", "permission"]:
        key = field
        # 支持驼峰
        camel = "".join(w.capitalize() if i else w for i, w in enumerate(field.split("_")))
        if camel in data:
            key = camel
        elif field in data:
            key = field
        else:
            continue
        setattr(menu, field, data[key])
    # 特殊处理 parentId
    if "parentId" in data:
        menu.parent_id = data["parentId"]
    await db.commit()
    return {"ok": True}


@router.delete("/menus/{menu_id}")
async def delete_menu(menu_id: str, db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    """删除菜单"""
    from uuid import UUID
    menu = await db.get(Menu, UUID(menu_id))
    if not menu:
        raise HTTPException(404, "菜单不存在")
    await db.delete(menu)
    await db.commit()
    return {"ok": True}
