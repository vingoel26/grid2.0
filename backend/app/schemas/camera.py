from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class CameraBase(BaseModel):
    name: str
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    rtsp_url: Optional[str] = None
    expected_flow_direction: float = 0.0
    stop_line_polygon: Optional[Any] = None
    intersection_polygon: Optional[Any] = None
    no_parking_zones: Optional[Any] = None
    is_active: bool = True


class CameraCreate(CameraBase):
    id: str


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    rtsp_url: Optional[str] = None
    expected_flow_direction: Optional[float] = None
    stop_line_polygon: Optional[Any] = None
    intersection_polygon: Optional[Any] = None
    no_parking_zones: Optional[Any] = None
    is_active: Optional[bool] = None


class CameraOut(CameraBase):
    id: str
    created_at: datetime
    model_config = {"from_attributes": True}
