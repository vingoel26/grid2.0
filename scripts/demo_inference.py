#!/usr/bin/env python3
"""Quick single-image / video demo of the pipeline.

Usage:
  python scripts/demo_inference.py --source sample.jpg
  python scripts/demo_inference.py --source sample_video.mp4 --camera BTP_MG_ROAD_01
  python scripts/demo_inference.py --synthetic            # no media needed
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.config import PipelineConfig  # noqa: E402
from ml.orchestrator import TrafficViolationOrchestrator  # noqa: E402


def run_image(orch, path, camera):
    import cv2

    frame = cv2.imread(path)
    if frame is None:
        print(f"Could not read image: {path}")
        return
    t0 = time.perf_counter()
    violations = orch.process_frame(frame, time.time(), camera)
    dt = (time.perf_counter() - t0) * 1000
    print(f"\nProcessed {path} in {dt:.1f}ms — {len(violations)} violation(s)")
    for v in violations:
        print(f"  • {v.type:22s} {v.action:13s} conf={v.final_confidence:.2f} "
              f"plate={v.plate_number} fine=₹{v.fine_inr}")


def run_video(orch, path, camera, max_frames):
    import cv2

    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        print(f"Could not open video: {path}")
        return
    total, count, n = 0, 0, 0
    while True:
        ok, frame = cap.read()
        if not ok or (max_frames and n >= max_frames):
            break
        n += 1
        t0 = time.perf_counter()
        violations = orch.process_frame(frame, time.time(), camera)
        total += (time.perf_counter() - t0) * 1000
        count += len(violations)
        for v in violations:
            print(f"  frame {n:5d} | {v.type:22s} {v.action:13s} conf={v.final_confidence:.2f}")
    cap.release()
    if n:
        print(f"\n{n} frames | {count} violations | avg {total/n:.1f}ms/frame "
              f"({1000*n/total:.1f} FPS)")


def run_synthetic(orch, camera):
    print("Synthetic mode — random frames (stub models emit no violations).")
    for i in range(10):
        frame = (np.random.rand(720, 1280, 3) * 255).astype("uint8")
        t0 = time.perf_counter()
        v = orch.process_frame(frame, time.time(), camera)
        print(f"  frame {i+1:2d} | {len(v)} violations | "
              f"{(time.perf_counter()-t0)*1000:.1f}ms")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", help="image or video path")
    ap.add_argument("--camera", default="BTP_MG_ROAD_01")
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--max-frames", type=int, default=0)
    args = ap.parse_args()

    cfg = PipelineConfig()
    print(f"Device: {cfg.device} | Vehicle model: {cfg.vehicle_model_path.name}")
    orch = TrafficViolationOrchestrator(cfg)

    if args.synthetic or not args.source:
        run_synthetic(orch, args.camera)
    elif args.source.lower().endswith((".jpg", ".jpeg", ".png", ".bmp")):
        run_image(orch, args.source, args.camera)
    else:
        run_video(orch, args.source, args.camera, args.max_frames)


if __name__ == "__main__":
    main()
