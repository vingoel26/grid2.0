#!/usr/bin/env python3
"""Test Model F — Scene/Weather Classifier in isolation.

Classifies the overall scene condition: clear, hazy, rainy, low_light, or
motion_blur. This drives the adaptive image enhancement in Stage 0.

Usage:
  python scripts/test_scene_classifier.py --source test_image.jpg
"""
import argparse
import sys
import time
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.config import PipelineConfig
from ml.models import SceneClassifier

SCENE_EMOJI = {
    "clear": "☀️",
    "hazy": "🌫️",
    "rainy": "🌧️",
    "low_light": "🌙",
    "motion_blur": "💨",
}


def main():
    ap = argparse.ArgumentParser(description="Test Scene/Weather Classifier")
    ap.add_argument("--source", required=True, help="Path to test image")
    args = ap.parse_args()

    cfg = PipelineConfig()
    print(f"Device: {cfg.device}")
    print(f"Model : {cfg.scene_model_path.name}")
    print(f"Image : {args.source}\n")

    model = SceneClassifier(cfg.scene_model_path, cfg.device)
    print(f"Scene model available: {model.available}\n")

    frame = cv2.imread(args.source)
    if frame is None:
        print(f"❌ Could not read image: {args.source}")
        return

    t0 = time.perf_counter()
    scene = model.classify(frame)
    dt = (time.perf_counter() - t0) * 1000

    emoji = SCENE_EMOJI.get(scene, "❓")
    print(f"⏱  Inference: {dt:.1f}ms")
    print(f"{emoji} Scene classification: {scene.upper()}")

    if scene == "clear":
        print("   → No image enhancement needed")
    elif scene == "hazy":
        print("   → Will apply dehazing + contrast boost")
    elif scene == "rainy":
        print("   → Will apply rain-streak removal")
    elif scene == "low_light":
        print("   → Will apply CLAHE + brightness boost")
    elif scene == "motion_blur":
        print("   → Will apply sharpening filter")


if __name__ == "__main__":
    main()
