"""Saved BaZi records: create / list / detail / delete (owner-only)."""

import json

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from api.deps import CurrentUser, DbDep
from api.schemas import RecordCreate
from models.bazi_chart import BaziChart
from services import chart_service

router = APIRouter()


@router.post("", status_code=201)
def save_record(payload: RecordCreate, user: CurrentUser, db: DbDep):
    result, solar_birth = chart_service.compute(payload)
    record = BaziChart(
        user_id=user.id,
        person_name=payload.person_name,
        relationship_type=payload.relationship.value,
        name=payload.name,
        gender=payload.gender.value,
        birth_solar=solar_birth,
        birth_input_is_lunar=payload.calendar == "lunar",
        birth_lunar=result.get("lunar_birth"),
        birth_place=payload.birth_place,
        longitude=payload.longitude,
        latitude=payload.latitude,
        notes=payload.notes,
        chart_result=json.dumps(result, ensure_ascii=False),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {
        "id": record.id,
        "person_name": record.person_name,
        "relationship": record.relationship_type,
        "created_at": record.created_at.isoformat(),
        "chart_result": json.loads(record.chart_result),
    }


@router.get("")
def list_records(user: CurrentUser, db: DbDep):
    records = (
        db.query(BaziChart)
        .filter(BaziChart.user_id == user.id)
        .order_by(BaziChart.created_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "person_name": r.person_name,
            "relationship": r.relationship_type,
            "birth_solar": r.birth_solar.isoformat() if r.birth_solar else "",
            "created_at": r.created_at.isoformat(),
            "summary": _summarize(json.loads(r.chart_result)),
        }
        for r in records
    ]


def _summarize(result: dict) -> dict:
    pillars = result.get("pillars", {})
    return {
        "year": pillars.get("year"),
        "month": pillars.get("month"),
        "day": pillars.get("day"),
        "time": pillars.get("time"),
    }


def _get_owned(db: Session, record_id: int, user_id: int) -> BaziChart:
    record = db.get(BaziChart, record_id)
    if record is None or record.user_id != user_id:
        raise HTTPException(status_code=404, detail="记录不存在")
    return record


@router.get("/{record_id}")
def get_record(record_id: int, user: CurrentUser, db: DbDep):
    record = _get_owned(db, record_id, user.id)
    return {
        "id": record.id,
        "person_name": record.person_name,
        "relationship": record.relationship_type,
        "notes": record.notes,
        "created_at": record.created_at.isoformat(),
        "chart_result": json.loads(record.chart_result),
    }


@router.delete("/{record_id}", status_code=204)
def delete_record(record_id: int, user: CurrentUser, db: DbDep):
    record = _get_owned(db, record_id, user.id)
    db.delete(record)
    db.commit()
    return None
