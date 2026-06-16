"""Model B — COCO YOLO11n. Provides person (0) and traffic_light (9)."""
from __future__ import annotations

from .base import YoloDetectorBase

COCO_NAMES = {0: "person", 1: "bicycle", 2: "car", 3: "motorcycle", 9: "traffic_light"}


class PersonDetector(YoloDetectorBase):
    source = "person"

    def _allowed_classes(self):
        return [0, 9]  # person + traffic_light

    def _map_class(self, cls_id: int) -> str:
        return COCO_NAMES.get(cls_id, str(cls_id))
