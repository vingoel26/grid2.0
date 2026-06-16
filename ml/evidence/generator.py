"""Stage 6 — evidence package generation.

Produces, per AUTO_ENFORCE / HUMAN_REVIEW violation:
  annotated_image.jpg, thumbnail.jpg, video_clip.mp4 (from a circular buffer),
  metadata.json, and a SHA-256 hash of the original frame for tamper-proofing.
"""
from __future__ import annotations

import hashlib
import json
import logging
from collections import deque
from pathlib import Path

import numpy as np

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None

log = logging.getLogger("ml.evidence")


class FrameBuffer:
    """Circular buffer of recent frames for clip extraction (per camera)."""

    def __init__(self, seconds: float = 3.0, fps: float = 30.0):
        self.maxlen = max(int(seconds * fps), 1)
        self.fps = fps
        self._buf: deque = deque(maxlen=self.maxlen)

    def push(self, frame: np.ndarray) -> None:
        self._buf.append(frame.copy() if frame is not None else None)

    def frames(self) -> list:
        return [f for f in self._buf if f is not None]


class EvidenceGenerator:
    def __init__(self, evidence_dir: Path, model_version: str = "gridlock-2.0"):
        self.dir = Path(evidence_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.model_version = model_version

    # -- public --------------------------------------------------------
    def generate(self, frame: np.ndarray, violation, timestamp: float,
                 frame_buffer: FrameBuffer | None = None) -> dict:
        vid = f"V_{int(timestamp)}_{violation.vehicle_track_id}"
        out = self.dir / vid
        out.mkdir(parents=True, exist_ok=True)
        paths: dict = {"violation_id": vid}

        sha = self._sha256(frame)
        paths["evidence_hash"] = sha

        if cv2 is not None and frame is not None:
            annotated = self._annotate(frame, violation)
            img_path = out / "annotated_image.jpg"
            cv2.imwrite(str(img_path), annotated)
            paths["evidence_image_path"] = str(img_path)

            thumb_path = out / "thumbnail.jpg"
            cv2.imwrite(str(thumb_path), self._thumbnail(frame, violation.vehicle_bbox))
            paths["evidence_thumbnail_path"] = str(thumb_path)

            if frame_buffer is not None:
                clip_path = self._write_clip(out, frame_buffer)
                if clip_path:
                    paths["evidence_video_path"] = clip_path

        meta = {
            "violation_id": vid,
            "type": violation.type,
            "violation_code": violation.violation_code,
            "fine_inr": violation.fine_inr,
            "camera_id": violation.camera_id,
            "vehicle_type": violation.vehicle_type,
            "vehicle_bbox": list(violation.vehicle_bbox),
            "plate_number": violation.plate_number,
            "plate_confidence": violation.plate_confidence,
            "raw_confidence": violation.raw_confidence,
            "final_confidence": violation.final_confidence,
            "enforcement_action": violation.action,
            "model_version": self.model_version,
            "occurred_at": timestamp,
            "evidence_hash": sha,
            "extra": violation.extra,
        }
        meta_path = out / "metadata.json"
        meta_path.write_text(json.dumps(meta, indent=2, default=str))
        paths["metadata_path"] = str(meta_path)
        return paths

    # -- helpers -------------------------------------------------------
    @staticmethod
    def _sha256(frame: np.ndarray | None) -> str:
        if frame is None:
            return ""
        return hashlib.sha256(np.ascontiguousarray(frame).tobytes()).hexdigest()

    def _annotate(self, frame: np.ndarray, violation) -> np.ndarray:
        img = frame.copy()
        x1, y1, x2, y2 = (int(v) for v in violation.vehicle_bbox)
        color = (0, 0, 255) if violation.action == "AUTO_ENFORCE" else (0, 165, 255)
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        label = f"{violation.type} {violation.final_confidence:.2f}"
        if violation.plate_number and violation.plate_number != "UNREADABLE":
            label += f" [{violation.plate_number}]"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(img, (x1, max(0, y1 - th - 6)), (x1 + tw, y1), color, -1)
        cv2.putText(img, label, (x1, max(10, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (255, 255, 255), 1, cv2.LINE_AA)
        return img

    def _thumbnail(self, frame: np.ndarray, bbox, size: int = 256) -> np.ndarray:
        h, w = frame.shape[:2]
        x1, y1, x2, y2 = bbox
        x1, y1 = max(0, int(x1)), max(0, int(y1))
        x2, y2 = min(w, int(x2)), min(h, int(y2))
        if x2 <= x1 or y2 <= y1:
            region = frame
        else:
            region = frame[y1:y2, x1:x2]
        return cv2.resize(region, (size, size))

    def _write_clip(self, out: Path, fb: FrameBuffer) -> str | None:
        frames = fb.frames()
        if not frames:
            return None
        h, w = frames[0].shape[:2]
        path = out / "video_clip.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(path), fourcc, fb.fps, (w, h))
        for f in frames:
            writer.write(f)
        writer.release()
        return str(path)
