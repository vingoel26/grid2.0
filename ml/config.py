"""Pipeline configuration with hardware auto-select (Part 6 of plan).

Loads thresholds.yaml / cameras.yaml and resolves model paths. Picks the
YOLO11-X (GPU) or YOLO11-S (CPU) UVH-26 variant at runtime.
"""
from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent


def _detect_device() -> str:
    forced = os.getenv("DEVICE", "auto").lower()
    if forced in ("cpu", "cuda:0", "cuda"):
        return "cuda:0" if forced.startswith("cuda") else "cpu"
    try:
        import torch

        return "cuda:0" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def _load_yaml(path: Path) -> dict[str, Any]:
    if path.exists():
        with open(path) as f:
            return yaml.safe_load(f) or {}
    return {}


class CameraConfig:
    """Resolved per-camera geometry used by violation analyzers."""

    def __init__(self, raw: dict[str, Any]):
        self.id: str = raw["id"]
        self.name: str = raw.get("name", raw["id"])
        loc = raw.get("location", {}) or {}
        self.lat: float | None = loc.get("lat")
        self.lng: float | None = loc.get("lng")
        self.rtsp_url: str | None = raw.get("rtsp_url")
        self.expected_flow_direction: float = float(raw.get("expected_flow_direction", 0.0))
        self.stop_line_polygon: list = raw.get("stop_line_polygon") or []
        self.intersection_polygon: list = raw.get("intersection_polygon") or []
        self.no_parking_zones: list = raw.get("no_parking_zones") or []


class PipelineConfig:
    def __init__(self, data_dir: Path | None = None):
        self.device = _detect_device()
        self.is_gpu = self.device.startswith("cuda")
        self.data_dir = data_dir or (ROOT / "data")
        self.evidence_dir = Path(os.getenv("EVIDENCE_DIR", ROOT / "evidence"))
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

        # ── Model paths ──────────────────────────────────────────────
        self.yolo11x_path = self.data_dir / "uvh26_models/weights/YOLOv11-X/UVH-26-MV-YOLOv11-X.pt"
        self.yolo11s_path = self.data_dir / "uvh26_models/weights/YOLOv11-S/UVH-26-MV-YOLOv11-S.pt"
        self.vehicle_model_path = self.yolo11x_path if self.is_gpu else self.yolo11s_path
        self.person_model_path = "yolo11n.pt"  # auto-downloads via Ultralytics
        self.plate_model_path = self.data_dir / "plate_model/license-plate-finetune-v1s.pt"
        self.seatbelt_model_path = self.data_dir / "seatbelt_model/weights/best.pt"
        self.helmet_model_path = self.data_dir / "helmet_model/best.pt"
        self.scene_model_path = self.data_dir / "scene_model/best.pt"

        # ── Thresholds (from configs/thresholds.yaml) ────────────────
        self.thresholds = _load_yaml(ROOT / "configs/thresholds.yaml")
        det = self.thresholds.get("detection", {})
        self.img_size = det.get("imgsz_gpu", 640) if self.is_gpu else det.get("imgsz_cpu", 480)
        self.batch_size = 4 if self.is_gpu else 1
        self.vehicle_conf = det.get("vehicle_conf", 0.25)
        self.person_conf = det.get("person_conf", 0.30)
        self.plate_conf = det.get("plate_conf", 0.30)
        self.iou = det.get("iou", 0.70)

        # ── Cameras ──────────────────────────────────────────────────
        cam_raw = _load_yaml(ROOT / "configs/cameras.yaml").get("cameras", [])
        self.cameras: dict[str, CameraConfig] = {c["id"]: CameraConfig(c) for c in cam_raw}

        # ── Backend integration ──────────────────────────────────────
        self.backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        self.ml_api_key = os.getenv("ML_API_KEY", "gridlock-ml-key-change-me")
        self.enable_gemini = os.getenv("ENABLE_GEMINI_REVIEW", "false").lower() == "true"
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")

    def camera(self, camera_id: str) -> CameraConfig:
        """Return camera config; synthesizes a permissive default if unknown."""
        if camera_id in self.cameras:
            return self.cameras[camera_id]
        return CameraConfig({"id": camera_id, "expected_flow_direction": 0.0})

    @property
    def tracker_config(self) -> dict:
        t = self.thresholds.get("tracker", {})
        return dict(
            track_high_thresh=t.get("track_high_thresh", 0.5),
            track_low_thresh=t.get("track_low_thresh", 0.1),
            new_track_thresh=t.get("new_track_thresh", 0.6),
            track_buffer=t.get("track_buffer", 60),
            match_thresh=t.get("match_thresh", 0.85),
            with_reid=t.get("with_reid", True),
        )

    def vio(self, name: str) -> dict:
        """Per-violation threshold block."""
        return self.thresholds.get("violations", {}).get(name, {})
