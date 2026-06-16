"""V4 — Wrong-side driving (A + Tracker). Trajectory angle vs expected flow."""
from __future__ import annotations

import math

from ..types import Track
from .geometry import make_violation


def check_wrong_side(track: Track, camera_cfg, cfg: dict, timestamp: float = 0.0):
    min_traj = cfg.get("min_trajectory", 10)
    angle_th = math.radians(cfg.get("angle_deg", 120))
    persist = cfg.get("persist_frames", 10)

    if len(track.trajectory) < min_traj:
        return

    p_now = track.trajectory[-1]
    p_then = track.trajectory[-min_traj]
    dx, dy = p_now[0] - p_then[0], p_now[1] - p_then[1]
    if abs(dx) < 1 and abs(dy) < 1:  # stationary — not wrong-side
        track.wrong_side_frames = 0
        return

    actual = math.atan2(dy, dx)
    diff = abs(actual - camera_cfg.expected_flow_direction)
    if diff > math.pi:
        diff = 2 * math.pi - diff

    if diff > angle_th:
        track.wrong_side_frames += 1
        if track.wrong_side_frames >= persist:
            conf = min(0.70 + 0.02 * track.wrong_side_frames, 0.95)
            yield make_violation("WRONG_SIDE_DRIVING", track, camera_cfg.id, conf,
                                 timestamp, angle_diff_deg=math.degrees(diff),
                                 consistent_frames=track.wrong_side_frames)
    else:
        track.wrong_side_frames = 0
