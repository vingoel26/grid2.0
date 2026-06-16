"""Stage 0 — scene-adaptive preprocessing (Part 2 of plan).

Maps a scene class to a targeted enhancement:
  clear       -> pass-through
  hazy        -> CLAHE (clipLimit=3.0)
  rainy       -> bilateral denoise (d=9, sigmaColor=75)
  low_light   -> gamma (2.2) + CLAHE
  motion_blur -> light sharpen (Wiener-style deconvolution approximation)
"""
from __future__ import annotations

import numpy as np

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None


class ImageEnhancer:
    def __init__(self) -> None:
        self._clahe = (
            cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)) if cv2 is not None else None
        )
        # precompute gamma LUT (gamma=2.2 brightening)
        if cv2 is not None:
            inv = 1.0 / 2.2
            self._gamma_lut = np.array(
                [((i / 255.0) ** inv) * 255 for i in range(256)], dtype=np.uint8
            )
        self._sharpen = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)

    def enhance(self, frame: np.ndarray, scene: str) -> np.ndarray:
        if cv2 is None or frame is None:
            return frame
        if scene == "clear":
            return frame
        if scene == "hazy":
            return self._apply_clahe(frame)
        if scene == "rainy":
            return cv2.bilateralFilter(frame, d=9, sigmaColor=75, sigmaSpace=75)
        if scene == "low_light":
            return self._apply_clahe(cv2.LUT(frame, self._gamma_lut))
        if scene == "motion_blur":
            return cv2.filter2D(frame, -1, self._sharpen)
        return frame

    def _apply_clahe(self, frame: np.ndarray) -> np.ndarray:
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l = self._clahe.apply(l)
        return cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)
