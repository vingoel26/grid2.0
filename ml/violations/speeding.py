"""V6 — Dynamic Speeding Enforcement via Perspective Transformation."""
from __future__ import annotations

import cv2
import numpy as np

from ..types import Track
from .geometry import make_violation


class PerspectiveTransformer:
    """Uses OpenCV Homography to warp 2D pixels into 3D meters for accurate speed calculation."""
    def __init__(self, src_pts: list[tuple[float, float]], dst_pts: list[tuple[float, float]]):
        self.H, _ = cv2.findHomography(
            np.array(src_pts, dtype=np.float32), 
            np.array(dst_pts, dtype=np.float32)
        )
        
    def transform(self, pt: tuple[float, float]) -> tuple[float, float]:
        pts = np.array([[pt]], dtype=np.float32)
        warped = cv2.perspectiveTransform(pts, self.H)
        return float(warped[0][0][0]), float(warped[0][0][1])


# Example Calibration for Hackathon (Assume a 10m x 10m patch on the road)
# In production, these come from `cameras.yaml` calibrated by a technician.
DEFAULT_SRC = [(300, 600), (900, 600), (500, 300), (700, 300)]
DEFAULT_DST = [(0, 10), (10, 10), (0, 0), (10, 0)]

# Singleton Transformer for the demo
_TRANSFORMER = PerspectiveTransformer(DEFAULT_SRC, DEFAULT_DST)

def check_speeding(track: Track, cfg: dict, camera_id: str, timestamp: float = 0.0, fps: float = 30.0):
    """Calculates KM/H using Homography and triggers SPEEDING violation."""
    speed_limit_kmh = cfg.get("speed_limit", 60.0)
    persist = cfg.get("persist_frames", 3)
    
    # We need at least 5 frames of trajectory to calculate a smooth speed
    if len(track.trajectory) < 5:
        track.speeding_frames = 0
        return
        
    start_pt = track.trajectory[-5]
    end_pt = track.trajectory[-1]
    
    # Warp 2D pixel centers to 3D real-world meters
    m_start = _TRANSFORMER.transform(start_pt)
    m_end = _TRANSFORMER.transform(end_pt)
    
    # Euclidean distance in meters
    distance_meters = np.sqrt((m_end[0] - m_start[0])**2 + (m_end[1] - m_start[1])**2)
    
    # Time passed across these frames
    time_seconds = 5.0 / fps
    
    if time_seconds > 0:
        speed_mps = distance_meters / time_seconds
        speed_kmh = speed_mps * 3.6
        
        if speed_kmh > speed_limit_kmh:
            track.speeding_frames += 1
            if track.speeding_frames >= persist:
                # Add the exact calculated speed into extra payload for the dashboard
                violation = make_violation(
                    "SPEEDING", track, camera_id, 0.95, timestamp, 
                    consistent_frames=track.speeding_frames
                )
                violation.extra["calculated_speed_kmh"] = round(speed_kmh, 1)
                violation.extra["speed_limit"] = speed_limit_kmh
                yield violation
                return

    track.speeding_frames = 0
