#!/usr/bin/env python3
"""Comprehensive pipeline tester — images, videos, webcam, and model health check.

USAGE:
  # 1. Check which models are loaded and working
  python scripts/test_pipeline.py --health

  # 2. Test on a single image (saves annotated output)
  python scripts/test_pipeline.py --image path/to/traffic.jpg

  # 3. Test on multiple images (folder)
  python scripts/test_pipeline.py --image-dir path/to/images/

  # 4. Test on a video (saves annotated output video + prints violations)
  python scripts/test_pipeline.py --video path/to/traffic.mp4

  # 5. Test on video with live preview window
  python scripts/test_pipeline.py --video path/to/traffic.mp4 --show

  # 6. Test webcam (live preview)
  python scripts/test_pipeline.py --webcam

  # 7. Test with specific camera config
  python scripts/test_pipeline.py --video clip.mp4 --camera BTP_MG_ROAD_01

  # 8. Quick synthetic test (no media files needed at all)
  python scripts/test_pipeline.py --synthetic

OUTPUT:
  All annotated images/videos are saved to: gridlock/test_output/
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import cv2
import numpy as np

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ml.config import PipelineConfig  # noqa: E402
from ml.orchestrator import TrafficViolationOrchestrator  # noqa: E402

OUTPUT_DIR = ROOT / "test_output"

# ── Annotation colors (BGR) ──────────────────────────────────────────────────
COLORS = {
    "HELMET_VIOLATION":     (0, 0, 255),      # red
    "SEATBELT_VIOLATION":   (0, 128, 255),     # orange
    "TRIPLE_RIDING":        (0, 0, 200),       # dark red
    "WRONG_SIDE_DRIVING":   (0, 255, 255),     # yellow
    "STOP_LINE_VIOLATION":  (255, 0, 255),     # magenta
    "RED_LIGHT_VIOLATION":  (255, 0, 0),       # blue
    "ILLEGAL_PARKING":      (255, 255, 0),     # cyan
    "NO_PLATE":             (128, 0, 255),     # purple
    "detection":            (0, 255, 0),       # green (for all detections)
}

FINE_MAP = {
    "HELMET_VIOLATION": "₹1,000", "SEATBELT_VIOLATION": "₹1,000",
    "TRIPLE_RIDING": "₹1,000", "WRONG_SIDE_DRIVING": "₹5,000",
    "STOP_LINE_VIOLATION": "₹1,000", "RED_LIGHT_VIOLATION": "₹5,000",
    "ILLEGAL_PARKING": "₹500", "NO_PLATE": "₹5,000",
}


def annotate_frame(frame, violations, detections=None, show_dets=True):
    """Draw violation bboxes and labels on frame. Returns annotated copy."""
    out = frame.copy()

    # Draw raw detections in green (if provided)
    if show_dets and detections:
        for det in detections:
            x1, y1, x2, y2 = [int(c) for c in det.bbox]
            cv2.rectangle(out, (x1, y1), (x2, y2), COLORS["detection"], 1)
            label = f"{det.cls_name} {det.confidence:.2f}"
            cv2.putText(out, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX,
                        0.4, COLORS["detection"], 1)

    # Draw violations in color
    for v in violations:
        color = COLORS.get(v.type, (255, 255, 255))
        x1, y1, x2, y2 = [int(c) for c in v.vehicle_bbox]
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 3)

        # Label with type, confidence, action
        label = f"{v.type.replace('_', ' ')} {v.final_confidence:.0%}"
        action_label = v.action.replace("_", " ")
        plate_label = f"Plate: {v.plate_number}" if v.plate_number else ""

        # Background rectangle for text
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(out, (x1, y1 - th - 10), (x1 + tw + 4, y1), color, -1)
        cv2.putText(out, label, (x1 + 2, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (255, 255, 255), 2)

        # Action badge below
        cv2.putText(out, action_label, (x1, y2 + 20), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, color, 2)
        if plate_label:
            cv2.putText(out, plate_label, (x1, y2 + 40), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (255, 255, 255), 1)

    # Stats overlay
    h, w = out.shape[:2]
    stats = f"Violations: {len(violations)}"
    cv2.putText(out, stats, (10, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    return out


# ── MODE: Health Check ──────────────────────────────────────────────────────
def run_health(cfg, orch):
    """Print which models are loaded and ready."""
    print("\n" + "=" * 60)
    print("  GRIDLOCK 2.0 — MODEL HEALTH CHECK")
    print("=" * 60)
    print(f"  Device:         {cfg.device}")
    print(f"  GPU available:  {cfg.is_gpu}")
    print(f"  Image size:     {cfg.img_size}")
    print(f"  Vehicle model:  {cfg.vehicle_model_path}")
    print()

    models = [
        ("A. Vehicle Detector (UVH-26)",    orch.vehicle_model),
        ("B. Person + Traffic Light (COCO)", orch.person_model),
        ("C. Plate Detector",               orch.plate_model),
        ("D. Seatbelt Detector",            orch.seatbelt_model),
        ("E. Helmet Classifier",            orch.helmet_classifier),
        ("F. Scene Classifier",             orch.scene_classifier),
        ("G. Plate OCR (PaddleOCR)",        orch.ocr),
    ]

    all_ok = True
    for name, model in models:
        avail = model.available
        status = "✅ LOADED" if avail else "⚠️  STUB (weights missing)"
        if not avail:
            all_ok = False
        print(f"  {name:40s} {status}")

    print()
    if all_ok:
        print("  🟢 All 7 models loaded — pipeline fully operational!")
    else:
        print("  🟡 Some models in stub mode — pipeline will run but those")
        print("     violation types won't be detected. Download missing weights.")
    print()

    # Quick latency test with synthetic frame
    print("  Running latency benchmark (10 synthetic frames)...")
    times = []
    for _ in range(10):
        frame = (np.random.rand(720, 1280, 3) * 255).astype("uint8")
        t0 = time.perf_counter()
        orch.process_frame(frame, time.time(), "health_check")
        times.append((time.perf_counter() - t0) * 1000)

    avg = sum(times) / len(times)
    fps = 1000 / avg if avg > 0 else 0
    print(f"  Average: {avg:.1f}ms/frame ({fps:.1f} FPS)")
    print(f"  Min:     {min(times):.1f}ms")
    print(f"  Max:     {max(times):.1f}ms")
    print("=" * 60 + "\n")


# ── MODE: Single Image ──────────────────────────────────────────────────────
def run_image(orch, path: str, camera: str, show: bool = False):
    """Process one image, print violations, save annotated output."""
    frame = cv2.imread(path)
    if frame is None:
        print(f"❌ Could not read image: {path}")
        return

    print(f"\n🖼️  Processing: {path}")
    print(f"   Size: {frame.shape[1]}x{frame.shape[0]}")

    t0 = time.perf_counter()
    violations = orch.process_frame(frame, time.time(), camera)
    dt = (time.perf_counter() - t0) * 1000

    print(f"   Latency: {dt:.1f}ms")
    print(f"   Violations found: {len(violations)}")

    if violations:
        print()
        print(f"   {'Type':<25s} {'Action':<15s} {'Conf':>6s} {'Plate':<14s} {'Fine':>8s}")
        print(f"   {'-'*25} {'-'*15} {'-'*6} {'-'*14} {'-'*8}")
        for v in violations:
            plate = v.plate_number or "—"
            fine = FINE_MAP.get(v.type, "—")
            print(f"   {v.type:<25s} {v.action:<15s} {v.final_confidence:5.1%} {plate:<14s} {fine:>8s}")
    else:
        print("   ✅ No violations detected.")

    # Save annotated output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stem = Path(path).stem
    out_path = OUTPUT_DIR / f"{stem}_annotated.jpg"
    annotated = annotate_frame(frame, violations)
    cv2.imwrite(str(out_path), annotated)
    print(f"\n   📁 Saved: {out_path}")

    if show:
        cv2.imshow("Gridlock Test — Image", annotated)
        print("   Press any key to close...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()


# ── MODE: Image Directory ────────────────────────────────────────────────────
def run_image_dir(orch, dir_path: str, camera: str):
    """Process all images in a directory."""
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    images = sorted([
        f for f in Path(dir_path).iterdir()
        if f.suffix.lower() in exts
    ])

    if not images:
        print(f"❌ No images found in: {dir_path}")
        return

    print(f"\n📁 Processing {len(images)} images from: {dir_path}")
    total_violations = 0
    total_time = 0

    for img_path in images:
        frame = cv2.imread(str(img_path))
        if frame is None:
            continue

        t0 = time.perf_counter()
        violations = orch.process_frame(frame, time.time(), camera)
        dt = (time.perf_counter() - t0) * 1000
        total_time += dt
        total_violations += len(violations)

        status = f"{len(violations)} violation(s)" if violations else "clean"
        print(f"   {img_path.name:<40s} {dt:6.1f}ms  {status}")

        for v in violations:
            print(f"     └─ {v.type} ({v.action}, {v.final_confidence:.0%})")

        # Save annotated
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        annotated = annotate_frame(frame, violations)
        cv2.imwrite(str(OUTPUT_DIR / f"{img_path.stem}_annotated.jpg"), annotated)

    print(f"\n   Total: {len(images)} images, {total_violations} violations, "
          f"avg {total_time/len(images):.1f}ms/image")
    print(f"   📁 Annotated outputs saved to: {OUTPUT_DIR}")


# ── MODE: Video ──────────────────────────────────────────────────────────────
def run_video(orch, path: str, camera: str, max_frames: int = 0,
              show: bool = False, frame_skip: int = 1):
    """Process video, save annotated output video, print per-frame violations."""
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        print(f"❌ Could not open video: {path}")
        return

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"\n🎬 Processing: {path}")
    print(f"   Resolution: {w}x{h} @ {fps:.1f} FPS")
    print(f"   Total frames: {total_frames}")
    print(f"   Frame skip: {frame_skip} (processing every {frame_skip}th frame)")
    if max_frames:
        print(f"   Max frames to process: {max_frames}")
    print()

    # Setup output video
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stem = Path(path).stem
    out_path = OUTPUT_DIR / f"{stem}_annotated.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out_path), fourcc, fps / frame_skip, (w, h))

    idx = 0
    processed = 0
    total_violations = 0
    times = []
    violation_log = []

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        idx += 1

        if idx % frame_skip != 0:
            continue

        if max_frames and processed >= max_frames:
            break

        t0 = time.perf_counter()
        violations = orch.process_frame(frame, time.time(), camera)
        dt = (time.perf_counter() - t0) * 1000
        times.append(dt)
        processed += 1
        total_violations += len(violations)

        # Print violations as they occur
        for v in violations:
            violation_log.append((idx, v))
            print(f"   frame {idx:5d} │ {v.type:<25s} {v.action:<15s} "
                  f"conf={v.final_confidence:.0%} plate={v.plate_number or '—'}")

        # Annotate and write
        annotated = annotate_frame(frame, violations)

        # FPS overlay
        current_fps = 1000 / dt if dt > 0 else 0
        cv2.putText(annotated, f"{current_fps:.0f} FPS | {dt:.0f}ms",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        writer.write(annotated)

        if show:
            # Resize for display if too large
            display = annotated
            if w > 1400:
                scale = 1400 / w
                display = cv2.resize(annotated, None, fx=scale, fy=scale)
            cv2.imshow("Gridlock Test — Video (Q to quit)", display)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27:  # Q or ESC
                print("\n   ⏹️  Stopped by user.")
                break

        # Progress every 100 frames
        if processed % 100 == 0:
            avg = sum(times[-100:]) / min(len(times), 100)
            print(f"   ... frame {idx}/{total_frames} | avg {avg:.1f}ms | "
                  f"{total_violations} violations so far")

    cap.release()
    writer.release()
    if show:
        cv2.destroyAllWindows()

    # Summary
    if times:
        avg_ms = sum(times) / len(times)
        avg_fps = 1000 / avg_ms if avg_ms > 0 else 0
        print(f"\n{'='*60}")
        print(f"  VIDEO SUMMARY")
        print(f"{'='*60}")
        print(f"  Frames processed: {processed}/{total_frames}")
        print(f"  Total violations: {total_violations}")
        print(f"  Avg latency:      {avg_ms:.1f}ms ({avg_fps:.1f} FPS)")
        print(f"  Min latency:      {min(times):.1f}ms")
        print(f"  Max latency:      {max(times):.1f}ms")
        print(f"  Output video:     {out_path}")

        if violation_log:
            print(f"\n  Violation breakdown:")
            from collections import Counter
            counts = Counter(v.type for _, v in violation_log)
            for vtype, count in counts.most_common():
                print(f"    {vtype:<25s} {count:3d}")

        print(f"{'='*60}\n")


# ── MODE: Webcam ─────────────────────────────────────────────────────────────
def run_webcam(orch, camera: str, device_idx: int = 0):
    """Live webcam inference with preview window."""
    cap = cv2.VideoCapture(device_idx)
    if not cap.isOpened():
        print(f"❌ Could not open webcam (device {device_idx})")
        return

    print(f"\n📹 Webcam mode — press Q to quit")
    print(f"   Camera config: {camera}")

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        t0 = time.perf_counter()
        violations = orch.process_frame(frame, time.time(), camera)
        dt = (time.perf_counter() - t0) * 1000
        fps = 1000 / dt if dt > 0 else 0

        annotated = annotate_frame(frame, violations)
        cv2.putText(annotated, f"{fps:.0f} FPS | {dt:.0f}ms",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        for v in violations:
            print(f"   {v.type:<25s} {v.action:<15s} conf={v.final_confidence:.0%}")

        cv2.imshow("Gridlock Test — Webcam (Q to quit)", annotated)
        if (cv2.waitKey(1) & 0xFF) in (ord("q"), 27):
            break

    cap.release()
    cv2.destroyAllWindows()


# ── MODE: Synthetic ──────────────────────────────────────────────────────────
def run_synthetic(orch, camera: str):
    """Test pipeline with random noise frames — verifies pipeline runs end-to-end."""
    print("\n🧪 Synthetic test (random noise — no real detections expected)")
    print("   This tests that the pipeline loads and runs without crashing.\n")

    for i in range(10):
        frame = (np.random.rand(720, 1280, 3) * 255).astype("uint8")
        t0 = time.perf_counter()
        violations = orch.process_frame(frame, time.time(), camera)
        dt = (time.perf_counter() - t0) * 1000
        print(f"   frame {i+1:2d}/10 │ {dt:6.1f}ms │ {len(violations)} violations")

    print("\n   ✅ Pipeline runs end-to-end without errors!")


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(
        description="Test the Gridlock 2.0 traffic violation pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/test_pipeline.py --health
  python scripts/test_pipeline.py --image traffic.jpg
  python scripts/test_pipeline.py --image-dir ./test_images/
  python scripts/test_pipeline.py --video traffic.mp4
  python scripts/test_pipeline.py --video traffic.mp4 --show
  python scripts/test_pipeline.py --video traffic.mp4 --show --frame-skip 3
  python scripts/test_pipeline.py --webcam
  python scripts/test_pipeline.py --synthetic
        """,
    )
    ap.add_argument("--health", action="store_true",
                    help="Run model health check + latency benchmark")
    ap.add_argument("--image", type=str,
                    help="Path to a single image")
    ap.add_argument("--image-dir", type=str,
                    help="Path to a directory of images")
    ap.add_argument("--video", type=str,
                    help="Path to a video file")
    ap.add_argument("--webcam", action="store_true",
                    help="Use webcam (device 0)")
    ap.add_argument("--synthetic", action="store_true",
                    help="Test with random noise frames (no media needed)")
    ap.add_argument("--camera", default="BTP_MG_ROAD_01",
                    help="Camera ID for config lookup (default: BTP_MG_ROAD_01)")
    ap.add_argument("--show", action="store_true",
                    help="Show live preview window (for video/webcam)")
    ap.add_argument("--max-frames", type=int, default=0,
                    help="Max frames to process from video (0 = all)")
    ap.add_argument("--frame-skip", type=int, default=1,
                    help="Process every Nth frame (default: 1 = every frame)")
    args = ap.parse_args()

    # Initialize pipeline
    print("\n⚡ Initializing Gridlock 2.0 Pipeline...")
    cfg = PipelineConfig()
    print(f"   Device: {cfg.device}")
    print(f"   Vehicle model: {cfg.vehicle_model_path.name}")
    orch = TrafficViolationOrchestrator(cfg)

    # Dispatch to mode
    if args.health:
        run_health(cfg, orch)
    elif args.image:
        run_image(orch, args.image, args.camera, args.show)
    elif args.image_dir:
        run_image_dir(orch, args.image_dir, args.camera)
    elif args.video:
        run_video(orch, args.video, args.camera, args.max_frames, args.show,
                  args.frame_skip)
    elif args.webcam:
        run_webcam(orch, args.camera)
    elif args.synthetic:
        run_synthetic(orch, args.camera)
    else:
        # Default: run health check
        print("   No mode specified — running health check (use --help for options)")
        run_health(cfg, orch)


if __name__ == "__main__":
    main()
