"""V5 & V6 — Stop-line and red-light violations (A + B + Config)."""
from __future__ import annotations

from ..types import Track
from .geometry import make_violation, point_crossed_line, point_in_polygon


def check_intersection(track: Track, traffic_light_state: str, camera_cfg,
                       cfg_stop: dict, cfg_red: dict, timestamp: float = 0.0):
    """Only triggers while the light is RED. Emits STOP_LINE and/or RED_LIGHT."""
    if traffic_light_state != "RED":
        return

    center = track.center

    if camera_cfg.stop_line_polygon and point_crossed_line(center, camera_cfg.stop_line_polygon):
        yield make_violation("STOP_LINE_VIOLATION", track, camera_cfg.id,
                             confidence=0.85, timestamp=timestamp)

    if camera_cfg.intersection_polygon and point_in_polygon(center, camera_cfg.intersection_polygon):
        yield make_violation("RED_LIGHT_VIOLATION", track, camera_cfg.id,
                             confidence=0.88, timestamp=timestamp)
