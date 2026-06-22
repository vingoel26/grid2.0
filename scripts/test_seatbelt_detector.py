#!/usr/bin/env python3
"""Test Model D — Seatbelt Detector in isolation.

Detects seatbelt / no_seatbelt in an image. Works best on images showing
the front of a car with the driver visible through the windshield.

Usage:
  python scripts/test_seatbelt_detector.py --source test_image.jpg
"""
import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.config import PipelineConfig
from ml.models import SeatbeltDetector

COLORS = {
    "seatbelt": (0, 255, 0),      # green = good
    "no_seatbelt": (0, 0, 255),   # red = violation
}


def main():
    ap = argparse.ArgumentParser(description="Test Seatbelt Detector")
    ap.add_argument("--source", required=True, help="Path to test image")
    ap.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    args = ap.parse_args()

    cfg = PipelineConfig()
    print(f"Device: {cfg.device}")
    print(f"Model : {cfg.seatbelt_model_path.name}")
    print(f"Image : {args.source}\n")

    model = SeatbeltDetector(cfg.seatbelt_model_path, cfg.device, cfg.img_size)

    frame = cv2.imread(args.source)
    if frame is None:
        print(f"❌ Could not read image: {args.source}")
        return

    t0 = time.perf_counter()
    detections = model.detect(frame, args.conf, 0.7)
    dt = (time.perf_counter() - t0) * 1000

    print(f"⏱  Inference: {dt:.1f}ms")
    print(f"🔍 Found {len(detections)} detection(s):\n")

    for i, det in enumerate(detections):
        color = COLORS.get(det.cls_name, (128, 128, 128))
        x1, y1, x2, y2 = [int(c) for c in det.bbox]
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
        label = f"{det.cls_name} {det.confidence:.2f}"
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        emoji = "✅" if det.cls_name == "seatbelt" else "❌"
        print(f"  [{i+1}] {emoji} {det.cls_name:15s}  conf={det.confidence:.3f}  bbox=({x1},{y1},{x2},{y2})")

    out_path = "result_seatbelt.jpg"
    cv2.imwrite(out_path, frame)
    print(f"\n✅ Annotated image saved to: {out_path}")


if __name__ == "__main__":
    main()
