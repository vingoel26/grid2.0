"""V8 — No number plate (A + C). Plate absent for N consecutive frames."""
from __future__ import annotations

from ..types import Detection, Track, compute_iou
from .geometry import make_violation


def check_no_plate(track: Track, plates: list[Detection], cfg: dict,
                   camera_id: str, timestamp: float = 0.0):
    plate_iou = cfg.get("plate_iou", 0.10)
    missing_frames = cfg.get("missing_frames", 15)
    skip = set(cfg.get("skip_classes", ["Bicycle", "Three-wheeler"]))

    has_plate = any(compute_iou(track.bbox, p.bbox) > plate_iou for p in plates)
    if has_plate:
        track.no_plate_frames = 0
        return

    track.no_plate_frames += 1
    if track.no_plate_frames >= missing_frames and track.cls_name not in skip:
        yield make_violation("NO_PLATE", track, camera_id, confidence=0.80,
                             timestamp=timestamp,
                             consistent_frames=track.no_plate_frames)
