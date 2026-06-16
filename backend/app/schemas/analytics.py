from __future__ import annotations

from pydantic import BaseModel


class SummaryOut(BaseModel):
    total_today: int
    total_all_time: int
    auto_enforced: int
    pending_review: int
    avg_latency_ms: float
    by_type: dict[str, int]
    by_action: dict[str, int]
    pct_change_vs_yesterday: float


class HourlyPoint(BaseModel):
    hour: str
    count: int


class HeatmapPoint(BaseModel):
    lat: float
    lng: float
    count: int
    camera_id: str
    camera_name: str | None = None
