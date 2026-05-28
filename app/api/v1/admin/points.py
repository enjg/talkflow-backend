"""管理端 - 积分管理"""
import uuid as _uuid
import random
import string
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from ....dependencies import get_db
from ....domain.models.points import PointsRule, Package, ActivationCode, PointsLog
from ..deps import require_admin

router = APIRouter()


# ─── 积分规则 ───

@router.get("/points/rules")
async def list_rules(db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    result = await db.execute(select(PointsRule).order_by(PointsRule.created_at.desc()))
    return [_rule_to_dict(r) for r in result.scalars().all()]


@router.post("/points/rules")
async def create_rule(data: dict, db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    rule = PointsRule(
        name=data["name"], type=data["type"], gain_or_consume=data["gain_or_consume"],
        points=data["points"], daily_limit=data.get("daily_limit", 0), enabled=data.get("enabled", True),
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return {"id": str(rule.id), "ok": True}


@router.put("/points/rules/{rule_id}")
async def update_rule(rule_id: str, data: dict, db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    rule = await db.get(PointsRule, _uuid.UUID(rule_id))
    if not rule:
        raise HTTPException(404, "规则不存在")
    for k in ["name", "type", "gain_or_consume", "points", "daily_limit", "enabled"]:
        if k in data:
            setattr(rule, k, data[k])
    await db.commit()
    return {"ok": True}


@router.delete("/points/rules/{rule_id}")
async def delete_rule(rule_id: str, db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    rule = await db.get(PointsRule, _uuid.UUID(rule_id))
    if not rule:
        raise HTTPException(404, "规则不存在")
    await db.delete(rule)
    await db.commit()
    return {"ok": True}


# ─── 积分套餐 ───

@router.get("/points/packages")
async def list_packages(db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    result = await db.execute(select(Package).order_by(Package.created_at.desc()))
    return [_pkg_to_dict(p) for p in result.scalars().all()]


@router.post("/points/packages")
async def create_package(data: dict, db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    pkg = Package(
        name=data["name"], description=data.get("description"),
        points=data["points"], price=data["price"],
        duration_days=data.get("duration_days", 0), status=data.get("status", 1),
    )
    db.add(pkg)
    await db.commit()
    await db.refresh(pkg)
    return {"id": str(pkg.id), "ok": True}


@router.put("/points/packages/{pkg_id}")
async def update_package(pkg_id: str, data: dict, db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    pkg = await db.get(Package, _uuid.UUID(pkg_id))
    if not pkg:
        raise HTTPException(404, "套餐不存在")
    for k in ["name", "description", "points", "price", "duration_days", "status"]:
        if k in data:
            setattr(pkg, k, data[k])
    await db.commit()
    return {"ok": True}


@router.delete("/points/packages/{pkg_id}")
async def delete_package(pkg_id: str, db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    pkg = await db.get(Package, _uuid.UUID(pkg_id))
    if not pkg:
        raise HTTPException(404, "套餐不存在")
    await db.delete(pkg)
    await db.commit()
    return {"ok": True}


# ─── 激活码 ───

@router.get("/points/activation-codes")
async def list_codes(
    package_id: str = Query("", description="按套餐筛选"),
    status: int | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
):
    query = select(ActivationCode)
    count_query = select(func.count(ActivationCode.id))
    if package_id:
        query = query.where(ActivationCode.package_id == package_id)
        count_query = count_query.where(ActivationCode.package_id == package_id)
    if status is not None:
        query = query.where(ActivationCode.status == status)
        count_query = count_query.where(ActivationCode.status == status)
    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(query.order_by(ActivationCode.created_at.desc()).offset((page - 1) * size).limit(size))
    return {
        "total": total, "page": page, "size": size,
        "items": [_code_to_dict(c) for c in result.scalars().all()],
    }


@router.post("/points/activation-codes/generate")
async def generate_codes(data: dict, db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    """批量生成激活码"""
    package_id = data["package_id"]
    count = data.get("count", 1)
    expires_days = data.get("expires_days", 0)
    codes = []
    for _ in range(min(count, 500)):
        code_str = "".join(random.choices(string.ascii_uppercase + string.digits, k=16))
        code = ActivationCode(
            code=code_str,
            package_id=package_id,
            status=0,
            expires_at=datetime.now(timezone.utc) + timedelta(days=expires_days) if expires_days > 0 else None,
        )
        db.add(code)
        codes.append(code_str)
    await db.commit()
    return {"generated": len(codes), "codes": codes}


@router.delete("/points/activation-codes/{code_id}")
async def delete_code(code_id: str, db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    code = await db.get(ActivationCode, _uuid.UUID(code_id))
    if not code:
        raise HTTPException(404, "激活码不存在")
    await db.delete(code)
    await db.commit()
    return {"ok": True}


# ─── 积分流水 ───

@router.get("/points/logs")
async def list_logs(
    member_id: str = Query("", description="会员ID"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
):
    query = select(PointsLog)
    count_query = select(func.count(PointsLog.id))
    if member_id:
        query = query.where(PointsLog.member_id == member_id)
        count_query = count_query.where(PointsLog.member_id == member_id)
    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(query.order_by(PointsLog.created_at.desc()).offset((page - 1) * size).limit(size))
    return {
        "total": total, "page": page, "size": size,
        "items": [
            {
                "id": str(l.id), "member_id": l.member_id, "type": l.type,
                "points": l.points, "balance": l.balance, "description": l.description,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in result.scalars().all()
        ],
    }


# ─── helpers ───

def _rule_to_dict(r):
    return {
        "id": str(r.id), "name": r.name, "type": r.type, "gain_or_consume": r.gain_or_consume,
        "points": r.points, "daily_limit": r.daily_limit, "enabled": r.enabled,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _pkg_to_dict(p):
    return {
        "id": str(p.id), "name": p.name, "description": p.description,
        "points": p.points, "price": p.price, "duration_days": p.duration_days,
        "status": p.status, "created_at": p.created_at.isoformat() if p.created_at else None,
    }


def _code_to_dict(c):
    return {
        "id": str(c.id), "code": c.code, "package_id": c.package_id,
        "status": c.status, "used_by": c.used_by,
        "used_at": c.used_at.isoformat() if c.used_at else None,
        "expires_at": c.expires_at.isoformat() if c.expires_at else None,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }
