"""Model F — Scene/weather classifier (MobileNetV3-Small, 5 classes).

Drives Stage 0 adaptive enhancement. Degrades to "clear" (pass-through) when
weights are absent.
"""
from __future__ import annotations

import logging
from pathlib import Path

log = logging.getLogger("ml.models")

CLASSES = ["clear", "hazy", "rainy", "low_light", "motion_blur"]


class SceneClassifier:
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
            log.warning("[scene] weights not found: %s — defaulting to 'clear'", self.weights)
            return
        try:
            import torch
            from torchvision import models, transforms

            net = models.mobilenet_v3_small(weights=None)
            net.classifier[-1] = torch.nn.Linear(1024, len(CLASSES))
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
            log.info("[scene] loaded %s", self.weights)
        except Exception as e:  # pragma: no cover
            log.warning("[scene] load failed (%s) — defaulting to 'clear'", e)
            self._model = None

    def classify(self, frame) -> str:
        self._ensure_loaded()
        if self._model is None:
            return "clear"
        try:
            import torch

            x = self._tf(frame).unsqueeze(0).to(self.device)
            with torch.no_grad():
                probs = torch.softmax(self._model(x), dim=1)[0]
            return CLASSES[int(probs.argmax())]
        except Exception as e:  # pragma: no cover
            log.warning("[scene] inference error: %s", e)
            return "clear"
