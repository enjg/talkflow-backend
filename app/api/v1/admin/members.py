"""管理端 - 会员管理"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from ....dependencies import get_db
from ....domain.models.member import Member
from ..deps import require_admin

router = APIRouter()


@router.get("/members")
async def list_members(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    keyword: str = Query("", description="搜索关键词(手机号/邮箱)"),
    status: int | None = Query(None, description="状态筛选"),
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
):
    """会员列表"""
    query = select(Member)
    count_query = select(func.count(Member.id))

    if keyword:
        filter_cond = or_(Member.phone.contains(keyword), Member.email.contains(keyword))
        query = query.where(filter_cond)
        count_query = count_query.where(filter_cond)
    if status is not None:
        query = query.where(Member.status == status)
        count_query = count_query.where(Member.status == status)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(query.order_by(Member.created_at.desc()).offset((page - 1) * size).limit(size))
    members = result.scalars().all()
    return {
        "total": total,
        "page": page,
        "size": size,
        "items": [
            {
                "id": str(m.id),
                "user_id": m.user_id,
                "phone": m.phone,
                "email": m.email,
                "points_balance": m.points_balance,
                "level": m.level,
                "status": m.status,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in members
        ],
    }


@router.get("/members/{member_id}")
async def get_member(member_id: str, db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    """会员详情"""
    from uuid import UUID
    member = await db.get(Member, UUID(member_id))
    if not member:
        raise HTTPException(404, "会员不存在")
    return {
        "id": str(member.id),
        "user_id": member.user_id,
        "phone": member.phone,
        "email": member.email,
        "points_balance": member.points_balance,
        "level": member.level,
        "status": member.status,
        "created_at": member.created_at.isoformat() if member.created_at else None,
    }


@router.put("/members/{member_id}/freeze")
async def freeze_member(member_id: str, db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    """冻结会员"""
    from uuid import UUID
    member = await db.get(Member, UUID(member_id))
    if not member:
        raise HTTPException(404, "会员不存在")
    member.status = 0
    await db.commit()
    return {"ok": True, "status": 0}


@router.put("/members/{member_id}/unfreeze")
async def unfreeze_member(member_id: str, db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    """解冻会员"""
    from uuid import UUID
    member = await db.get(Member, UUID(member_id))
    if not member:
        raise HTTPException(404, "会员不存在")
    member.status = 1
    await db.commit()
    return {"ok": True, "status": 1}
