"""V7 — Illegal parking (A + Tracker + Config). Stationary timer in zone."""
from __future__ import annotations

import math

from ..types import Track
from .geometry import make_violation, point_in_polygon


def check_illegal_parking(track: Track, camera_cfg, cfg: dict, fps: float = 30.0,
                          timestamp: float = 0.0):
    zones = camera_cfg.no_parking_zones or []
    if not zones:
        return
    in_zone = any(point_in_polygon(track.center, z) for z in zones)
    if not in_zone:
        return

    stationary_s = cfg.get("stationary_seconds", 30)
    max_disp = cfg.get("max_displacement_px", 5.0)
    window = int(stationary_s * fps)
    if len(track.trajectory) < window:
        return

    recent = track.trajectory[-window:]
    origin = recent[0]
    max_displacement = max(math.dist(origin, p) for p in recent)
    if max_displacement < max_disp:
        yield make_violation("ILLEGAL_PARKING", track, camera_cfg.id,
                             confidence=0.92, timestamp=timestamp,
                             stationary_seconds=stationary_s)
