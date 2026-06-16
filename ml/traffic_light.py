"""HSV-based traffic-light state classification (Stage 3 helper)."""
from __future__ import annotations

import numpy as np

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None

from .types import Detection
from .violations.geometry import crop


def _hsv_mask_fraction(hsv, bands, s_min, v_min) -> float:
    """Fraction of pixels falling inside any of the given hue bands."""
    total = hsv.shape[0] * hsv.shape[1]
    if total == 0:
        return 0.0
    count = 0
    for (h_lo, h_hi) in bands:
        lower = np.array([h_lo, s_min, v_min])
        upper = np.array([h_hi, 255, 255])
        count += int(cv2.inRange(hsv, lower, upper).astype(bool).sum())
    return count / total


def classify_traffic_light(frame, traffic_lights: list[Detection]) -> str:
    """Return RED / YELLOW / GREEN / UNKNOWN from the brightest light crop."""
    if cv2 is None or not traffic_lights:
        return "UNKNOWN"
    best_state, best_score = "UNKNOWN", 0.0
    for tl in traffic_lights:
        c = crop(frame, tl.bbox)
        if c is None:
            continue
        hsv = cv2.cvtColor(c, cv2.COLOR_BGR2HSV)
        red = _hsv_mask_fraction(hsv, [(0, 10), (170, 180)], 100, 100)
        yellow = _hsv_mask_fraction(hsv, [(20, 40)], 100, 100)
        green = _hsv_mask_fraction(hsv, [(40, 80)], 100, 100)
        state, score = max(
            (("RED", red), ("YELLOW", yellow), ("GREEN", green)), key=lambda kv: kv[1]
        )
        if score > best_score and score > 0.02:
            best_state, best_score = state, score
    return best_state
