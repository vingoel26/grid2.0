"""Model C — License plate localizer (morsetechlab/yolov11-lp)."""
from __future__ import annotations

from .base import YoloDetectorBase


class PlateDetector(YoloDetectorBase):
    source = "plate"

    def _map_class(self, cls_id: int) -> str:
        return "license_plate"
