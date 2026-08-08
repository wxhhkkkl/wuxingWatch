"""Pydantic request/response models."""

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field


class Gender(StrEnum):
    M = "M"
    F = "F"
    UNKNOWN = "UNKNOWN"


class Calendar(StrEnum):
    SOLAR = "solar"
    LUNAR = "lunar"


class Relationship(StrEnum):
    SELF = "SELF"
    CHILD = "CHILD"
    PARENT = "PARENT"
    OTHER = "OTHER"


class BirthInput(BaseModel):
    name: str | None = None
    gender: Gender = Gender.UNKNOWN
    calendar: Calendar = Calendar.SOLAR
    birth_date: date
    birth_time: str | None = Field(
        default=None, description="HH:MM，或时辰名（如 子/午时）；缺省表示时辰不详"
    )
    birth_month_is_leap: bool = False  # 仅 calendar=lunar 时有意义
    birth_place: str | None = None
    longitude: float | None = None
    latitude: float | None = None


class RecordCreate(BirthInput):
    person_name: str | None = None
    relationship: Relationship = Relationship.SELF
    notes: str | None = None


class SendCodeRequest(BaseModel):
    phone: str


class VerifyRequest(BaseModel):
    phone: str
    code: str


class UserOut(BaseModel):
    id: int
    phone: str
    name: str | None = None


class RecordSummary(BaseModel):
    id: int
    person_name: str | None
    relationship: str
    birth_solar: str
    created_at: str
    summary: dict
