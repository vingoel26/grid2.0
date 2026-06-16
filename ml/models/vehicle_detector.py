"""Model A — UVH-26 YOLO11 vehicle detector (IISc, 14 Indian classes)."""
from __future__ import annotations

from ..types import UVH26_CLASSES
from .base import YoloDetectorBase


class VehicleDetector(YoloDetectorBase):
    source = "vehicle"

    def _map_class(self, cls_id: int) -> str:
        return UVH26_CLASSES.get(cls_id, "Others")
