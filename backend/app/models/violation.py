"""Violation ORM model (TimescaleDB hypertable on occurred_at)."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class Violation(Base):
    __tablename__ = "violations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True,
                                    default=lambda: str(uuid.uuid4()))
    violation_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    violation_type: Mapped[str] = mapped_column(String(30), index=True)
    violation_code: Mapped[str] = mapped_column(String(10))
    fine_inr: Mapped[int] = mapped_column(Integer)

    camera_id: Mapped[str] = mapped_column(String(50), index=True)
    camera_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    raw_confidence: Mapped[float] = mapped_column(Float)
    final_confidence: Mapped[float] = mapped_column(Float)
    enforcement_action: Mapped[str] = mapped_column(String(20), index=True)

    vehicle_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    plate_number: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    plate_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    vehicle_bbox: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    evidence_image_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    evidence_thumbnail_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    evidence_video_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    evidence_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    location_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="PENDING", index=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    gemini_verdict: Mapped[str | None] = mapped_column(String(20), nullable=True)
    gemini_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    pipeline_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)

    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 default=lambda: datetime.utcnow())
