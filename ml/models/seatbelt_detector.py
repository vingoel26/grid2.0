"""Model D — Seatbelt detector (RISEF/yolov11s-seatbelt)."""
from __future__ import annotations

from .base import YoloDetectorBase

# RISEF model class order: 0 -> seatbelt, 1 -> no_seatbelt (verify on real weights)
SEATBELT_NAMES = {0: "seatbelt", 1: "no_seatbelt"}


class SeatbeltDetector(YoloDetectorBase):
    source = "seatbelt"

    def _map_class(self, cls_id: int) -> str:
        return SEATBELT_NAMES.get(cls_id, str(cls_id))
