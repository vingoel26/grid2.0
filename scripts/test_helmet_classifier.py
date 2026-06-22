#!/usr/bin/env python3
"""Test Model E — Helmet Classifier in isolation.

Uses the UVH-26 detector to find motorcycles, then the person detector to find
riders, crops their heads, and runs the EfficientNetV2 helmet classifier.
Draws results and saves the annotated image.

Usage:
  python scripts/test_helmet_classifier.py --source test_image.jpg
"""
import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.config import PipelineConfig
from ml.models import VehicleDetector, PersonDetector, HelmetClassifier
from ml.types import TWO_WHEELER

HELMET_COLORS = {
    "helmet": (0, 255, 0),       # green
    "no_helmet": (0, 0, 255),    # red
    "ambiguous": (0, 165, 255),  # orange
}


def main():
    ap = argparse.ArgumentParser(description="Test Helmet Classifier")
    ap.add_argument("--source", required=True, help="Path to test image")
    args = ap.parse_args()

    cfg = PipelineConfig()
    print(f"Device: {cfg.device}\n")

    vehicle_model = VehicleDetector(cfg.vehicle_model_path, cfg.device, cfg.img_size)
    person_model = PersonDetector(cfg.person_model_path, cfg.device, cfg.img_size)
    helmet_model = HelmetClassifier(cfg.helmet_model_path, cfg.device)

    print(f"Helmet model available: {helmet_model.available}")

    frame = cv2.imread(args.source)
    if frame is None:
        print(f"❌ Could not read image: {args.source}")
        return

    h, w = frame.shape[:2]

    # Step 1: Find vehicles
    t0 = time.perf_counter()
    vehicles = vehicle_model.detect(frame, 0.25, 0.7)
    two_wheelers = [v for v in vehicles if v.cls_name == TWO_WHEELER]
    print(f"\n🏍  Found {len(two_wheelers)} two-wheeler(s) out of {len(vehicles)} vehicles")

    # Step 2: Find persons
    persons = person_model.detect(frame, 0.30, 0.7)
    persons_only = [p for p in persons if p.cls_name == "person"]
    print(f"👤 Found {len(persons_only)} person(s)")

    # Step 3: For each two-wheeler, find overlapping persons and crop heads
    helmet_results = []
    for tw in two_wheelers:
        tx1, ty1, tx2, ty2 = [int(c) for c in tw.bbox]
        cv2.rectangle(frame, (tx1, ty1), (tx2, ty2), (255, 255, 0), 2)
        cv2.putText(frame, f"Motorcycle {tw.confidence:.2f}", (tx1, ty1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        for person in persons_only:
            px1, py1, px2, py2 = [int(c) for c in person.bbox]
            # Check overlap between person and two-wheeler
            overlap_x = max(0, min(tx2, px2) - max(tx1, px1))
            overlap_y = max(0, min(ty2, py2) - max(ty1, py1))
            if overlap_x > 0 and overlap_y > 0:
                # Crop the top 40% of the person bbox as "head"
                head_h = int((py2 - py1) * 0.4)
                head_crop = frame[max(0, py1):min(h, py1 + head_h),
                                  max(0, px1):min(w, px2)]

                if head_crop.size > 0:
                    result = helmet_model.classify(head_crop)
                    color = HELMET_COLORS.get(result.class_name, (128, 128, 128))

                    cv2.rectangle(frame, (px1, py1), (px2, py1 + head_h), color, 3)
                    label = f"{result.class_name} {result.confidence:.2f}"
                    cv2.putText(frame, label, (px1, py1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

                    helmet_results.append(result)
                    print(f"\n  🪖 Rider: {result.class_name} (conf={result.confidence:.3f})")

    dt = (time.perf_counter() - t0) * 1000
    print(f"\n⏱  Total: {dt:.1f}ms")

    if not helmet_results:
        print("⚠️  No riders detected on two-wheelers. Try a different image with motorcycles!")

    out_path = "result_helmet.jpg"
    cv2.imwrite(out_path, frame)
    print(f"✅ Annotated image saved to: {out_path}")


if __name__ == "__main__":
    main()
