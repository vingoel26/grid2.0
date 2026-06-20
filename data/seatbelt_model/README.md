---
license: agpl-3.0
tags:
  - image-classification
  - driver-monitoring
  - traffic-safety
  - seatbelt
  - yolov11
  - ultralytics
  - onnx
pipeline_tag: image-classification
library_name: ultralytics
---

# YOLOv11s-cls · seatbelt binary classifier

Binary classifier that predicts whether a **driver is wearing a seatbelt**
from a cropped driver / windshield-view RGB image.

Part of the **ktk-studio** traffic-violation analytics stack (DeepStream 9.0 +
Triton + B200).

## Summary

| | |
|---|---|
| Architecture | YOLOv11s-cls (Ultralytics) |
| Input | 224×224 RGB |
| Output | logits over 2 classes: `no_seatbelt`, `seat_belt` |
| Parameters | 5.4 M |
| GFLOPs | 12.0 |
| Weights | `best.pt` (PyTorch, 11 MB) / `best.onnx` (21 MB, opset 19) |
| Val top1 | **100.0 %** at epoch 8 (early-stop after 18) |
| Train epochs | 18 (early-stopped out of 40) |

## Training data

Source: [lavdeep1234/driver-seat-belt-dectection](https://www.kaggle.com/datasets/lavdeep1234/driver-seat-belt-dectection) (Kaggle).
Windshield-view still frames; labels collapsed to binary (`no seatbelt` / `seat_belt`).

| Split | `no_seatbelt` | `seat_belt` | Total |
|---|---|---|---|
| train | 46 | 690 | 736 |
| val (15 % holdout) | 8 | 121 | 129 |
| test | 33 | 366 | 399 |

> The dataset is heavily imbalanced (seat-belt class ~15× more frequent).
> 100 % val accuracy should be interpreted against the small negative class
> size. On out-of-distribution traffic footage, expect lower accuracy; combine
> with driver-ROI detection and a second-tier verifier.

## Usage

### Ultralytics

```python
from ultralytics import YOLO
model = YOLO("best.pt")
r = model("driver_crop.jpg")
print(r[0].probs.top1, r[0].names[r[0].probs.top1])
```

### ONNX Runtime

```python
import cv2, numpy as np, onnxruntime as ort
sess = ort.InferenceSession("best.onnx", providers=["CUDAExecutionProvider"])
img = cv2.cvtColor(cv2.imread("driver_crop.jpg"), cv2.COLOR_BGR2RGB)
img = cv2.resize(img, (224, 224)).astype(np.float32) / 255.0
x = np.ascontiguousarray(img.transpose(2, 0, 1)[None])
logits = sess.run(None, {"images": x})[0][0]
print(["no_seatbelt", "seat_belt"][int(logits.argmax())], float(logits.max()))
```

## Intended use

- Real-time seatbelt violation flagging on road-traffic video after car
  detection + tracking (e.g. via DeepStream TrafficCamNet + NvDCF tracker).
- Run on the top ~50 % crop of a detected car bbox, where the windshield /
  driver sits.

## Out-of-scope / limitations

- Nighttime / tinted-glass / heavy glare scenes under-represented in training.
- Dataset is English/European angle; fine-tune on local data for RU / KZ plates.
- Binary only — does not distinguish passenger vs driver belt.

## License

AGPL-3.0 (inherits Ultralytics YOLOv11 weight license).
