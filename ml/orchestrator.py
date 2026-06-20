"""The 7-stage traffic-violation pipeline (Part 2 & Part 6 of plan).

Stage 0  Scene analysis + adaptive enhancement
Stage 1  Parallel multi-model detection (vehicle / person+TL / plate)
Stage 2  Tracking (persistent IDs + trajectories)
Stage 3  Specialist routing + traffic-light state
Stage 4  Violation analyzers (8 types)
Stage 5  License-plate OCR
Stage 6  Confidence calibration + evidence generation
"""
from __future__ import annotations

import logging
import time
from typing import Optional

import numpy as np

from . import violations as V
from .calibration import classify_action, compute_final_confidence
from .config import PipelineConfig
from .enhancement import ImageEnhancer
from .evidence import EvidenceGenerator
from .evidence.generator import FrameBuffer
from .models import (
    HelmetClassifier,
    PersonDetector,
    PlateDetector,
    PlateOCR,
    SceneClassifier,
    SeatbeltDetector,
    VehicleDetector,
)
from .tracking import VehicleTracker
from .traffic_light import classify_traffic_light
from .types import CAR_CLASSES, TWO_WHEELER, Detection, compute_iou
from .violations.geometry import crop

log = logging.getLogger("ml.orchestrator")


class TrafficViolationOrchestrator:
    def __init__(self, config: Optional[PipelineConfig] = None, fps: float = 30.0):
        self.cfg = config or PipelineConfig()
        self.fps = fps
        dev = self.cfg.device

        # Stage 0
        self.scene_classifier = SceneClassifier(self.cfg.scene_model_path, dev)
        self.enhancer = ImageEnhancer()

        # Stage 1
        self.vehicle_model = VehicleDetector(self.cfg.vehicle_model_path, dev, self.cfg.img_size)
        self.person_model = PersonDetector(self.cfg.person_model_path, dev, self.cfg.img_size)
        self.plate_model = PlateDetector(self.cfg.plate_model_path, dev, self.cfg.img_size)

        # Stage 2 — one tracker per camera (persistent IDs across that camera's frames)
        self._trackers: dict[str, VehicleTracker] = {}

        # Stage 4
        self.helmet_classifier = HelmetClassifier(self.cfg.helmet_model_path, dev)
        self.seatbelt_model = SeatbeltDetector(self.cfg.seatbelt_model_path, dev, self.cfg.img_size)

        # Stage 5
        ocr_cfg = self.cfg.thresholds.get("ocr", {})
        self.ocr = PlateOCR(dev, ocr_cfg.get("min_conf", 0.70),
                            ocr_cfg.get("plate_regex", r"^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}$"))

        # Stage 6
        self.evidence_gen = EvidenceGenerator(self.cfg.evidence_dir)
        self._frame_buffers: dict[str, FrameBuffer] = {}

        cal = self.cfg.thresholds.get("calibration", {})
        self._cal = dict(
            temperature=cal.get("temperature", 1.3),
            frame_boost_per=cal.get("frame_boost_per", 0.05),
            frame_boost_max=cal.get("frame_boost_max", 0.15),
            plate_boost=cal.get("plate_boost", 0.05),
        )
        enf = self.cfg.thresholds.get("enforcement", {})
        self._auto = enf.get("auto_enforce", 0.90)
        self._review = enf.get("human_review", 0.70)

        log.info("Pipeline initialized | device=%s | models=7 | gpu=%s",
                 self.cfg.device, self.cfg.is_gpu)

    # -- per-camera state ---------------------------------------------
    def _tracker(self, camera_id: str) -> VehicleTracker:
        if camera_id not in self._trackers:
            self._trackers[camera_id] = VehicleTracker(self.cfg.tracker_config)
        return self._trackers[camera_id]

    def _buffer(self, camera_id: str) -> FrameBuffer:
        if camera_id not in self._frame_buffers:
            self._frame_buffers[camera_id] = FrameBuffer(seconds=3.0, fps=self.fps)
        return self._frame_buffers[camera_id]

    # -- main entry ----------------------------------------------------
    def process_frame(self, frame: np.ndarray, timestamp: Optional[float] = None,
                      camera_id: str = "default") -> list:
        t0 = time.perf_counter()
        timestamp = timestamp if timestamp is not None else time.time()
        camera_cfg = self.cfg.camera(camera_id)
        fb = self._buffer(camera_id)
        fb.push(frame)

        # ── Stage 0 ──
        scene = self.scene_classifier.classify(frame)
        enhanced = self.enhancer.enhance(frame, scene)

        # ── Stage 1 (parallel on GPU via CUDA streams; sequential on CPU) ──
        vehicle_dets, person_all, plate_dets = self._detect(enhanced)
        persons = [d for d in person_all if d.cls_name == "person"]
        traffic_lights = [d for d in person_all if d.cls_name == "traffic_light"]

        # ── Stage 2 ──
        tracks = self._tracker(camera_id).update(vehicle_dets)

        # ── Stage 3 ──
        tl_state = classify_traffic_light(enhanced, traffic_lights)

        # ── Stage 4 ──
        found: list = []
        for track in tracks:
            found += self._analyze_track(enhanced, track, persons, plate_dets,
                                         tl_state, camera_cfg, timestamp)

        # ── Stage 5 — OCR all plates once, then match to violations ──
        plate_texts = self._ocr_plates(enhanced, plate_dets)

        # ── Stage 6 — calibrate, score, evidence ──
        emitted = []
        for v in found:
            v.plate_number, v.plate_confidence = self._match_plate(v.vehicle_bbox, plate_texts)
            v.final_confidence = compute_final_confidence(v, **self._cal)
            v.action = classify_action(v.final_confidence, self._auto, self._review)
            if v.action in ("AUTO_ENFORCE", "HUMAN_REVIEW"):
                v.evidence = self.evidence_gen.generate(frame, v, timestamp, fb)
                emitted.append(v)

        latency_ms = (time.perf_counter() - t0) * 1000.0
        for v in emitted:
            v.extra["pipeline_latency_ms"] = round(latency_ms, 2)
            v.extra["scene"] = scene
        return emitted

    # -- stage helpers -------------------------------------------------
    def _detect(self, frame) -> tuple[list, list, list]:
        if self.cfg.is_gpu:
            try:
                import torch

                s1, s2, s3 = torch.cuda.Stream(), torch.cuda.Stream(), torch.cuda.Stream()
                with torch.cuda.stream(s1):
                    veh = self.vehicle_model.detect(frame, self.cfg.vehicle_conf, self.cfg.iou)
                with torch.cuda.stream(s2):
                    ppl = self.person_model.detect(frame, self.cfg.person_conf, self.cfg.iou)
                with torch.cuda.stream(s3):
                    plt = self.plate_model.detect(frame, self.cfg.plate_conf, self.cfg.iou)
                torch.cuda.synchronize()
                return veh, ppl, plt
            except Exception as e:  # pragma: no cover
                log.debug("CUDA-stream path failed (%s); falling back to sequential", e)
        veh = self.vehicle_model.detect(frame, self.cfg.vehicle_conf, self.cfg.iou)
        ppl = self.person_model.detect(frame, self.cfg.person_conf, self.cfg.iou)
        plt = self.plate_model.detect(frame, self.cfg.plate_conf, self.cfg.iou)
        return veh, ppl, plt

    def _analyze_track(self, frame, track, persons, plates, tl_state, camera_cfg, ts) -> list:
        vio = self.cfg.vio
        out: list = []

        if track.cls_name == TWO_WHEELER:
            out += V.check_helmet(frame, track, persons, self.helmet_classifier,
                                  vio("helmet"), camera_cfg.id, ts)
            out += V.check_triple_riding(track, persons, vio("triple_riding"), camera_cfg.id, ts)
        elif track.cls_name in CAR_CLASSES:
            out += V.check_seatbelt(frame, track, self.seatbelt_model,
                                    vio("seatbelt"), camera_cfg.id, ts)

        out += V.check_wrong_side(track, camera_cfg, vio("wrong_side"), ts)
        out += V.check_intersection(track, tl_state, camera_cfg,
                                    vio("stop_line"), vio("red_light"), ts)
        out += V.check_illegal_parking(track, camera_cfg, vio("illegal_parking"), self.fps, ts)
        out += V.check_no_plate(track, plates, vio("no_plate"), camera_cfg.id, ts)
        return out

    def _ocr_plates(self, frame, plate_dets: list[Detection]) -> list[tuple]:
        """Return list of (bbox, text, conf) for readable plates."""
        results = []
        for p in plate_dets:
            c = crop(frame, p.bbox)
            text, conf = self.ocr.read(c)
            if text != "UNREADABLE":
                results.append((p.bbox, text, conf))
        return results

    @staticmethod
    def _match_plate(vehicle_bbox, plate_texts) -> tuple[Optional[str], float]:
        best, best_score, best_conf = None, 0.0, 0.0
        vx1, vy1, vx2, vy2 = vehicle_bbox
        margin_x = (vx2 - vx1) * 0.20
        margin_y = (vy2 - vy1) * 0.20
        for bbox, text, conf in plate_texts:
            # Score by IoU
            iou = compute_iou(vehicle_bbox, bbox)
            score = iou
            # Also check plate center inside vehicle bbox (for tiny plates)
            px = (bbox[0] + bbox[2]) / 2
            py = (bbox[1] + bbox[3]) / 2
            if (vx1 - margin_x) <= px <= (vx2 + margin_x) and \
               (vy1 - margin_y) <= py <= (vy2 + margin_y):
                score = max(score, 0.5)  # containment match = 0.5 baseline
            if score > best_score and score > 0.01:
                best, best_score, best_conf = text, score, conf
        return best, best_conf
