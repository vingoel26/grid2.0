"""Model E — Helmet classifier (EfficientNetV2-S, 3 classes).

Fine-tuned on SHWD + Kaggle helmet data. Operates on a head crop and returns
one of: helmet / no_helmet / ambiguous. Degrades to "ambiguous" (no violation)
when weights are absent.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger("ml.models")

CLASSES = ["helmet", "no_helmet", "ambiguous"]


@dataclass
class ClsResult:
    class_name: str
    confidence: float


class HelmetClassifier:
    def __init__(self, weights: str | Path, device: str = "cpu"):
        self.weights = str(weights)
        self.device = device
        self._model = None
        self._tf = None
        self._tried = False

    @property
    def available(self) -> bool:
        self._ensure_loaded()
        return self._model is not None

    def _ensure_loaded(self) -> None:
        if self._tried:
            return
        self._tried = True
        if not Path(self.weights).exists():
            log.warning("[helmet] weights not found: %s — stub mode", self.weights)
            return
        try:
            import torch
            from torchvision import models, transforms

            net = models.efficientnet_v2_s(weights=None)
            net.classifier[-1] = torch.nn.Linear(1280, len(CLASSES))
            state = torch.load(self.weights, map_location=self.device)
            net.load_state_dict(state.get("model", state) if isinstance(state, dict) else state)
            net.eval().to(self.device)
            self._model = net
            self._tf = transforms.Compose([
                transforms.ToPILImage(),
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ])
            log.info("[helmet] loaded %s", self.weights)
        except Exception as e:  # pragma: no cover
            log.warning("[helmet] load failed (%s) — stub mode", e)
            self._model = None

    def classify(self, head_crop) -> ClsResult:
        self._ensure_loaded()
        if self._model is None or head_crop is None or getattr(head_crop, "size", 0) == 0:
            return ClsResult("ambiguous", 0.0)
        try:
            import torch

            x = self._tf(head_crop).unsqueeze(0).to(self.device)
            with torch.no_grad():
                probs = torch.softmax(self._model(x), dim=1)[0]
            idx = int(probs.argmax())
            return ClsResult(CLASSES[idx], float(probs[idx]))
        except Exception as e:  # pragma: no cover
            log.warning("[helmet] inference error: %s", e)
            return ClsResult("ambiguous", 0.0)

    # alias for orchestrator call style
    __call__ = classify
