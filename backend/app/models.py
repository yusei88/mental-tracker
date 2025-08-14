from pydantic import BaseModel, field_serializer, field_validator, Field, StrictInt, StrictFloat
from datetime import date
from typing import Optional


class Entry(BaseModel):
    id: Optional[str] = Field(
        default=None,
        description="エントリーID（自動生成、任意）",
        json_schema_extra={"example": "dummy_id"}
    )
    record_date: date = Field(
        description="記録日（必須、YYYY-MM-DD形式）",
        json_schema_extra={"example": "2025-08-14"}
    )
    mood_score: StrictInt = Field(
        description="メンタルスコア（必須、0〜5の整数）",
        ge=0,
        le=5,
        json_schema_extra={"example": 4}
    )
    sleep_hours: StrictFloat = Field(
        description="睡眠時間（必須、0以上の小数）",
        ge=0,
        json_schema_extra={"example": 6.5}
    )
    memo: Optional[str] = Field(
        default=None,
        description="メモ（任意、空文字可）",
        json_schema_extra={"example": "今日はよく眠れた"}
    )

    model_config = {
        "extra": "forbid"
    }

    @field_serializer('record_date')
    def serialize_record_date(self, v:date) -> str:
        return v.isoformat()

    @field_validator('mood_score')
    def validate_mood_score(cls, v):
        """
        メンタルスコアは0〜5の整数のみ許容。
        """
        if v is None:
            raise ValueError('mood_scoreは必須です')
        if not (0 <= v <= 5):
            raise ValueError('mood_scoreは0〜5の整数である必要があります')
        return v

    @field_validator('sleep_hours')
    def validate_sleep_hours(cls, v):
        """
        睡眠時間は0以上のみ許容。
        """
        if v is None:
            raise ValueError('sleep_hoursは必須です')
        if v < 0:
            raise ValueError('sleep_hoursは0以上である必要があります')
        return v


class EntryResponse(BaseModel):
    status: str
    entry: Entry
