"""Pydantic request/response models."""

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class Gender(StrEnum):
    M = "M"
    F = "F"
    UNKNOWN = "UNKNOWN"


class Calendar(StrEnum):
    SOLAR = "solar"
    LUNAR = "lunar"
    SIZHU = "sizhu"


class Relationship(StrEnum):
    SELF = "SELF"
    CHILD = "CHILD"
    PARENT = "PARENT"
    OTHER = "OTHER"


class BirthInput(BaseModel):
    name: str | None = None
    gender: Gender = Gender.UNKNOWN
    calendar: Calendar = Calendar.SOLAR
    birth_date: date | None = Field(default=None, description="公历/农历模式必填；四柱模式不需要")
    birth_time: str | None = Field(
        default=None, description="HH:MM，或时辰名（如 子/午时）；缺省表示时辰不详"
    )
    birth_month_is_leap: bool = False  # 仅 calendar=lunar 时有意义
    birth_place: str | None = None
    longitude: float | None = None
    latitude: float | None = None
    timezone: str | None = Field(default=None, description="出生地 IANA 时区，如 Asia/Shanghai")
    birth_pillars: dict[str, str] | None = Field(
        default=None,
        description="仅 calendar=sizhu：四柱干支，键 year/month/day/time，如 {'year':'庚午',...}",
    )

    @model_validator(mode="after")
    def _validate_birth_date(self):
        if self.calendar != Calendar.SIZHU and self.birth_date is None:
            raise ValueError("出生日期为必填（公历/农历模式）")
        if self.calendar == Calendar.SIZHU and self.birth_pillars is None:
            raise ValueError("四柱模式需提供 birth_pillars")
        return self


class RecordCreate(BirthInput):
    person_name: str | None = None
    relationship: Relationship = Relationship.SELF
    notes: str | None = None


class AuthIntent(StrEnum):
    LOGIN = "login"
    REGISTER = "register"
    RESET = "reset"


class SendCodeRequest(BaseModel):
    phone: str
    intent: AuthIntent = AuthIntent.LOGIN


class VerifyRequest(BaseModel):
    phone: str
    code: str


class RegisterIn(BaseModel):
    phone: str
    code: str
    password: str


class PasswordLoginIn(BaseModel):
    phone: str
    password: str


class ResetPasswordIn(BaseModel):
    phone: str
    code: str
    password: str


class UserOut(BaseModel):
    id: int
    phone: str
    name: str | None = None
    role: str = "member"


class RecordSummary(BaseModel):
    id: int
    person_name: str | None
    relationship: str
    birth_solar: str
    created_at: str
    summary: dict
