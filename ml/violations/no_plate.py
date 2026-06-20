"""V8 — No number plate (A + C). Plate absent for N consecutive frames.

Fixed Issues (June 20, 2026):
1. IoU matching fails for motorcycles (tiny plate vs large vehicle bbox).
   → Now uses containment ratio (plate center inside vehicle bbox) instead
     of pure IoU.
2. 15 frames (0.5s) was too aggressive → raised to 45 frames (~1.5s).
3. Hardcoded 0.80 confidence → now scales with how many frames plate is
   missing (more frames = higher confidence).
4. Added Two-wheeler to skip list — rear plates are rarely visible from
   CCTV angle in Indian traffic.
"""
from __future__ import annotations

from ..types import Detection, Track, compute_iou
from .geometry import make_violation


def _plate_overlaps_vehicle(vehicle_bbox, plate_bbox, iou_thresh: float) -> bool:
    """Check if a plate belongs to a vehicle using BOTH IoU and containment.

    Pure IoU fails when the plate is tiny relative to the vehicle (motorcycles).
    So we also check if the plate center falls inside the vehicle bbox.
    """
    # Method 1: Standard IoU (works for cars)
    if compute_iou(vehicle_bbox, plate_bbox) > iou_thresh:
        return True

    # Method 2: Plate center inside vehicle bbox (works for motorcycles)
    px = (plate_bbox[0] + plate_bbox[2]) / 2
    py = (plate_bbox[1] + plate_bbox[3]) / 2
    vx1, vy1, vx2, vy2 = vehicle_bbox
    # Allow some margin (20% expansion) since plate may be slightly outside bbox
    margin_x = (vx2 - vx1) * 0.20
    margin_y = (vy2 - vy1) * 0.20
    if (vx1 - margin_x) <= px <= (vx2 + margin_x) and (vy1 - margin_y) <= py <= (vy2 + margin_y):
        return True

    return False


def check_no_plate(track: Track, plates: list[Detection], cfg: dict,
                   camera_id: str, timestamp: float = 0.0):
    plate_iou = cfg.get("plate_iou", 0.10)
    missing_frames = cfg.get("missing_frames", 45)  # was 15 → now 45 (~1.5s at 30fps)
    skip = set(cfg.get("skip_classes", ["Bicycle", "Three-wheeler", "Two-wheeler"]))

    has_plate = any(
        _plate_overlaps_vehicle(track.bbox, p.bbox, plate_iou)
        for p in plates
    )
    if has_plate:
        track.no_plate_frames = 0
        return

    track.no_plate_frames += 1
    if track.no_plate_frames >= missing_frames and track.cls_name not in skip:
        # Scale confidence by how long plate has been missing
        # 45 frames → 0.65 (LOG_ONLY), 90+ frames → 0.80 (HUMAN_REVIEW)
        conf = min(0.50 + 0.005 * track.no_plate_frames, 0.85)
        yield make_violation("NO_PLATE", track, camera_id, confidence=conf,
                             timestamp=timestamp,
                             consistent_frames=track.no_plate_frames)
