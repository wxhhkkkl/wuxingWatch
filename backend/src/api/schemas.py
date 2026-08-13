"""Pydantic request/response models."""

from datetime import date
from datetime import date as date_t
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
    precise_shichen: bool = Field(
        default=False,
        description="精确时辰（日出日落定位法）：按当日日出/正午/日落/子夜划分 24 段确定时辰",
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


class LiuShiLevel(StrEnum):
    MONTH = "month"
    DAY = "day"
    HOUR = "hour"


class LiuShiContext(BaseModel):
    day_ganzhi: str = Field(min_length=2, max_length=2)
    year_ganzhi: str = Field(min_length=2, max_length=2)
    month_zhi: str = Field(min_length=1, max_length=1)


class LiuShiRequest(BaseModel):
    """流月/流日/流时下钻查询；context 为本命盘干支上下文。"""

    level: LiuShiLevel
    year: int = Field(ge=1900, le=2100)
    month_branch: str | None = Field(default=None, description="level=day/hour 必填：节气月支（寅…丑）")
    date: date_t | None = Field(default=None, description="level=hour 必填：公历日期")
    context: LiuShiContext

    @model_validator(mode="after")
    def _validate_level_params(self):
        if self.level in (LiuShiLevel.DAY, LiuShiLevel.HOUR) and not self.month_branch:
            raise ValueError("level=day/hour 需提供 month_branch")
        if self.level == LiuShiLevel.HOUR and self.date is None:
            raise ValueError("level=hour 需提供 date")
        return self


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


# ============ 阅读模块（006-reading-module）============


class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    sort_order: int = 0


class CategoryOut(BaseModel):
    id: int
    name: str
    sort_order: int


class BookIn(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    author: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    cover_url: str | None = Field(default=None, max_length=500)
    category_id: int | None = Field(default=None, description="创建时必填")


class ChapterIn(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str | None = None


class ChapterReorderIn(BaseModel):
    chapter_ids: list[int]


class ProgressUpdateIn(BaseModel):
    chapter_id: int
