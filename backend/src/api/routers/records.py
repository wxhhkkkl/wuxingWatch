"""Saved BaZi records: create / list / detail / delete (owner-only).

**记录与引擎口径的绑定**（2026-09-16）：`chart_result` 里另存两个**下划线键**——
`_engine_version`（引擎核心模块源码哈希）与 `_input`（当时的完整入参）。读取时若版本
不符就**重算**并回写，保证界面上不会出现「保存那一刻的旧段序/旧口径」。两个下划线键
不下发给前端（`_strip`）。
"""

import json

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from api.deps import CurrentUser, DbDep
from api.schemas import RecordCreate
from models.bazi_chart import BaziChart
from services import chart_service
from services.bazi.v2 import engine_version

router = APIRouter()


def _dump(payload: RecordCreate, result: dict) -> str:
    """入库：引擎结果 + **口径版本** + **完整入参**（下划线键，不下发）。"""
    return json.dumps(
        {**result, "_engine_version": engine_version(),
         "_input": payload.model_dump(mode="json")},
        ensure_ascii=False)


def _raw(record: BaziChart) -> dict:
    return json.loads(record.chart_result)


def _strip(stored: dict) -> dict:
    """剥掉存储专用的下划线键。"""
    return {k: v for k, v in stored.items() if not k.startswith("_")}


def _load_result(record: BaziChart, db: Session) -> tuple[dict, dict]:
    """取 (结果, 当时的入参)。**引擎口径变了就重算并回写。**

    - 版本一致 → 直接用存的（省一次计算）。
    - 版本不符且存了 `_input` → 重算、回写、返回新的。
    - 没有 `_input`（早于本次改动的老记录）或重算失败 → 退回存的那份。

    返回的入参优先取 `_input`（完整保真）；老记录退回 `_birth_input_of` 的重建。
    """
    stored = _raw(record)
    payload = stored.get("_input")
    if stored.get("_engine_version") == engine_version():
        return _strip(stored), payload or {}
    if not payload:
        return _strip(stored), {}
    try:
        fresh, _ = chart_service.compute(RecordCreate(**payload))
    except Exception:                       # 旧参数已不被接受：退回存的那份
        return _strip(stored), {}
    record.chart_result = _dump(RecordCreate(**payload), fresh)
    db.commit()
    return fresh, payload


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
        chart_result=_dump(payload, result),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {
        "id": record.id,
        "person_name": record.person_name,
        "relationship": record.relationship_type,
        "created_at": record.created_at.isoformat(),
        "chart_result": _strip(_raw(record)),
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
            "summary": _summarize(_raw(r)),
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
    result, payload = _load_result(record, db)
    return {
        "id": record.id,
        "person_name": record.person_name,
        "relationship": record.relationship_type,
        "notes": record.notes,
        "created_at": record.created_at.isoformat(),
        "chart_result": result,
        "birth_input": payload or _birth_input_of(record, result),
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
    record.chart_result = _dump(payload, result)
    db.commit()
    return {
        "id": record.id,
        "person_name": record.person_name,
        "relationship": record.relationship_type,
        "notes": record.notes,
        "created_at": record.created_at.isoformat(),
        "chart_result": result,
        "birth_input": payload.model_dump(mode="json"),
    }


@router.delete("/{record_id}", status_code=204)
def delete_record(record_id: int, user: CurrentUser, db: DbDep):
    record = _get_owned(db, record_id, user.id)
    db.delete(record)
    db.commit()
    return None
