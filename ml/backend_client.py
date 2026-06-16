"""Posts detected violations from the ML service to the backend API."""
from __future__ import annotations

import logging
from typing import Any

import httpx

log = logging.getLogger("ml.client")


class BackendClient:
    def __init__(self, base_url: str, api_key: str, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-API-Key": api_key}
        self.timeout = timeout

    def _payload(self, v) -> dict[str, Any]:
        ev = v.evidence or {}
        return {
            "violation_id": ev.get("violation_id", f"V_{int(v.timestamp)}_{v.vehicle_track_id}"),
            "violation_type": v.type,
            "violation_code": v.violation_code,
            "fine_inr": v.fine_inr,
            "camera_id": v.camera_id,
            "raw_confidence": v.raw_confidence,
            "final_confidence": v.final_confidence,
            "enforcement_action": v.action,
            "vehicle_type": v.vehicle_type,
            "plate_number": v.plate_number,
            "plate_confidence": v.plate_confidence,
            "vehicle_bbox": list(v.vehicle_bbox),
            "evidence_image_path": ev.get("evidence_image_path"),
            "evidence_thumbnail_path": ev.get("evidence_thumbnail_path"),
            "evidence_video_path": ev.get("evidence_video_path"),
            "evidence_hash": ev.get("evidence_hash"),
            "model_version": "gridlock-2.0",
            "pipeline_latency_ms": v.extra.get("pipeline_latency_ms"),
            "occurred_at": v.timestamp,
        }

    async def submit(self, violation) -> bool:
        url = f"{self.base_url}/api/v1/violations"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.post(url, json=self._payload(violation), headers=self.headers)
                r.raise_for_status()
                return True
        except Exception as e:
            log.warning("submit failed (%s): %s", violation.type, e)
            return False

    def submit_sync(self, violation) -> bool:
        url = f"{self.base_url}/api/v1/violations"
        try:
            r = httpx.post(url, json=self._payload(violation), headers=self.headers,
                           timeout=self.timeout)
            r.raise_for_status()
            return True
        except Exception as e:
            log.warning("submit failed (%s): %s", violation.type, e)
            return False
