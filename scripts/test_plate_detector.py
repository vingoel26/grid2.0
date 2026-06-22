#!/usr/bin/env python3
"""Test Model C + G — License Plate Detector + OCR in isolation.

Finds license plates in an image, draws bounding boxes, and attempts to read
the plate text using PaddleOCR.

Usage:
  python scripts/test_plate_detector.py --source test_image.jpg
"""
import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.config import PipelineConfig
from ml.models import PlateDetector, PlateOCR


def main():
    ap = argparse.ArgumentParser(description="Test License Plate Detector + OCR")
    ap.add_argument("--source", required=True, help="Path to test image")
    ap.add_argument("--conf", type=float, default=0.30, help="Confidence threshold")
    args = ap.parse_args()

    cfg = PipelineConfig()
    print(f"Device: {cfg.device}")
    print(f"Plate Model : {cfg.plate_model_path.name}")
    print(f"Image : {args.source}\n")

    plate_model = PlateDetector(cfg.plate_model_path, cfg.device, cfg.img_size)
    ocr = PlateOCR(cfg.device)

    frame = cv2.imread(args.source)
    if frame is None:
        print(f"❌ Could not read image: {args.source}")
        return

    h, w = frame.shape[:2]

    t0 = time.perf_counter()
    plates = plate_model.detect(frame, args.conf, 0.7)
    dt_detect = (time.perf_counter() - t0) * 1000

    print(f"⏱  Detection: {dt_detect:.1f}ms")
    print(f"🪪 Found {len(plates)} license plate(s):\n")

    for i, plate in enumerate(plates):
        x1, y1, x2, y2 = [int(c) for c in plate.bbox]

        # Crop plate region
        crop = frame[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]

        # OCR
        t1 = time.perf_counter()
        text, conf = ocr.read(crop)
        dt_ocr = (time.perf_counter() - t1) * 1000

        # Draw
        color = (0, 255, 0) if text != "UNREADABLE" else (0, 0, 255)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
        label = f"{text} ({conf:.2f})" if text != "UNREADABLE" else "UNREADABLE"
        cv2.putText(frame, label, (x1, y2 + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        print(f"  [{i+1}] Plate bbox=({x1},{y1},{x2},{y2})  conf={plate.confidence:.3f}")
        print(f"       OCR: \"{text}\" (conf={conf:.3f}, {dt_ocr:.1f}ms)")

    out_path = "result_plates.jpg"
    cv2.imwrite(out_path, frame)
    print(f"\n✅ Annotated image saved to: {out_path}")


if __name__ == "__main__":
    main()
