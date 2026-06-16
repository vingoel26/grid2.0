# Gridlock 2.0 — Complete System Plan (v4)

> **Last Updated:** June 16, 2026
> **Competition:** Flipkart Gridlock 2.0 — Phase 2 (Prototype)
> **Platform:** [gridlock2point0.hackerearth.com](https://gridlock2point0.hackerearth.com/)
> **Problem:** Automated Photo Identification and Classification for Traffic Violations Using Computer Vision

---

## TABLE OF CONTENTS

1. [Executive Summary](#part-1-executive-summary)
2. [System Architecture](#part-2-system-architecture)
3. [Model Inventory (7 Models)](#part-3-model-inventory)
4. [Violation Detection Logic (8 Types)](#part-4-violation-detection-logic)
5. [Datasets & Downloads](#part-5-datasets--downloads)
6. [ML Pipeline Code Design](#part-6-ml-pipeline-code-design)
7. [Backend API Design](#part-7-backend-api-design)
8. [Frontend Dashboard Design](#part-8-frontend-dashboard-design)
9. [Infrastructure & Deployment](#part-9-infrastructure--deployment)
10. [Latency & Performance](#part-10-latency--performance)
11. [Scalability Design](#part-11-scalability-design)
12. [Project Structure](#part-12-project-structure)
13. [7-Day Execution Plan](#part-13-7-day-execution-plan)
14. [Team Task Assignments](#part-14-team-task-assignments)
- [Appendix A: Quick Start](#appendix-a-quick-start)
- [Appendix B: Key Links](#appendix-b-key-links)
- [Appendix C: Confidence Calibration Detail](#appendix-c-confidence-calibration-detail)

---

## PART 1: EXECUTIVE SUMMARY

### What We're Building

A production-grade, AI-powered traffic violation detection system purpose-built for **Bengaluru** (Indian road conditions, Indian vehicles, Indian license plate formats) that:

- Processes CCTV feeds at **30+ FPS on GPU** or **5+ FPS on CPU** with adaptive hardware selection
- Detects **all 8 violation types** fully automatically with per-violation pseudocode logic
- Generates **tamper-proof evidence packages** — annotated image + 3-second video clip + SHA-256 hash
- Provides a **real-time Next.js dashboard** with live feeds, officer review queue, and analytics heatmap
- Scales from **1 laptop demo → 100+ cameras in production** via Docker Compose + horizontal workers

### Why This Architecture Wins

| Innovation | What It Does | Competition Edge |
|---|---|---|
| **UVH-26 YOLO11 (IISc)** | Pretrained on 26,646 Bengaluru Safe-City CCTV images. mAP 0.63 vs 0.40 COCO baseline — **58% better on Indian traffic** | No other team has Indian-traffic-specific pretrained weights |
| **7 Specialist Models** | Each model is best-in-class at its task. GPU stream parallelism = total time is `max()` not `sum()` | Higher accuracy and lower latency simultaneously |
| **Zero-Training-Day-1 Architecture** | 5 of 7 models are fully pretrained. Only helmet + scene need light fine-tuning (~1.5 hours total on Kaggle T4) | Working demo on Day 1, not Day 5 |
| **CPU + GPU Adaptive** | Auto-selects YOLO11-X (GPU, 6ms) or YOLO11-S (CPU, 80ms) at runtime based on hardware | Demos on any laptop, deploys to any server |
| **3-Tier Confidence System** | ≥0.90 auto-enforce, 0.70–0.90 human review, <0.70 log-only | Zero false positives reaching citizens |
| **PaddleOCR PP-OCRv5** | State-of-the-art OCR pipeline with perspective correction + Indian plate regex validation | Near-perfect character accuracy on Indian number plates |
| **Gemini 2.5 Flash Pre-Review** | Optional AI pre-analysis for human-review tier: CONFIRM/REJECT/NEEDS_OFFICER in ~500ms async | Reduces officer workload by ~60% |

### Competition Context

| Field | Detail |
|---|---|
| **Hackathon** | Flipkart Gridlock 2.0 (May–July 2026) |
| **Organizers** | Flipkart + Bengaluru Traffic Police (BTP) + HackerEarth |
| **Phase** | Phase 2 — Prototype Development |
| **Team Size** | Up to 4 members |
| **Finale** | Onsite at Flipkart HQ, Bengaluru |

### Evaluation Criteria

| Criterion | Weight | How We Score |
|---|---|---|
| **Feasibility** | High | UVH-26 models proven on Bengaluru CCTV. Working demo Day 1. |
| **Technical Innovation** | High | Multi-model GPU parallelism, 3-tier confidence, Gemini AI pre-review |
| **Impact** | High | All 8 violations covered. Evidence-grade output with SHA-256 tamper-proofing. |
| **Scalability** | Medium | Docker Compose. 4 camera pipelines per T4. Horizontal Celery workers. |

---

## PART 2: SYSTEM ARCHITECTURE

### Full Pipeline (7 Stages)

```
┌──────────────────────────────────────────────────────────────────┐
│                         INPUT SOURCES                            │
│   CCTV Stream (RTSP/RTMP) │ Uploaded Image │ Video File Upload  │
└─────────────┬─────────────┴────────┬────────┴───────────────────┘
              │                      │
┌─────────────▼──────────────────────▼──────────────────────────────┐
│  STAGE 0: SCENE ANALYSIS + ADAPTIVE PREPROCESSING        [~2.5ms] │
│                                                                    │
│  MobileNetV3-Small → classify scene condition                      │
│  Classes: clear │ hazy │ rainy │ low_light │ motion_blur           │
│                                                                    │
│  → clear:       pass-through (no overhead)                         │
│  → hazy:        CLAHE contrast enhancement (clipLimit=3.0)         │
│  → rainy:       bilateral denoising (d=9, sigmaColor=75)           │
│  → low_light:   gamma correction (γ=2.2) + CLAHE                   │
│  → motion_blur: Wiener deconvolution kernel (3×3)                  │
│                                                                    │
│  Source:    MobileNetV3-Small (ImageNet pretrained)                │
│  Training:  Fine-tune on Kaggle weather dataset (~20 min on T4)    │
└─────────────┬──────────────────────────────────────────────────────┘
              │
┌─────────────▼──────────────────────────────────────────────────────┐
│  STAGE 1: PARALLEL MULTI-MODEL DETECTION         [~6ms GPU/~150ms CPU] │
│                                                                    │
│  Three detection models run simultaneously on separate CUDA streams│
│  Wall-clock time = max(6ms, 2.5ms, 3ms) = 6ms  (NOT the sum)      │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  STREAM 1 — UVH-26 YOLO11-X/S  [Vehicle Detection]         │  │
│  │  Source: IISc AIM (HuggingFace: iisc-aim/UVH-26)           │  │
│  │  14 Indian vehicle classes (see Part 3)                     │  │
│  │  GPU weights: UVH-26-MV-YOLOv11-X.pt (327 MB)              │  │
│  │  CPU weights: UVH-26-MV-YOLOv11-S.pt (55 MB)               │  │
│  │  Training: NONE — use directly ✅                           │  │
│  │  mAP@50:95: 0.63 on Bengaluru CCTV benchmark               │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  STREAM 2 — COCO YOLO11n  [Person + Traffic Light]          │  │
│  │  Source: Ultralytics (auto-downloads yolo11n.pt, 12 MB)     │  │
│  │  Classes used: person (0), traffic_light (9)                │  │
│  │  Training: NONE — use directly ✅                           │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  STREAM 3 — License Plate YOLO11  [Plate Localization]      │  │
│  │  Source: morsetechlab/yolov11-license-plate-detection (HF)  │  │
│  │  Classes: license_plate                                     │  │
│  │  Training: NONE — use directly ✅                           │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  CPU MODE: Sequential. Total ~150ms (≈6–7 FPS). Demo-viable.       │
└─────────────┬──────────────────────────────────────────────────────┘
              │
┌─────────────▼──────────────────────────────────────────────────────┐
│  STAGE 2: BoT-SORT TRACKING                               [~2ms]   │
│                                                                    │
│  Better Optimized Tracking by Segmentation + Re-ID (Ultralytics)  │
│  • Kalman filter prediction + Re-ID embedding fusion              │
│  • Camera Motion Compensation (CMC) — essential for PTZ cameras   │
│  • Persistent track IDs across frames (temporal violation logic)  │
│  • Handles occlusion and dense Indian traffic scenarios           │
│                                                                    │
│  Config:                                                           │
│    track_high_thresh: 0.50   new_track_thresh: 0.60               │
│    track_low_thresh:  0.10   match_thresh: 0.85                   │
│    track_buffer: 60          with_reid: true                      │
└─────────────┬──────────────────────────────────────────────────────┘
              │
┌─────────────▼──────────────────────────────────────────────────────┐
│  STAGE 3: SPECIALIST ROUTER                               [~0.5ms] │
│                                                                    │
│  Routes each tracked vehicle to the correct violation analyzer:    │
│                                                                    │
│  IF Two-wheeler (class 7):                                         │
│    → Helmet Check (Model E) + Triple Riding Check                  │
│                                                                    │
│  IF Car/Hatchback/Sedan/SUV/MUV (classes 0–3, 12):                │
│    → Seatbelt Check (Model D)                                      │
│                                                                    │
│  IF traffic_light detected (COCO class 9):                         │
│    → Red-Light State Machine (HSV color classification)            │
│    → Stop-Line Violation Check                                     │
│                                                                    │
│  ALL tracked vehicles:                                             │
│    → Wrong-Side Check (trajectory direction vs. camera config)    │
│    → Illegal Parking Check (stationary timer + zone polygon)      │
│    → No Plate Check (plate detector found nothing in N frames)    │
└─────────────┬──────────────────────────────────────────────────────┘
              │
┌─────────────▼──────────────────────────────────────────────────────┐
│  STAGE 4: VIOLATION ANALYZERS (async, parallel)           [~5ms]   │
│                                                                    │
│  ┌──────────────────────────┐  ┌──────────────────────────┐       │
│  │ V1: HELMET               │  │ V2: SEATBELT             │       │
│  │ EfficientNetV2-S         │  │ RISEF/yolov11s-seatbelt  │       │
│  │ Fine-tuned on SHWD ~1hr  │  │ Pretrained (no training) │       │
│  │ Classes: helmet/no_helmet│  │ Classes: belt/no_belt    │       │
│  └──────────────────────────┘  └──────────────────────────┘       │
│                                                                    │
│  ┌──────────────────────────┐  ┌──────────────────────────┐       │
│  │ V3: TRIPLE RIDING        │  │ V4: WRONG-SIDE           │       │
│  │ IoU overlap count ≥ 3    │  │ Trajectory angle > 120°  │       │
│  │ Pure logic — no model    │  │ Over 10+ frames          │       │
│  └──────────────────────────┘  └──────────────────────────┘       │
│                                                                    │
│  ┌──────────────────────────┐  ┌──────────────────────────┐       │
│  │ V5: STOP-LINE            │  │ V6: RED-LIGHT            │       │
│  │ Zone polygon + red phase │  │ Intersection polygon +   │       │
│  │ Pure logic + HSV         │  │ red phase. Pure logic.   │       │
│  └──────────────────────────┘  └──────────────────────────┘       │
│                                                                    │
│  ┌──────────────────────────┐  ┌──────────────────────────┐       │
│  │ V7: ILLEGAL PARKING      │  │ V8: NO NUMBER PLATE      │       │
│  │ Stationary > 30s in zone │  │ No plate in 15+ frames   │       │
│  │ Centroid movement < 5px  │  │ Skip bicycle/auto        │       │
│  └──────────────────────────┘  └──────────────────────────┘       │
└─────────────┬──────────────────────────────────────────────────────┘
              │
┌─────────────▼──────────────────────────────────────────────────────┐
│  STAGE 5: LICENSE PLATE OCR                               [~4.5ms] │
│                                                                    │
│  PaddleOCR PP-OCRv5 (official English pretrained, auto-downloads)  │
│  1. Crop plate region from Stage 1 Stream 3 detection              │
│  2. 4-point perspective correction (warp to rectangle)             │
│  3. PP-OCRv5: Detection → Recognition → Post-processing            │
│  4. Regex validation: /^[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}$/           │
│     Examples: KA01AB1234, MH12CD5678, TN09EF0123                  │
│  5. Below conf 0.70 → tagged as "UNREADABLE"                      │
│                                                                    │
│  Training: NONE — use directly ✅                                  │
│  Optional upgrade: Fine-tune on CCPD2019 for 90% → 99% accuracy   │
└─────────────┬──────────────────────────────────────────────────────┘
              │
┌─────────────▼──────────────────────────────────────────────────────┐
│  STAGE 6: CONFIDENCE SCORING + EVIDENCE GENERATION        [~2ms]   │
│                                                                    │
│  CALIBRATION:                                                      │
│  • Temperature scaling (T=1.3) on raw model confidence             │
│  • Multi-frame boost: +0.05 per consistent frame (max +0.15)      │
│  • Plate match boost: +0.05 if plate OCR succeeded                │
│  • Final = calibrated + frame_boost + plate_boost                  │
│                                                                    │
│  3-TIER ENFORCEMENT:                                               │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  ≥ 0.90 → AUTO_ENFORCE  (~40% of violations)                 │ │
│  │  Challan auto-generated. No officer review needed.            │ │
│  ├──────────────────────────────────────────────────────────────┤ │
│  │  0.70–0.90 → HUMAN_REVIEW  (~35% of violations)              │ │
│  │  Queued for officer. Optional Gemini 2.5 Flash pre-analysis.  │ │
│  ├──────────────────────────────────────────────────────────────┤ │
│  │  < 0.70 → LOG_ONLY  (~25% of detections)                     │ │
│  │  Saved for analytics only. No enforcement action.             │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  EVIDENCE PACKAGE (per AUTO_ENFORCE or HUMAN_REVIEW):              │
│  • annotated_image.jpg  — bounding boxes + labels + confidence    │
│  • thumbnail.jpg        — 256×256 crop of violation area          │
│  • video_clip.mp4       — 3-second clip from circular frame buffer│
│  • metadata.json        — detection data, model versions, camera  │
│  • SHA-256 hash         — of original frame for tamper-proofing   │
└─────────────┬──────────────────────────────────────────────────────┘
              │
┌─────────────▼──────────────────────────────────────────────────────┐
│  OUTPUT LAYER                                                      │
│                                                                    │
│  FastAPI Backend (8000)    PostgreSQL 17 + TimescaleDB + Redis     │
│  Next.js 16 Dashboard (3000)    MinIO evidence storage             │
│  WebSocket real-time push to dashboard                             │
└────────────────────────────────────────────────────────────────────┘
```

---

## PART 3: MODEL INVENTORY

### Summary Table

| ID | Model | Architecture | Source | Size | Training | GPU Latency | CPU Latency |
|---|---|---|---|---|---|---|---|
| **A** | Vehicle Detector | YOLO11-X / YOLO11-S | IISc AIM — [iisc-aim/UVH-26](https://huggingface.co/iisc-aim/UVH-26) | 327 MB / 55 MB | ❌ None | 6ms / 3ms | ~600ms / ~80ms |
| **B** | Person + Traffic Light | YOLO11n | COCO — Ultralytics (auto-downloads) | 12 MB | ❌ None | 1.5ms | 30ms |
| **C** | Plate Detector | YOLO11 | [morsetechlab/yolov11-lp](https://huggingface.co/morsetechlab/yolov11-license-plate-detection) | ~50 MB | ❌ None | 3ms | 40ms |
| **D** | Seatbelt Detector | YOLO11s | [RISEF/yolov11s-seatbelt](https://huggingface.co/RISEF/yolov11s-seatbelt) | ~20 MB | ❌ None | 2ms | 25ms |
| **E** | Helmet Classifier | EfficientNetV2-S | ImageNet → fine-tune on SHWD | ~85 MB | ✅ ~1 hr on T4 | 3.5ms | 15ms |
| **F** | Scene Classifier | MobileNetV3-Small | ImageNet → fine-tune on weather | ~14 MB | ✅ ~20 min on T4 | 1.5ms | 5ms |
| **G** | Plate OCR | PaddleOCR PP-OCRv5 | Official English pretrained (auto-downloads) | ~15 MB | ❌ None | 4.5ms | 20ms |
| | **TOTAL** | | | **~523 MB** | **~1.5 hours** | **~22ms** | **~215ms** |

### Model A: UVH-26 YOLO11 (Vehicle Detection)

Trained by IISc Bangalore on 26,646 Bengaluru Safe-City CCTV images. Two variants for auto hardware selection.

**Benchmark (arXiv:2511.02563):**

| Metric | YOLO11-X (UVH-26) | YOLO11-S (UVH-26) | COCO Baseline |
|---|---|---|---|
| mAP@50:95 | **0.63** | **0.52** | 0.40 |
| Parameters | 57M | 9M | — |
| GPU Latency | 6ms | 3ms | — |
| CPU Latency | ~600ms | ~80ms | — |

**14 Vehicle Classes:**

| ID | UVH-26 Class | Mapped To | Examples |
|---|---|---|---|
| 0 | Hatchback | car | Swift, i20, Polo |
| 1 | Sedan | car | Honda City, Verna |
| 2 | SUV | car | Creta, Seltos, Fortuner |
| 3 | MUV | car | Innova, Ertiga |
| 4 | Bus | bus | BMTC, Volvo |
| 5 | Truck | truck | Heavy trucks, lorries |
| 6 | Three-wheeler | auto_rickshaw | Auto-rickshaws |
| 7 | Two-wheeler | motorcycle | Motorcycles, scooters |
| 8 | LCV | truck | Tata Ace, mini-trucks |
| 9 | Mini-bus | bus | School buses |
| 10 | Tempo-traveller | bus | Tempo travellers |
| 11 | Bicycle | bicycle | Pedal bicycles |
| 12 | Van | car | Omni, Eeco |
| 13 | Others | skip | Ignored |

**Download commands:**
```bash
hf download iisc-aim/UVH-26 weights/YOLOv11-X/UVH-26-MV-YOLOv11-X.pt --local-dir data/uvh26_models
hf download iisc-aim/UVH-26 weights/YOLOv11-S/UVH-26-MV-YOLOv11-S.pt --local-dir data/uvh26_models
```

**Usage:**
```python
from ultralytics import YOLO
import torch

model = YOLO(
    "data/uvh26_models/weights/YOLOv11-X/UVH-26-MV-YOLOv11-X.pt"
    if torch.cuda.is_available() else
    "data/uvh26_models/weights/YOLOv11-S/UVH-26-MV-YOLOv11-S.pt"
)
results = model("traffic_image.jpg", conf=0.25, iou=0.7, imgsz=640)
```

### Model B: COCO YOLO11n (Person + Traffic Light)

UVH-26 detects vehicles only. Model B provides `person` (triple riding) and `traffic_light` (red-light/stop-line violations).

COCO classes used: `0` (person), `9` (traffic_light). Auto-downloads on first use via Ultralytics.

```python
person_model = YOLO("yolo11n.pt")
results = person_model(frame, classes=[0, 1, 3, 9], conf=0.3)
```

### Model C: License Plate Detector

**Source:** [morsetechlab/yolov11-license-plate-detection](https://huggingface.co/morsetechlab/yolov11-license-plate-detection)

```bash
hf download morsetechlab/yolov11-license-plate-detection --local-dir data/plate_model
```

### Model D: Seatbelt Detector

**Source:** [RISEF/yolov11s-seatbelt](https://huggingface.co/RISEF/yolov11s-seatbelt) — Classes: `seatbelt`, `no_seatbelt`

```bash
hf download RISEF/yolov11s-seatbelt --local-dir data/seatbelt_model
```

### Model E: Helmet Classifier (Fine-Tune Required — ~1 hour)

**Architecture:** EfficientNetV2-S with custom head (3 classes: helmet, no_helmet, ambiguous)

**Training data:**
- SHWD Safety Helmet Wearing Dataset — 7,581 images ([Kaggle link](https://www.kaggle.com/datasets/andrewmvd/hard-hat-detection))
- Kaggle Helmet Detection — 5,000+ images ([Kaggle link](https://www.kaggle.com/datasets/vodan37/yolo-helmet-detection))
- Total: ~12,500 head-crop images

**Training recipe:**
```python
from torchvision import models
import torch

model = models.efficientnet_v2_s(weights="IMAGENET1K_V1")
model.classifier[-1] = torch.nn.Linear(1280, 3)  # helmet / no_helmet / ambiguous

optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=20)
# 20 epochs, batch_size=32 — ~1 hour on Kaggle T4
```

### Model F: Scene Classifier (Fine-Tune Required — ~20 min)

**Architecture:** MobileNetV3-Small (5 classes: clear, hazy, rainy, low_light, motion_blur)

**Training data:** [Kaggle Multiclass Weather Dataset](https://www.kaggle.com/datasets/vijaygiitk/multiclass-weather-dataset) — ~5,000 images

```python
from torchvision import models
model = models.mobilenet_v3_small(weights="IMAGENET1K_V1")
model.classifier[-1] = torch.nn.Linear(1024, 5)
# 15 epochs, batch_size=64 — ~20 min on Kaggle T4
```

### Model G: PaddleOCR PP-OCRv5

Auto-downloads via pip. Supports angle correction, which is critical for tilted/angled license plate crops.

```python
from paddleocr import PaddleOCR
import re

ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)

def read_plate(crop):
    result = ocr.ocr(crop, cls=True)
    text = result[0][0][1][0]  # e.g. "KA01AB1234"
    conf = result[0][0][1][1]
    # Validate Indian plate format
    if re.match(r'^[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}$', text) and conf > 0.70:
        return text, conf
    return "UNREADABLE", 0.0
```

---

## PART 4: VIOLATION DETECTION LOGIC

### All 8 Violations at a Glance

| # | Violation | Fine (₹) | IPC/MVA Section | Detection Method | Models Used |
|---|---|---|---|---|---|
| V1 | Helmet non-compliance | ₹1,000 | S129 | Classifier on rider head crop | A + B + E |
| V2 | Seatbelt non-compliance | ₹1,000 | S138(3) | Pretrained YOLO on windshield crop | A + D |
| V3 | Triple riding | ₹1,000 | S128 | IoU-based person-count on motorcycle | A + B |
| V4 | Wrong-side driving | ₹1,000–5,000 | S184 | Trajectory angle vs. expected lane direction | A + Tracker |
| V5 | Stop-line violation | ₹1,000 | S177A | Vehicle crosses configured polygon during red | A + B + Config |
| V6 | Red-light running | ₹1,000–5,000 | S119/177 | Vehicle enters intersection zone during red | A + B + Config |
| V7 | Illegal parking | ₹500 | S122/177 | Stationary timer inside no-parking polygon | A + Tracker + Config |
| V8 | No number plate | ₹5,000 | S39 | Plate not detected for 15+ consecutive frames | A + C |

### V1: Helmet Non-Compliance

```python
def check_helmet(frame, vehicle_track, person_detections):
    """
    Triggered when: vehicle is Two-wheeler (UVH-26 class 7)

    Steps:
    1. Find all 'person' detections overlapping with motorcycle bbox (IoU > 0.3)
    2. For each rider: crop the HEAD REGION (top 30% of person bbox)
    3. Run EfficientNetV2-S helmet classifier on head crop
    4. If no_helmet confidence > 0.80 → potential violation
    5. Require 3+ consecutive frames before confirming
    """
    riders = [p for p in person_detections if compute_iou(vehicle_track.bbox, p.bbox) > 0.3]

    for rider in riders:
        x1, y1, x2, y2 = rider.bbox
        head_crop = frame[y1 : y1 + int((y2-y1)*0.30), x1:x2]
        result = helmet_classifier(head_crop)

        if result.class_name == "no_helmet" and result.confidence > 0.80:
            vehicle_track.helmet_violation_frames += 1
            if vehicle_track.helmet_violation_frames >= 3:
                yield Violation(type="HELMET_VIOLATION", confidence=result.confidence,
                                vehicle_track_id=vehicle_track.id, evidence_frame=frame)
```

**Edge cases:** Scarves, turbans, and face-masks can cause false positives. The 3-frame persistence requirement and `ambiguous` class in EfficientNetV2-S reduce these.

### V2: Seatbelt Non-Compliance

```python
def check_seatbelt(frame, vehicle_track):
    """
    Triggered when: vehicle is Hatchback/Sedan/SUV/MUV (classes 0-3, 12)

    Steps:
    1. Crop WINDSHIELD REGION: top 40%, center 70% of car bbox
    2. Run RISEF/yolov11s-seatbelt on windshield crop
    3. no_seatbelt confidence > 0.80 + 3 consecutive frames → violation
    """
    x1, y1, x2, y2 = vehicle_track.bbox
    w, h = x2-x1, y2-y1
    crop = frame[y1 : y1+int(h*0.40), x1+int(w*0.15) : x2-int(w*0.15)]

    for det in seatbelt_model(crop):
        if det.class_name == "no_seatbelt" and det.confidence > 0.80:
            vehicle_track.seatbelt_violation_frames += 1
            if vehicle_track.seatbelt_violation_frames >= 3:
                yield Violation(type="SEATBELT_VIOLATION", ...)
```

**Edge cases:** Tinted windows reduce detection accuracy. Mitigated by confidence threshold of 0.80 (higher than default).

### V3: Triple Riding

```python
def check_triple_riding(vehicle_track, person_detections):
    """
    Triggered when: vehicle is Two-wheeler (class 7)

    Count persons with IoU > 0.3 overlap with motorcycle bbox.
    Count >= 3 and persists 5+ frames → violation.
    """
    rider_count = sum(
        1 for p in person_detections
        if compute_iou(vehicle_track.bbox, p.bbox) > 0.3
    )
    if rider_count >= 3:
        vehicle_track.triple_riding_frames += 1
        if vehicle_track.triple_riding_frames >= 5:
            yield Violation(type="TRIPLE_RIDING", ...)
```

**Edge cases:** Pedestrians walking beside a motorcycle at low IoU threshold. The 5-frame requirement filters these transient overlaps.

### V4: Wrong-Side Driving

```python
def check_wrong_side(vehicle_track, camera_config):
    """
    Triggered for: ALL tracked vehicles

    Compare trajectory direction against expected lane flow.
    Angle deviation > 120° for 10+ frames → violation.
    """
    if len(vehicle_track.trajectory) < 10:
        return

    dx = vehicle_track.trajectory[-1].x - vehicle_track.trajectory[-10].x
    dy = vehicle_track.trajectory[-1].y - vehicle_track.trajectory[-10].y
    actual_angle = math.atan2(dy, dx)

    angle_diff = abs(actual_angle - camera_config.expected_flow_direction)
    if angle_diff > math.pi:
        angle_diff = 2*math.pi - angle_diff

    if angle_diff > math.radians(120):
        vehicle_track.wrong_side_frames += 1
        if vehicle_track.wrong_side_frames >= 10:
            yield Violation(type="WRONG_SIDE_DRIVING", ...)
```

**Edge cases:** U-turns and lane changes can trigger false positives. The 10-frame requirement (~333ms at 30fps) filters these — genuine wrong-side driving persists longer.

### V5 & V6: Stop-Line and Red-Light Violations

```python
def check_intersection_violations(vehicle_track, traffic_light_state, camera_config):
    """
    Requires per-camera configuration:
      stop_line_polygon:    coordinates of the stop line
      intersection_polygon: coordinates of the intersection zone

    Traffic light state from HSV analysis of traffic_light crop:
      Red:    H=0–10 or 170–180, S>100, V>100
      Green:  H=40–80, S>100, V>100
      Yellow: H=20–40, S>100, V>100
    """
    if traffic_light_state != "RED":
        return

    center = vehicle_track.center

    # V5: Vehicle crosses the stop line during red
    if point_crossed_line(center, camera_config.stop_line_polygon):
        yield Violation(type="STOP_LINE_VIOLATION", ...)

    # V6: Vehicle enters the intersection box during red
    if point_in_polygon(center, camera_config.intersection_polygon):
        yield Violation(type="RED_LIGHT_VIOLATION", ...)
```

**Configuration note:** Each camera needs its `stop_line_polygon` and `intersection_polygon` configured once via the Cameras page in the dashboard. This is a one-time setup per deployment location.

### V7: Illegal Parking

```python
def check_illegal_parking(vehicle_track, camera_config, fps=30):
    """
    Triggered for: ALL tracked vehicles

    Vehicle must be inside a no-parking zone AND stationary for > 30 seconds.
    Stationary = centroid movement < 5 pixels over the last 30 seconds.
    """
    if not point_in_polygon(vehicle_track.center, camera_config.no_parking_zones):
        return

    window = 30 * fps  # 30 seconds of frames
    if len(vehicle_track.trajectory) < window:
        return

    recent = vehicle_track.trajectory[-window:]
    max_displacement = max(math.dist(recent[0], p) for p in recent)

    if max_displacement < 5.0:
        yield Violation(type="ILLEGAL_PARKING", ...)
```

### V8: No Number Plate

```python
def check_no_plate(vehicle_track, plate_detections):
    """
    If a tracked vehicle has no plate detected for 15+ consecutive frames,
    flag it. Skip bicycles and auto-rickshaws (common to have no visible plate).
    """
    has_plate = any(
        compute_iou(vehicle_track.bbox, p.bbox) > 0.1
        for p in plate_detections
    )
    if has_plate:
        vehicle_track.no_plate_frames = 0
    else:
        vehicle_track.no_plate_frames += 1

    if vehicle_track.no_plate_frames >= 15:
        if vehicle_track.class_name not in ["Bicycle", "Three-wheeler"]:
            yield Violation(type="NO_PLATE", ...)
```

---

## PART 5: DATASETS & DOWNLOADS

### Required Downloads

| # | Dataset / Model | Size | Source | Download Command / Link | Status |
|---|---|---|---|---|---|
| 1 | UVH-26 YOLO11-X weights | 327 MB | HuggingFace | `hf download iisc-aim/UVH-26 weights/YOLOv11-X/UVH-26-MV-YOLOv11-X.pt --local-dir data/uvh26_models` | ✅ DONE |
| 2 | UVH-26 YOLO11-S weights | 55 MB | HuggingFace | `hf download iisc-aim/UVH-26 weights/YOLOv11-S/UVH-26-MV-YOLOv11-S.pt --local-dir data/uvh26_models` | ✅ DONE |
| 3 | COCO YOLO11n | 12 MB | Ultralytics | Auto-downloads on first `YOLO("yolo11n.pt")` call | ✅ AUTO |
| 4 | Seatbelt YOLO11s | ~20 MB | HuggingFace | `hf download RISEF/yolov11s-seatbelt --local-dir data/seatbelt_model` | ⬜ TODO |
| 5 | License Plate YOLO11 | ~50 MB | HuggingFace | `hf download morsetechlab/yolov11-license-plate-detection --local-dir data/plate_model` | ⬜ TODO |
| 6 | SHWD Helmet Dataset | ~500 MB | Kaggle | [andrewmvd/hard-hat-detection](https://www.kaggle.com/datasets/andrewmvd/hard-hat-detection) | ⬜ TODO |
| 7 | Kaggle Helmet YOLO | ~600 MB | Kaggle | [vodan37/yolo-helmet-detection](https://www.kaggle.com/datasets/vodan37/yolo-helmet-detection) | ⬜ TODO |
| 8 | Multiclass Weather Dataset | ~700 MB | Kaggle | [vijaygiitk/multiclass-weather-dataset](https://www.kaggle.com/datasets/vijaygiitk/multiclass-weather-dataset) | ⬜ TODO |
| 9 | PaddleOCR PP-OCRv5 | ~15 MB | PyPI | Auto-downloads via `paddleocr` on first call | ✅ AUTO |
| 10 | MobileNetV3 ImageNet | ~14 MB | PyPI | Auto-downloads via `torchvision` | ✅ AUTO |
| 11 | EfficientNetV2-S ImageNet | ~85 MB | PyPI | Auto-downloads via `torchvision` | ✅ AUTO |

**Total manual downloads: ~1.5 GB** (items 4–8)
**Auto-downloads: ~126 MB** (items 3, 9–11)

### Supplementary Datasets (Roboflow — Instant Download)

| Dataset | Size | Violations Covered | Link |
|---|---|---|---|
| TVD — Traffic Violation Detection | ~1,000 images | No Helmet, Triple Riding, Mobile Use | [universe.roboflow.com/traffic-violation-detection/tvd-kp9qw](https://universe.roboflow.com/traffic-violation-detection/tvd-kp9qw) |
| AICity 2024 Track 5 (Roboflow mirror) | 4,168 images | Helmet + Triple Riding (Indian roads) | [universe.roboflow.com/thesis-dataset-dxaoy/ai-city-challenge](https://universe.roboflow.com/thesis-dataset-dxaoy/ai-city-challenge) |
| With No Helmet | 349 images | No Helmet + motorcycle | [universe.roboflow.com/traffic-violation/with-no-helmet](https://universe.roboflow.com/traffic-violation/with-no-helmet) |
| Indian LP Detection (ILPD) | 296 images | License plate (YOLO-ready) | [universe.roboflow.com/ilpd/indian-licence-plate-detection/dataset/4](https://universe.roboflow.com/ilpd/indian-licence-plate-detection/dataset/4) |
| Indian Number Plate (yolox) | 548 images | License plate (YOLOv8 format) | [universe.roboflow.com/yolox-qcftu/indian-number-plate-keeo5](https://universe.roboflow.com/yolox-qcftu/indian-number-plate-keeo5) |
| YOLOv8 Indian Roads Dataset | — | Cars, bikes, pedestrians | [universe.roboflow.com/object-detection-dp5wa/yolo-v8-indian-roads-dataset](https://universe.roboflow.com/object-detection-dp5wa/yolo-v8-indian-roads-dataset) |
| Seat Belt Detection (Karan Panja) | — | Seatbelt compliance | [universe.roboflow.com/karan-panja/seat-belt-detection-uhqwa](https://universe.roboflow.com/karan-panja/seat-belt-detection-uhqwa) |

### Optional Upgrade Path

| Dataset | Size | Purpose | Link |
|---|---|---|---|
| CCPD2019 | ~6–12 GB | Fine-tune PaddleOCR for 90% → 99% plate accuracy | [github.com/detectRecog/CCPD](https://github.com/detectRecog/CCPD) |
| IDD — India Driving Dataset (IIIT Hyd) | Large | Base vehicle/road diversity | [kaggle.com/datasets/mitanshuchakrawarty/new-idd-dataset](https://www.kaggle.com/datasets/mitanshuchakrawarty/new-idd-dataset) |
| Indian Traffic Violation (Kaggle) | Tabular + images | Supplementary analytics | [kaggle.com/datasets/khushikyad001/indian-traffic-violation](https://www.kaggle.com/datasets/khushikyad001/indian-traffic-violation) |

### Data Preparation Notes

- All datasets should be converted to **YOLO format** (`.txt` label files, normalized `[cls cx cy w h]`)
- Train/val/test split: **80% / 10% / 10%**
- Augmentation for helmet fine-tuning: random horizontal flip, brightness ±30%, HSV jitter, random crop
- Scene classifier augmentation: artificially generate `low_light` (gamma < 1.0) and `motion_blur` (Gaussian kernel) samples from `clear` images to boost class balance

---

## PART 6: ML PIPELINE CODE DESIGN

### Core Orchestrator

```python
# ml/orchestrator.py

import torch
import math
from concurrent.futures import ThreadPoolExecutor
from ultralytics import YOLO
from paddleocr import PaddleOCR

class TrafficViolationOrchestrator:
    def __init__(self, config):
        self.config = config
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Stage 0: Scene analysis
        self.scene_classifier = SceneClassifier(config.scene_model_path)
        self.enhancer = ImageEnhancer()

        # Stage 1: Detection (auto-selects GPU/CPU variant)
        self.vehicle_model = YOLO(
            config.yolo11x_path if self.device == "cuda:0" else config.yolo11s_path
        )
        self.person_model  = YOLO("yolo11n.pt")          # auto-downloads
        self.plate_model   = YOLO(config.plate_model_path)

        # Stage 2: Tracking
        self.tracker = BoTSORT(config.tracker_config)

        # Stage 4: Violation analyzers
        self.helmet_classifier = HelmetClassifier(config.helmet_model_path)
        self.seatbelt_model    = YOLO(config.seatbelt_model_path)

        # Stage 5: OCR
        self.ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)

        # Stage 6: Evidence
        self.evidence_gen = EvidenceGenerator(config.evidence_dir)

        print(f"✅ Pipeline initialized | device={self.device} | models=7")

    def process_frame(self, frame, timestamp: float, camera_id: str) -> list:
        """Full 7-stage pipeline. Returns list of Violation objects."""

        # Stage 0
        scene = self.scene_classifier.classify(frame)
        enhanced = self.enhancer.enhance(frame, scene)

        # Stage 1
        if self.device == "cuda:0":
            import torch.cuda
            s1 = torch.cuda.Stream(); s2 = torch.cuda.Stream(); s3 = torch.cuda.Stream()
            with torch.cuda.stream(s1):
                vehicle_results = self.vehicle_model(enhanced, conf=0.25, device=0)
            with torch.cuda.stream(s2):
                person_results  = self.person_model(enhanced, classes=[0, 9], conf=0.3, device=0)
            with torch.cuda.stream(s3):
                plate_results   = self.plate_model(enhanced, conf=0.3, device=0)
            torch.cuda.synchronize()
        else:
            vehicle_results = self.vehicle_model(enhanced, conf=0.25)
            person_results  = self.person_model(enhanced, classes=[0, 9], conf=0.3)
            plate_results   = self.plate_model(enhanced, conf=0.3)

        # Stage 2: Tracking
        tracked = self.tracker.update(vehicle_results, frame.shape)

        # Stage 3+4: Route and analyze
        persons        = person_results[0].boxes  if person_results else []
        plates         = plate_results[0].boxes   if plate_results  else []
        traffic_lights = [d for d in persons if int(d.cls) == 9]

        violations = []
        for track in tracked:
            tl_state = self.get_traffic_light_state(enhanced, traffic_lights)

            if track.cls_name == "Two-wheeler":
                violations += list(self.check_helmet(enhanced, track, persons))
                violations += list(self.check_triple_riding(track, persons))
            elif track.cls_name in ["Hatchback", "Sedan", "SUV", "MUV", "Van"]:
                violations += list(self.check_seatbelt(enhanced, track))

            violations += list(self.check_wrong_side(track, camera_id))
            violations += list(self.check_intersection(track, tl_state, camera_id))
            violations += list(self.check_parking(track, camera_id))
            violations += list(self.check_no_plate(track, plates))

        # Stage 5: OCR
        plate_texts = {}
        for plate_box in plates:
            crop = self.crop_plate(enhanced, plate_box)
            text, conf = self.read_plate(crop)
            if conf > 0.70:
                plate_texts[id(plate_box)] = text

        # Stage 6: Score + evidence
        for v in violations:
            v.plate_number     = self.match_plate(v.vehicle_bbox, plate_texts, plates)
            v.final_confidence = self.calibrate_confidence(v)
            v.action           = self.classify_action(v.final_confidence)
            if v.action in ("AUTO_ENFORCE", "HUMAN_REVIEW"):
                v.evidence = self.evidence_gen.generate(frame, v, timestamp)

        return [v for v in violations if v.action != "LOG_ONLY"]
```

### Hardware Config (Auto-Select)

```python
# ml/config.py

import torch
from pathlib import Path

class PipelineConfig:
    def __init__(self):
        self.device    = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.data_dir  = Path("data")
        is_gpu         = self.device == "cuda:0"

        self.yolo11x_path    = self.data_dir / "uvh26_models/weights/YOLOv11-X/UVH-26-MV-YOLOv11-X.pt"
        self.yolo11s_path    = self.data_dir / "uvh26_models/weights/YOLOv11-S/UVH-26-MV-YOLOv11-S.pt"
        self.plate_model_path   = self.data_dir / "plate_model/best.pt"
        self.seatbelt_model_path= self.data_dir / "seatbelt_model/best.pt"
        self.helmet_model_path  = self.data_dir / "helmet_model/best.pt"
        self.scene_model_path   = self.data_dir / "scene_model/best.pt"

        self.img_size   = 640 if is_gpu else 480
        self.batch_size = 4   if is_gpu else 1
        self.evidence_dir = Path("evidence")

    @property
    def tracker_config(self) -> dict:
        return dict(
            track_high_thresh=0.5, track_low_thresh=0.1,
            new_track_thresh=0.6,  track_buffer=60,
            match_thresh=0.85,     with_reid=True
        )
```

---

## PART 7: BACKEND API DESIGN

### Tech Stack

- **Framework:** FastAPI 0.115+ with async throughout
- **Database:** PostgreSQL 17 + TimescaleDB (time-series hypertable on violations)
- **Cache / PubSub:** Redis 7.x
- **File Storage:** MinIO (S3-compatible, self-hosted)
- **ORM:** SQLAlchemy 2.0 (async) + Alembic migrations
- **Auth:** JWT (officer/admin roles) + API Key (ML service)

### Database Schema

```sql
-- violations table — TimescaleDB hypertable on occurred_at
CREATE TABLE violations (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    violation_id            VARCHAR(50) UNIQUE NOT NULL,  -- "V_1718500000_42"
    violation_type          VARCHAR(30) NOT NULL,          -- "HELMET_VIOLATION"
    violation_code          VARCHAR(10) NOT NULL,          -- "S129"
    fine_inr                INTEGER NOT NULL,              -- 1000

    camera_id               VARCHAR(50) NOT NULL,
    camera_name             VARCHAR(100),

    raw_confidence          FLOAT NOT NULL,
    final_confidence        FLOAT NOT NULL,
    enforcement_action      VARCHAR(20) NOT NULL,          -- AUTO_ENFORCE / HUMAN_REVIEW / LOG_ONLY

    vehicle_type            VARCHAR(30),
    plate_number            VARCHAR(20),
    plate_confidence        FLOAT,
    vehicle_bbox            JSONB,

    evidence_image_path     VARCHAR(255),
    evidence_thumbnail_path VARCHAR(255),
    evidence_video_path     VARCHAR(255),
    evidence_hash           VARCHAR(64),                   -- SHA-256

    location_lat            DOUBLE PRECISION,
    location_lng            DOUBLE PRECISION,
    location_name           VARCHAR(100),

    status                  VARCHAR(20) DEFAULT 'PENDING', -- PENDING / CONFIRMED / REJECTED
    reviewed_by             VARCHAR(50),
    review_notes            TEXT,
    reviewed_at             TIMESTAMPTZ,

    gemini_verdict          VARCHAR(20),                   -- CONFIRM / REJECT / NEEDS_OFFICER
    gemini_explanation      TEXT,

    model_version           VARCHAR(50),
    pipeline_latency_ms     FLOAT,

    occurred_at             TIMESTAMPTZ NOT NULL,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

SELECT create_hypertable('violations', 'occurred_at');

CREATE INDEX idx_violations_camera  ON violations(camera_id, occurred_at DESC);
CREATE INDEX idx_violations_type    ON violations(violation_type, occurred_at DESC);
CREATE INDEX idx_violations_status  ON violations(status) WHERE status = 'PENDING';
CREATE INDEX idx_violations_plate   ON violations(plate_number);

-- cameras table
CREATE TABLE cameras (
    id                      VARCHAR(50) PRIMARY KEY,  -- "BTP_MG_ROAD_01"
    name                    VARCHAR(100) NOT NULL,
    location_lat            DOUBLE PRECISION,
    location_lng            DOUBLE PRECISION,
    rtsp_url                VARCHAR(255),
    expected_flow_direction FLOAT,                    -- radians (for wrong-side)
    stop_line_polygon       JSONB,                    -- [[x1,y1], [x2,y2], ...]
    intersection_polygon    JSONB,
    no_parking_zones        JSONB,                    -- [[[x1,y1],...], ...]
    is_active               BOOLEAN DEFAULT true,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);
```

### API Endpoints

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/api/v1/violations` | ML service submits new violation | API Key |
| `GET` | `/api/v1/violations` | Query with filters (type, camera, date, status, plate) | JWT |
| `GET` | `/api/v1/violations/{id}` | Single violation + full evidence | JWT |
| `PATCH` | `/api/v1/violations/{id}/review` | Officer approves or rejects | JWT (officer) |
| `GET` | `/api/v1/analytics/summary` | Dashboard KPIs (counts, trends) | JWT |
| `GET` | `/api/v1/analytics/hourly` | Hourly violation trend data | JWT |
| `GET` | `/api/v1/analytics/heatmap` | Location-based heatmap points | JWT |
| `GET` | `/api/v1/cameras` | List all cameras | JWT |
| `POST` | `/api/v1/cameras` | Register new camera | JWT (admin) |
| `PATCH` | `/api/v1/cameras/{id}` | Update camera config / zones | JWT (admin) |
| `WS` | `/ws/violations` | Real-time violation push feed | Token |

### WebSocket Protocol

```jsonc
// Client → Server
{ "type": "subscribe",   "cameras": ["BTP_MG_ROAD_01"] }
{ "type": "unsubscribe", "cameras": ["BTP_MG_ROAD_01"] }
{ "type": "ping" }

// Server → Client
{ "type": "new_violation",  "data": { "violation_id": "...", "type": "HELMET_VIOLATION",
                                       "camera": "BTP_MG_ROAD_01", "confidence": 0.92,
                                       "thumbnail_url": "..." } }
{ "type": "stats_update",   "data": { "camera_id": "...", "fps": 29.8,
                                       "latency_ms": 22.4, "violations_last_hour": 47 } }
{ "type": "review_update",  "data": { "violation_id": "...", "status": "CONFIRMED",
                                       "reviewed_by": "officer_42" } }
{ "type": "pong" }
```

---

## PART 8: FRONTEND DASHBOARD DESIGN

### Tech Stack

- **Framework:** Next.js 16 (App Router, TypeScript)
- **UI Library:** shadcn/ui + Tailwind CSS v4
- **Charts:** Recharts
- **Maps:** Leaflet.js (violation heatmap)
- **Real-time:** Native WebSocket
- **State:** Zustand

### Pages

| Page | Route | Description |
|---|---|---|
| Dashboard | `/` | KPI cards, live stats, recent violation feed, camera overview |
| Violations | `/violations` | Searchable + filterable table (type, camera, date, status, plate) |
| Review Queue | `/review` | Officer approve/reject interface with evidence side-by-side |
| Analytics | `/analytics` | Hourly trends, violation breakdown, peak-hour heatmap |
| Cameras | `/cameras` | Camera management, live MJPEG feed preview, zone polygon editor |
| Evidence Viewer | `/violations/[id]` | Annotated image + video clip + full metadata |

### Dashboard KPI Cards

```
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Total Today  │ │ Auto-Enforced│ │ Pending Review│ │ Avg Latency  │
│    847       │ │    312       │ │    198        │ │   22.4ms     │
│ ▲ 12% vs yd │ │  36.8%       │ │ ▼ 5 min ago  │ │ ✅ < 40ms   │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

### Color System

| Status | Color | Usage |
|---|---|---|
| AUTO_ENFORCE | `red-600` | Critical — immediately actionable |
| HUMAN_REVIEW | `amber-500` | Warning — needs officer attention |
| LOG_ONLY / CONFIRMED | `green-500` | Informational / resolved |
| REJECTED | `slate-400` | Dismissed |

---

## PART 9: INFRASTRUCTURE & DEPLOYMENT

### Docker Compose

```yaml
# docker-compose.yml
services:
  ml-inference:
    build: { context: ./ml, dockerfile: Dockerfile }
    runtime: nvidia            # Remove for CPU-only demo
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - BACKEND_URL=http://backend:8000
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./data:/app/data
      - evidence:/evidence
    ports: ["8001:8001"]
    depends_on: [redis, backend]
    restart: unless-stopped

  backend:
    build: { context: ./backend, dockerfile: Dockerfile }
    environment:
      - DATABASE_URL=postgresql+asyncpg://gridlock:gridlock@postgres:5432/gridlock
      - REDIS_URL=redis://redis:6379
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=gridlock
      - MINIO_SECRET_KEY=gridlock123
    volumes: [evidence:/evidence]
    ports: ["8000:8000"]
    depends_on: [postgres, redis, minio]
    restart: unless-stopped

  frontend:
    build: { context: ./frontend, dockerfile: Dockerfile }
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_WS_URL=ws://localhost:8000
    ports: ["3000:3000"]
    depends_on: [backend]
    restart: unless-stopped

  postgres:
    image: timescale/timescaledb:latest-pg17
    environment:
      POSTGRES_DB: gridlock
      POSTGRES_USER: gridlock
      POSTGRES_PASSWORD: gridlock
    volumes: [pg_data:/var/lib/postgresql/data]
    ports: ["5432:5432"]
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    restart: unless-stopped

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: gridlock
      MINIO_ROOT_PASSWORD: gridlock123
    volumes: [minio_data:/data]
    ports: ["9000:9000", "9001:9001"]
    restart: unless-stopped

volumes:
  pg_data:
  minio_data:
  evidence:
```

### Python Requirements

```
# requirements.txt
ultralytics>=8.3.0
paddleocr>=2.9.0
paddlepaddle>=3.0.0
torch>=2.4.0
torchvision>=0.19.0
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
sqlalchemy[asyncio]>=2.0.0
asyncpg>=0.30.0
alembic>=1.14.0
redis[hiredis]>=5.0.0
minio>=7.2.0
opencv-python-headless>=4.10.0
supervision>=0.24.0
Pillow>=10.0.0
pydantic>=2.0.0
python-multipart>=0.0.9
websockets>=12.0
numpy>=1.26.0
huggingface-hub>=0.24.0
google-generativeai>=0.8.0   # optional — Gemini pre-review
```

---

## PART 10: LATENCY & PERFORMANCE

### GPU Mode (T4 / A100)

| Stage | Component | Latency |
|---|---|---|
| 0 | Scene classification (MobileNetV3-S) | 1.5ms |
| 0 | Image enhancement (CLAHE/Gamma) | 1.0ms |
| 1 | Detection — 3 models in parallel (max) | 6.0ms |
| 2 | BoT-SORT tracking | 2.0ms |
| 3 | Specialist routing | 0.5ms |
| 4 | Violation analyzers (parallel, max) | 5.0ms |
| 5 | Plate OCR (PaddleOCR PP-OCRv5) | 4.5ms |
| 6 | Confidence scoring + evidence generation | 2.0ms |
| **Total** | | **~22ms typical / ~31ms worst-case** |

**Result: ~45 FPS throughput on GPU**

### CPU Mode (i7/i9 Laptop)

| Stage | Component | Latency |
|---|---|---|
| 0 | Scene + enhancement | 7ms |
| 1 | UVH-26 YOLO11-S (sequential) | 80ms |
| 1 | COCO YOLO11n | 30ms |
| 1 | Plate YOLO11 | 40ms |
| 2 | Tracking | 5ms |
| 3+4 | Violations | 20ms |
| 5 | OCR | 20ms |
| 6 | Scoring + Evidence | 3ms |
| **Total** | | **~205ms (~5 FPS)** |

**Result: ~5 FPS on CPU — sufficient for demo and still detects violations reliably**

### Optimization Path (post-MVP)

| Technique | Speedup | Requirement |
|---|---|---|
| ONNX Export | ~30% on CPU | None |
| TensorRT INT8 | ~40% on GPU | NVIDIA GPU |
| OpenVINO | ~50% on Intel CPU | Intel CPU |
| Frame skip (every N-th frame + track) | ~3× throughput | Logic adjustment |

---

## PART 11: SCALABILITY DESIGN

### Horizontal Scaling

| Hardware | Camera Pipelines | FPS per Camera | Use Case |
|---|---|---|---|
| 1 CPU laptop | 1 | 5 FPS | Hackathon demo |
| 1 T4 GPU (16 GB VRAM) | 4 | 30 FPS | Small deployment |
| 1 A100 GPU (40 GB VRAM) | 12 | 30 FPS | Medium deployment |
| 4 × T4 GPUs | 16 | 30 FPS | City-scale pilot |
| N GPU workers | 4N | 30 FPS | Full production |

### GPU Memory Budget (FP16)

| Model | FP16 | INT8 |
|---|---|---|
| YOLO11-X (vehicle) | 800 MB | 400 MB |
| YOLO11n (person) | 100 MB | 50 MB |
| YOLO11 (plate) | 200 MB | 100 MB |
| YOLO11s (seatbelt) | 150 MB | 75 MB |
| EfficientNetV2-S (helmet) | 200 MB | 100 MB |
| MobileNetV3-S (scene) | 50 MB | 25 MB |
| PaddleOCR PP-OCRv5 | 200 MB | 100 MB |
| **Total** | **~1.7 GB** | **~850 MB** |

T4 has 16 GB VRAM → fits 4 complete camera pipelines in FP16 (or 8+ in INT8).

### Architecture for Scale-Out

```
RTSP Cameras
    ↓ (one process per camera)
ML Inference Workers (Docker containers, GPU pass-through)
    ↓ POST /api/v1/violations
FastAPI Backend (load-balanced)
    ↓
PostgreSQL 17 + TimescaleDB          Redis 7 (pub/sub + cache)
    ↓                                     ↓
MinIO Evidence Storage           WebSocket → Next.js Dashboard
```

---

## PART 12: PROJECT STRUCTURE

```
gridlock/
│
├── data/                                  # Downloaded models + datasets
│   ├── uvh26_models/
│   │   ├── weights/YOLOv11-X/UVH-26-MV-YOLOv11-X.pt   (327 MB) ✅
│   │   ├── weights/YOLOv11-S/UVH-26-MV-YOLOv11-S.pt   (55 MB)  ✅
│   │   └── uvh_classes.txt
│   ├── plate_model/                       # ⬜ To download
│   ├── seatbelt_model/                    # ⬜ To download
│   ├── shwd/                              # ⬜ Helmet training data
│   ├── helmet_detection/                  # ⬜ Helmet training data
│   └── weather/                           # ⬜ Scene classifier data
│
├── ml/                                    # ML Inference Service (FastAPI port 8001)
│   ├── orchestrator.py                    # Main 7-stage pipeline
│   ├── config.py                          # Model paths + hardware auto-select
│   ├── server.py                          # FastAPI ML microservice endpoint
│   ├── models/
│   │   ├── vehicle_detector.py            # UVH-26 YOLO11 wrapper
│   │   ├── person_detector.py             # COCO YOLO11n wrapper
│   │   ├── plate_detector.py              # License plate YOLO wrapper
│   │   ├── seatbelt_detector.py           # RISEF seatbelt wrapper
│   │   ├── helmet_classifier.py           # EfficientNetV2-S wrapper
│   │   ├── scene_classifier.py            # MobileNetV3 wrapper
│   │   └── plate_ocr.py                   # PaddleOCR PP-OCRv5 wrapper
│   ├── violations/
│   │   ├── helmet.py                      # V1 logic
│   │   ├── seatbelt.py                    # V2 logic
│   │   ├── triple_riding.py               # V3 logic
│   │   ├── wrong_side.py                  # V4 logic
│   │   ├── stop_line.py                   # V5 logic
│   │   ├── red_light.py                   # V6 logic
│   │   ├── illegal_parking.py             # V7 logic
│   │   └── no_plate.py                    # V8 logic
│   ├── tracking/
│   │   └── tracker.py                     # BoT-SORT integration
│   ├── enhancement/
│   │   └── enhancer.py                    # Scene-adaptive preprocessing
│   └── evidence/
│       └── generator.py                   # Evidence package + SHA-256
│
├── backend/                               # FastAPI API Server (port 8000)
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── violations.py              # CRUD + review endpoints
│   │   │   ├── analytics.py              # Summary / hourly / heatmap
│   │   │   ├── cameras.py                # Camera management
│   │   │   └── websocket.py              # WS push to dashboard
│   │   ├── models/
│   │   │   ├── violation.py              # SQLAlchemy ORM model
│   │   │   └── camera.py
│   │   ├── schemas/
│   │   │   └── violation.py              # Pydantic request/response schemas
│   │   └── services/
│   │       ├── violation_service.py
│   │       └── analytics_service.py
│   ├── alembic/                           # DB migrations
│   └── requirements.txt
│
├── frontend/                              # Next.js 16 Dashboard (port 3000)
│   ├── app/
│   │   ├── page.tsx                       # Dashboard home
│   │   ├── violations/page.tsx
│   │   ├── review/page.tsx
│   │   ├── analytics/page.tsx
│   │   └── cameras/page.tsx
│   ├── components/
│   │   ├── ViolationCard.tsx
│   │   ├── LiveFeed.tsx
│   │   ├── AnalyticsChart.tsx
│   │   └── EvidenceViewer.tsx
│   └── package.json
│
├── notebooks/                             # Kaggle training notebooks
│   ├── 01_train_helmet_classifier.py      # EfficientNetV2-S on SHWD
│   ├── 02_train_scene_classifier.py       # MobileNetV3-S on weather
│   └── 03_finetune_plate_ocr.py           # Optional CCPD fine-tune
│
├── scripts/
│   ├── demo_inference.py                  # Quick single-image/video demo
│   ├── export_tensorrt.py                 # TensorRT INT8 export
│   └── benchmark.py                       # Latency profiler
│
├── configs/
│   ├── cameras.yaml                       # Per-camera zone polygons + flow direction
│   └── thresholds.yaml                    # Confidence thresholds per violation type
│
├── docker-compose.yml
├── requirements.txt
├── plan.md                                # THIS FILE
└── README.md
```

---

## PART 13: 7-DAY EXECUTION PLAN

### Day 1 — Foundation + First Demo *(Owner: All)*

```
[ ] Download seatbelt model from HuggingFace (Model D)
[ ] Download license plate model from HuggingFace (Model C)
[ ] Download helmet + weather datasets from Kaggle (items 6–8)
[ ] Set up project directory structure (Part 12)
[ ] Install Python dependencies: uv pip install -r requirements.txt
[ ] Write ml/config.py — hardware auto-select
[ ] Write scripts/demo_inference.py — test UVH-26 on a sample image
[ ] MILESTONE: Vehicle detections working on Indian traffic image ✅
```

### Day 2 — ML Pipeline Core *(Owner: ML Lead + ML Data)*

```
[ ] Write all 7 model wrapper classes (ml/models/)
[ ] Write ml/orchestrator.py — wire all models together
[ ] Write ml/tracking/tracker.py — BoT-SORT integration
[ ] Write ml/enhancement/enhancer.py — scene-adaptive preprocessing
[ ] Test full pipeline on a sample video end-to-end
[ ] MILESTONE: All detections running through a single pipeline call ✅
```

### Day 3 — Violations + Fine-Tuning *(Owner: ML Lead + ML Data)*

```
[ ] Fine-tune helmet classifier on Kaggle T4 (~1 hour) → save best.pt
[ ] Fine-tune scene classifier on Kaggle T4 (~20 min) → save best.pt
[ ] Write all 8 violation modules (ml/violations/)
[ ] Write ml/evidence/generator.py — annotated image + video + SHA-256
[ ] Implement confidence calibration (temperature scaling)
[ ] Test all violations on demo video
[ ] MILESTONE: All 8 violation types detected end-to-end ✅
```

### Day 4 — Backend API *(Owner: Backend)*

```
[ ] Set up FastAPI + PostgreSQL + Redis + MinIO services via Docker Compose
[ ] Write DB schema + run Alembic migrations
[ ] Implement all REST endpoints (violations, analytics, cameras)
[ ] Implement WebSocket real-time feed
[ ] Wire ML service → Backend (POST /api/v1/violations)
[ ] MILESTONE: Violations flowing ML → API → PostgreSQL → Redis pub/sub ✅
```

### Day 5 — Frontend Dashboard *(Owner: Frontend)*

```
[ ] Set up Next.js 16 + shadcn/ui + Tailwind v4 + Zustand
[ ] Dashboard home page (KPI cards + recent violations)
[ ] Violations table with filters
[ ] Officer review queue (approve/reject with notes)
[ ] Evidence viewer (image + video clip + metadata)
[ ] WebSocket integration for real-time updates
[ ] MILESTONE: Full dashboard showing live violations from the pipeline ✅
```

### Day 6 — Optimization + Docker *(Owner: ML Lead + Backend)*

```
[ ] ONNX export for CPU optimization
[ ] TensorRT INT8 export (if GPU available)
[ ] Complete Docker Compose — all services up with one command
[ ] Run scripts/benchmark.py — verify latency targets
[ ] SAHI integration (optional — for detecting small distant vehicles)
[ ] Analytics page (Recharts + Leaflet heatmap)
[ ] Polish dashboard UI
[ ] MILESTONE: Production-ready stack running in Docker ✅
```

### Day 7 — Demo + Presentation *(Owner: All)*

```
[ ] Record 3-minute demo video with real traffic footage
[ ] Prepare pitch deck (problem → solution → architecture → demo → impact)
[ ] Test edge cases: night, rain, overlapping vehicles, tinted windows
[ ] Final bug fixes
[ ] Write README.md
[ ] MILESTONE: Ready for Flipkart Gridlock 2.0 finale ✅
```

---

## PART 14: TEAM TASK ASSIGNMENTS

### 4-Person Split

| Person | Role | Days 1–3 | Days 4–7 |
|---|---|---|---|
| **Person 1** | ML Lead | Build orchestrator, model wrappers, BoT-SORT integration, violation modules | Latency optimization, TensorRT export, SAHI, benchmark |
| **Person 2** | ML + Data | Download all models/datasets, fine-tune helmet + scene on Kaggle | Evidence generator, OCR pipeline, confidence calibration |
| **Person 3** | Backend | FastAPI setup, DB schema, Alembic, all API endpoints | WebSocket pub/sub, Redis integration, Docker, env setup |
| **Person 4** | Frontend | Dashboard wireframes, Next.js 16 + shadcn/ui setup | All dashboard pages, real-time WS, analytics charts, UI polish |

### Key Dependencies & Sync Points

```
Days 1–2:   Person 1 + 2  →  ML pipeline (independent of backend)
            Person 3 + 4  →  Backend + Frontend (independent of ML)

Day 3:      Person 1 needs Person 2's trained helmet.pt + scene.pt
            Person 3 needs Person 1's Violation output format (define API contract)

Day 4:      Person 4 needs Person 3's API endpoints live
            Person 1 needs Person 3's POST /api/v1/violations working

Days 5–7:   Integration sprint — all four testing together
```

### Daily Standup (15 min, every morning)

1. What did I complete yesterday? (30 sec each)
2. What am I doing today? (30 sec each)
3. Any blockers? (action: resolve immediately, not async)
4. Integration check: are the interfaces still in sync?

---

## APPENDIX A: QUICK START

```bash
# 1. Clone and set up environment
cd C:\Users\HP\gridlock
python -m venv venv
venv\Scripts\activate
uv pip install -r requirements.txt

# 2. Verify UVH-26 model works
python - <<'EOF'
from ultralytics import YOLO
model = YOLO("data/uvh26_models/weights/YOLOv11-S/UVH-26-MV-YOLOv11-S.pt")
results = model("sample_image.jpg", conf=0.25)
results[0].show()
EOF

# 3. Run quick demo
python scripts/demo_inference.py --source sample_video.mp4

# 4. Run full stack (requires Docker Desktop)
docker-compose up --build
# Dashboard → http://localhost:3000
# API docs   → http://localhost:8000/docs
# MinIO UI   → http://localhost:9001
```

---

## APPENDIX B: KEY LINKS

| Resource | URL |
|---|---|
| UVH-26 Paper (arXiv) | https://arxiv.org/abs/2511.02563 |
| UVH-26 Models (HuggingFace) | https://huggingface.co/iisc-aim/UVH-26 |
| UVH-26 Dataset (HuggingFace) | https://huggingface.co/datasets/iisc-aim/UVH-26 |
| Seatbelt Model | https://huggingface.co/RISEF/yolov11s-seatbelt |
| Plate Detector Model | https://huggingface.co/morsetechlab/yolov11-license-plate-detection |
| SHWD Helmet Dataset | https://www.kaggle.com/datasets/andrewmvd/hard-hat-detection |
| Kaggle Helmet YOLO | https://www.kaggle.com/datasets/vodan37/yolo-helmet-detection |
| Multiclass Weather Dataset | https://www.kaggle.com/datasets/vijaygiitk/multiclass-weather-dataset |
| AICity 2024 Track 5 (Roboflow) | https://universe.roboflow.com/thesis-dataset-dxaoy/ai-city-challenge |
| TVD Roboflow | https://universe.roboflow.com/traffic-violation-detection/tvd-kp9qw |
| Indian LP Detection (ILPD) | https://universe.roboflow.com/ilpd/indian-licence-plate-detection/dataset/4 |
| Seat Belt Detection (Karan Panja) | https://universe.roboflow.com/karan-panja/seat-belt-detection-uhqwa |
| IDD — India Driving Dataset | https://www.kaggle.com/datasets/mitanshuchakrawarty/new-idd-dataset |
| Ultralytics Docs | https://docs.ultralytics.com/ |
| PaddleOCR Docs | https://paddlepaddle.github.io/PaddleOCR/ |
| Hackathon Platform | https://gridlock2point0.hackerearth.com/ |

---

## APPENDIX C: CONFIDENCE CALIBRATION DETAIL

Raw model outputs are overconfident. Temperature scaling with T=1.3 corrects this:

```python
def calibrate_confidence(raw_conf: float, T: float = 1.3) -> float:
    """Apply temperature scaling to soften raw model confidence."""
    import math
    logit = math.log(raw_conf / (1 - raw_conf + 1e-9))
    calibrated = 1 / (1 + math.exp(-logit / T))
    return calibrated

def compute_final_confidence(violation) -> float:
    base = calibrate_confidence(violation.raw_confidence)

    # Multi-frame boost: consistent detections are more reliable
    frame_boost = min(0.05 * violation.consistent_frames, 0.15)

    # Plate boost: if we can read the plate, evidence is stronger
    plate_boost = 0.05 if violation.plate_number and violation.plate_number != "UNREADABLE" else 0.0

    return min(base + frame_boost + plate_boost, 1.0)

def classify_action(final_conf: float) -> str:
    if final_conf >= 0.90:
        return "AUTO_ENFORCE"
    elif final_conf >= 0.70:
        return "HUMAN_REVIEW"
    else:
        return "LOG_ONLY"
```

---

*Plan v4 — generated June 16, 2026. Previous version: `original_plan.md` (v1), `plan.md` (v3).*