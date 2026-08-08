"""后台管理端点：会员与排盘（仅管理员，服务端强制 require_admin + 审计）。"""

import json

from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy import func

from api.deps import AdminUser, DbDep
from models.bazi_chart import BaziChart
from models.user import User
from services.audit_service import log_audit

router = APIRouter()


def _mask_phone(phone: str) -> str:
    return f"{phone[:3]}****{phone[-4:]}"


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("/members")
def list_members(
    admin: AdminUser,
    db: DbDep,
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    phone: str | None = Query(default=None),
):
    """会员列表：分页 + 手机号精确搜索 + 总数统计；手机号脱敏。"""
    q = db.query(User)
    if phone:
        q = q.filter(User.phone == phone)
    total = q.count()
    users = q.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    items = []
    for u in users:
        chart_count = db.query(func.count(BaziChart.id)).filter(BaziChart.user_id == u.id).scalar()
        items.append(
            {
                "id": u.id,
                "phone_masked": _mask_phone(u.phone),
                "created_at": u.created_at.isoformat(),
                "chart_count": chart_count,
            }
        )
    log_audit(db, admin.id, "member.list", ip=_client_ip(request))
    return {"total": total, "items": items}


@router.get("/members/{member_id}")
def member_detail(member_id: int, admin: AdminUser, db: DbDep, request: Request):
    u = db.get(User, member_id)
    if u is None:
        raise HTTPException(status_code=404, detail="会员不存在")
    chart_count = db.query(func.count(BaziChart.id)).filter(BaziChart.user_id == u.id).scalar()
    log_audit(db, admin.id, "member.detail", "member", u.id, _client_ip(request))
    return {
        "id": u.id,
        "phone": u.phone,
        "name": u.name,
        "created_at": u.created_at.isoformat(),
        "chart_count": chart_count,
    }


@router.get("/members/{member_id}/charts")
def member_charts(
    member_id: int,
    admin: AdminUser,
    db: DbDep,
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """会员的排盘记录列表（摘要，不含完整 chart_result）。"""
    if db.get(User, member_id) is None:
        raise HTTPException(status_code=404, detail="会员不存在")
    records = (
        db.query(BaziChart)
        .filter(BaziChart.user_id == member_id)
        .order_by(BaziChart.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = []
    for r in records:
        result = json.loads(r.chart_result)
        items.append(
            {
                "id": r.id,
                "person_name": r.person_name,
                "relationship": r.relationship_type,
                "created_at": r.created_at.isoformat(),
                "summary": {
                    "year": result.get("pillars", {}).get("year"),
                    "month": result.get("pillars", {}).get("month"),
                    "day": result.get("pillars", {}).get("day"),
                    "time": result.get("pillars", {}).get("time"),
                },
            }
        )
    log_audit(db, admin.id, "member.charts", "member", member_id, _client_ip(request))
    return {"items": items}


@router.get("/charts/{chart_id}")
def chart_detail(chart_id: int, admin: AdminUser, db: DbDep, request: Request):
    """排盘记录完整详情（仅详情返回 chart_result）。"""
    r = db.get(BaziChart, chart_id)
    if r is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    log_audit(db, admin.id, "chart.detail", "bazi_chart", r.id, _client_ip(request))
    return {
        "id": r.id,
        "person_name": r.person_name,
        "relationship": r.relationship_type,
        "created_at": r.created_at.isoformat(),
        "chart_result": json.loads(r.chart_result),
    }
