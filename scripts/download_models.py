#!/usr/bin/env python3
"""Download all required model weights from HuggingFace (Part 5 of plan).

Run once you have `huggingface-hub` installed and network access:
  python scripts/download_models.py
"""
from __future__ import annotations

import subprocess
import sys

DOWNLOADS = [
    ("UVH-26 YOLO11-X", ["hf", "download", "iisc-aim/UVH-26",
        "weights/YOLOv11-X/UVH-26-MV-YOLOv11-X.pt", "--local-dir", "data/uvh26_models"]),
    ("UVH-26 YOLO11-S", ["hf", "download", "iisc-aim/UVH-26",
        "weights/YOLOv11-S/UVH-26-MV-YOLOv11-S.pt", "--local-dir", "data/uvh26_models"]),
    ("License plate detector", ["hf", "download",
        "morsetechlab/yolov11-license-plate-detection", "--local-dir", "data/plate_model"]),
    ("Seatbelt detector", ["hf", "download",
        "RISEF/yolov11s-seatbelt", "--local-dir", "data/seatbelt_model"]),
]

# Helmet (E) and Scene (F) are fine-tuned on Kaggle — see notebooks/.
# COCO yolo11n (B), PaddleOCR (G), torchvision backbones auto-download at runtime.


def main():
    for name, cmd in DOWNLOADS:
        print(f"\n=== {name} ===\n$ {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"  ! failed: {e}\n  (install huggingface-hub: pip install huggingface-hub)")
            sys.exit(1)
    print("\nAll downloads complete. Helmet + scene weights: train via notebooks/.")


if __name__ == "__main__":
    main()
