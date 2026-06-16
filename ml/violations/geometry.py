"""Geometry helpers shared by violation analyzers."""
from __future__ import annotations

import numpy as np

from ..types import BBox, VIOLATION_META, Violation


def point_in_polygon(point: tuple[float, float], polygon: list) -> bool:
    """Ray-casting point-in-polygon. Empty polygon -> False."""
    if not polygon or len(polygon) < 3:
        return False
    x, y = point
    inside = False
    n = len(polygon)
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi):
            inside = not inside
        j = i
    return inside


def point_crossed_line(point: tuple[float, float], line_polygon: list) -> bool:
    """Treat a thin polygon as a stop-line band; True if point is inside it."""
    return point_in_polygon(point, line_polygon)


def crop(frame: np.ndarray, bbox: BBox):
    """Safe integer crop, clipped to frame bounds. Returns None if degenerate."""
    if frame is None:
        return None
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = bbox
    x1, y1 = max(0, int(x1)), max(0, int(y1))
    x2, y2 = min(w, int(x2)), min(h, int(y2))
    if x2 <= x1 or y2 <= y1:
        return None
    return frame[y1:y2, x1:x2]


def make_violation(vtype: str, track, camera_id: str, confidence: float,
                   timestamp: float = 0.0, **extra) -> Violation:
    """Construct a Violation pre-filled with section/fine metadata."""
    code, fine = VIOLATION_META.get(vtype, ("", 0))
    return Violation(
        type=vtype,
        confidence=float(confidence),
        raw_confidence=float(confidence),
        vehicle_track_id=track.id,
        camera_id=camera_id,
        vehicle_bbox=track.bbox,
        vehicle_type=track.cls_name,
        timestamp=timestamp,
        violation_code=code,
        fine_inr=fine,
        extra=extra,
    )
