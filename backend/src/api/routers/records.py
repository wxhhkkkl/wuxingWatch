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
    result = json.loads(record.chart_result)
    return {
        "id": record.id,
        "person_name": record.person_name,
        "relationship": record.relationship_type,
        "notes": record.notes,
        "created_at": record.created_at.isoformat(),
        "chart_result": result,
        "birth_input": _birth_input_of(record, result),
    }


def _birth_input_of(record: BaziChart, result: dict) -> dict:
    """从已存列重建 BirthInput（供前端"修改内容"回填表单）。

    农历输入已换算为等价阳历，统一回填 solar；timezone 未落库不返回。
    """
    base = {
        "name": record.name,
        "gender": record.gender or "UNKNOWN",
        "birth_place": record.birth_place,
        "longitude": record.longitude,
        "latitude": record.latitude,
    }
    if record.birth_solar is None:  # 四柱模式
        pillars = {
            k: (result.get("pillars", {}).get(k) or {}).get("ganzhi")
            for k in ("year", "month", "day", "time")
        }
        return {**base, "calendar": "sizhu", "birth_pillars": pillars}
    unknown_time = "hour_pillar" in (result.get("missing_parts") or [])
    return {
        **base,
        "calendar": "solar",
        "birth_date": record.birth_solar.date().isoformat(),
        "birth_time": None if unknown_time else record.birth_solar.strftime("%H:%M"),
        "precise_shichen": bool((result.get("shichen") or {}).get("applied")),
    }


@router.put("/{record_id}")
def update_record(record_id: int, payload: RecordCreate, user: CurrentUser, db: DbDep):
    record = _get_owned(db, record_id, user.id)
    result, solar_birth = chart_service.compute(payload)
    record.person_name = payload.person_name
    record.relationship_type = payload.relationship.value
    record.name = payload.name
    record.gender = payload.gender.value
    record.birth_solar = solar_birth
    record.birth_input_is_lunar = payload.calendar == "lunar"
    record.birth_lunar = result.get("lunar_birth")
    record.birth_place = payload.birth_place
    record.longitude = payload.longitude
    record.latitude = payload.latitude
    record.notes = payload.notes
    record.chart_result = json.dumps(result, ensure_ascii=False)
    db.commit()
    return {
        "id": record.id,
        "person_name": record.person_name,
        "relationship": record.relationship_type,
        "notes": record.notes,
        "created_at": record.created_at.isoformat(),
        "chart_result": result,
        "birth_input": _birth_input_of(record, result),
    }


@router.delete("/{record_id}", status_code=204)
def delete_record(record_id: int, user: CurrentUser, db: DbDep):
    record = _get_owned(db, record_id, user.id)
    db.delete(record)
    db.commit()
    return None
