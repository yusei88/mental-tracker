from pydantic import BaseModel, field_serializer, field_validator, Field, StrictInt, StrictFloat
from datetime import date
from typing import Optional, List


class Entry(BaseModel):
    id: Optional[str] = Field(
        default=None,
        validation_alias="_id",
        description="エントリーID（自動生成、任意）",
        json_schema_extra={"example": "dummy_id"}
    )
    entry_id: Optional[int] = Field(
        default=None,
        description="エントリーID（シーケンシャル、自動生成）",
        json_schema_extra={"example": 1}
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
        "extra": "forbid",
        "populate_by_name": True
    }

    @field_serializer('record_date')
    def serialize_record_date(self, v: date) -> str:
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

    # MongoDBドキュメント形式(dict)で返す
    def to_mongo_dict(self):
        d = self.model_dump(by_alias=True)
        # 念のためrecord_dateをISO文字列化
        if isinstance(d["record_date"], date):
            d["record_date"] = d["record_date"].isoformat()
        return d

    @staticmethod
    def get_next_entry_id(entries_collection):
        """
        次のentry_idを取得する。
        現在登録されているentryの「entry_id」の最大値に+1した値を返す。
        1つも登録されていない場合は1を返す。
        """
        # entry_idの最大値を取得
        pipeline = [
            {"$group": {"_id": None, "max_entry_id": {"$max": "$entry_id"}}}
        ]
        result = list(entries_collection.aggregate(pipeline))
        
        if result and result[0]["max_entry_id"] is not None:
            return result[0]["max_entry_id"] + 1
        else:
            return 1


class EntryResponse(BaseModel):
    status: str
    entry: Entry


class EntriesResponse(BaseModel):
    status: str
    entries: List[Entry]
