from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class ViolationCreate(BaseModel):
    """Payload from the ML service (POST /api/v1/violations)."""

    violation_id: str
    violation_type: str
    violation_code: str = ""
    fine_inr: int = 0
    camera_id: str
    raw_confidence: float
    final_confidence: float
    enforcement_action: str
    vehicle_type: Optional[str] = None
    plate_number: Optional[str] = None
    plate_confidence: Optional[float] = None
    vehicle_bbox: Optional[Any] = None
    evidence_image_path: Optional[str] = None
    evidence_thumbnail_path: Optional[str] = None
    evidence_video_path: Optional[str] = None
    evidence_hash: Optional[str] = None
    model_version: Optional[str] = None
    pipeline_latency_ms: Optional[float] = None
    occurred_at: float | datetime

    @field_validator("occurred_at")
    @classmethod
    def _coerce_ts(cls, v):
        if isinstance(v, (int, float)):
            return datetime.utcfromtimestamp(v)
        return v


class ViolationReview(BaseModel):
    status: str = Field(..., pattern="^(CONFIRMED|REJECTED)$")
    review_notes: Optional[str] = None


class ViolationOut(BaseModel):
    id: str
    violation_id: str
    violation_type: str
    violation_code: str
    fine_inr: int
    camera_id: str
    camera_name: Optional[str]
    raw_confidence: float
    final_confidence: float
    enforcement_action: str
    vehicle_type: Optional[str]
    plate_number: Optional[str]
    plate_confidence: Optional[float]
    vehicle_bbox: Optional[Any]
    evidence_image_path: Optional[str]
    evidence_thumbnail_path: Optional[str]
    evidence_video_path: Optional[str]
    evidence_hash: Optional[str]
    location_lat: Optional[float]
    location_lng: Optional[float]
    location_name: Optional[str]
    status: str
    reviewed_by: Optional[str]
    review_notes: Optional[str]
    reviewed_at: Optional[datetime]
    gemini_verdict: Optional[str]
    gemini_explanation: Optional[str]
    model_version: Optional[str]
    pipeline_latency_ms: Optional[float]
    occurred_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class ViolationList(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ViolationOut]
