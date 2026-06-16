"""ML inference microservice (FastAPI, port 8001).

Endpoints:
  GET  /health                     — pipeline + model availability
  POST /infer/image                — single image upload -> violations
  POST /stream/start               — begin processing an RTSP/video source
  POST /stream/stop                — stop a running stream
  GET  /streams                    — list active streams

Detected AUTO_ENFORCE / HUMAN_REVIEW violations are forwarded to the backend.
"""
from __future__ import annotations

import asyncio
import logging
import threading
import time
from contextlib import asynccontextmanager

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse

from .backend_client import BackendClient
from .config import PipelineConfig
from .orchestrator import TrafficViolationOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("ml.server")

STATE: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = PipelineConfig()
    STATE["cfg"] = cfg
    STATE["orch"] = TrafficViolationOrchestrator(cfg)
    STATE["client"] = BackendClient(cfg.backend_url, cfg.ml_api_key)
    STATE["streams"] = {}  # camera_id -> StreamWorker
    log.info("ML service ready on device=%s", cfg.device)
    yield
    for w in list(STATE.get("streams", {}).values()):
        w.stop()


app = FastAPI(title="Gridlock 2.0 ML Service", version="2.0.0", lifespan=lifespan)


def _violation_brief(v) -> dict:
    return {
        "violation_id": (v.evidence or {}).get("violation_id"),
        "type": v.type,
        "camera_id": v.camera_id,
        "vehicle_type": v.vehicle_type,
        "plate_number": v.plate_number,
        "final_confidence": round(v.final_confidence, 3),
        "action": v.action,
        "fine_inr": v.fine_inr,
    }


@app.get("/health")
async def health():
    orch: TrafficViolationOrchestrator = STATE["orch"]
    return {
        "status": "ok",
        "device": STATE["cfg"].device,
        "models": {
            "vehicle": orch.vehicle_model.available,
            "person": orch.person_model.available,
            "plate": orch.plate_model.available,
            "seatbelt": orch.seatbelt_model.available,
            "helmet": orch.helmet_classifier.available,
            "scene": orch.scene_classifier.available,
            "ocr": orch.ocr.available,
        },
        "active_streams": list(STATE["streams"].keys()),
    }


@app.post("/infer/image")
async def infer_image(file: UploadFile = File(...), camera_id: str = Form("default")):
    raw = await file.read()
    arr = np.frombuffer(raw, np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        return JSONResponse({"error": "could not decode image"}, status_code=400)

    orch: TrafficViolationOrchestrator = STATE["orch"]
    violations = orch.process_frame(frame, timestamp=time.time(), camera_id=camera_id)

    client: BackendClient = STATE["client"]
    for v in violations:
        await client.submit(v)

    return {"camera_id": camera_id, "count": len(violations),
            "violations": [_violation_brief(v) for v in violations]}


class StreamWorker:
    """Background thread that pulls frames from a source and runs the pipeline."""

    def __init__(self, source: str, camera_id: str, orch, client, loop, frame_skip: int = 1):
        self.source = source
        self.camera_id = camera_id
        self.orch = orch
        self.client = client
        self.loop = loop
        self.frame_skip = max(frame_skip, 1)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self.frames_processed = 0
        self.violations_found = 0

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _run(self):
        cap = cv2.VideoCapture(self.source)
        if not cap.isOpened():
            log.error("[%s] cannot open source %s", self.camera_id, self.source)
            return
        idx = 0
        while not self._stop.is_set():
            ok, frame = cap.read()
            if not ok:
                break
            idx += 1
            if idx % self.frame_skip != 0:
                continue
            violations = self.orch.process_frame(frame, time.time(), self.camera_id)
            self.frames_processed += 1
            self.violations_found += len(violations)
            for v in violations:
                asyncio.run_coroutine_threadsafe(self.client.submit(v), self.loop)
        cap.release()
        log.info("[%s] stream ended", self.camera_id)


@app.post("/stream/start")
async def stream_start(source: str = Form(...), camera_id: str = Form(...),
                       frame_skip: int = Form(1)):
    streams = STATE["streams"]
    if camera_id in streams:
        return JSONResponse({"error": f"stream {camera_id} already running"}, status_code=409)
    worker = StreamWorker(source, camera_id, STATE["orch"], STATE["client"],
                          asyncio.get_running_loop(), frame_skip)
    streams[camera_id] = worker
    worker.start()
    return {"status": "started", "camera_id": camera_id, "source": source}


@app.post("/stream/stop")
async def stream_stop(camera_id: str = Form(...)):
    worker = STATE["streams"].pop(camera_id, None)
    if not worker:
        return JSONResponse({"error": "not found"}, status_code=404)
    worker.stop()
    return {"status": "stopped", "camera_id": camera_id,
            "frames_processed": worker.frames_processed,
            "violations_found": worker.violations_found}


@app.get("/streams")
async def streams():
    return {cid: {"frames": w.frames_processed, "violations": w.violations_found}
            for cid, w in STATE["streams"].items()}
