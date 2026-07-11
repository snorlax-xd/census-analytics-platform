from pydantic import BaseModel


class MeasureValue(BaseModel):
    measure_code: str
    measure_name: str
    category: str
    unit: str
    value: float
    higher_is_better: bool | None
    rank: int | None = None


class LocaleAnalytics(BaseModel):
    locale_code: str
    locale_name: str
    year: int
    measures: list[MeasureValue]


class AnalyticsResponse(BaseModel):
    data: list[LocaleAnalytics]


class ClosestPresetResponse(BaseModel):
    state_code: str
    state_name: str
    value: float


class NeighborPresetResponse(BaseModel):
    state_code: str | None
    state_name: str | None = None

