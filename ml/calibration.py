"""Stage 6 — confidence calibration (Appendix C of plan)."""
from __future__ import annotations

import math


def calibrate_confidence(raw_conf: float, T: float = 1.3) -> float:
    """Temperature scaling to soften overconfident raw scores."""
    raw_conf = min(max(raw_conf, 1e-6), 1 - 1e-6)
    logit = math.log(raw_conf / (1 - raw_conf))
    return 1.0 / (1.0 + math.exp(-logit / T))


def compute_final_confidence(violation, *, temperature: float = 1.3,
                             frame_boost_per: float = 0.05, frame_boost_max: float = 0.15,
                             plate_boost: float = 0.05) -> float:
    base = calibrate_confidence(violation.raw_confidence or violation.confidence, temperature)
    fb = min(frame_boost_per * max(violation.consistent_frames - 1, 0), frame_boost_max)
    pb = plate_boost if (violation.plate_number and violation.plate_number != "UNREADABLE") else 0.0
    return min(base + fb + pb, 1.0)


def classify_action(final_conf: float, auto: float = 0.90, review: float = 0.70) -> str:
    if final_conf >= auto:
        return "AUTO_ENFORCE"
    if final_conf >= review:
        return "HUMAN_REVIEW"
    return "LOG_ONLY"
