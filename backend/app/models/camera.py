"""Camera ORM model — geometry + flow direction for violation analyzers."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    location_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    rtsp_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expected_flow_direction: Mapped[float] = mapped_column(Float, default=0.0)
    stop_line_polygon: Mapped[list | None] = mapped_column(JSON, nullable=True)
    intersection_polygon: Mapped[list | None] = mapped_column(JSON, nullable=True)
    no_parking_zones: Mapped[list | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 default=lambda: datetime.utcnow())
