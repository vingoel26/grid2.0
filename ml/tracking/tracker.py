"""Stage 2 — multi-object tracking.

BoT-SORT (Ultralytics) is the production tracker, but it's designed to run
*inside* model.track(). Since our architecture detects with multiple models and
tracks the fused vehicle detections, we use a self-contained IoU + centroid
tracker that preserves the same contract: persistent integer IDs, per-track
trajectories, and a configurable track buffer for occlusion handling.

The greedy-IoU association below is intentionally simple and dependency-free so
the pipeline runs anywhere; swap in BoT-SORT's matching cascade for production.
"""
from __future__ import annotations

from ..types import Detection, Track, compute_iou


class VehicleTracker:
    def __init__(self, config: dict | None = None, max_trajectory: int = 1024):
        config = config or {}
        self.match_thresh = 1.0 - config.get("match_thresh", 0.85)  # IoU floor for a match
        self.iou_floor = 0.2
        self.track_buffer = int(config.get("track_buffer", 60))
        self.new_track_thresh = config.get("new_track_thresh", 0.6)
        self.max_trajectory = max_trajectory

        self._tracks: dict[int, Track] = {}
        self._missed: dict[int, int] = {}  # frames since last seen
        self._next_id = 1

    def reset(self) -> None:
        self._tracks.clear()
        self._missed.clear()
        self._next_id = 1

    def update(self, detections: list[Detection]) -> list[Track]:
        """Associate detections to existing tracks, spawn/retire as needed."""
        unmatched_dets = list(range(len(detections)))
        matched_track_ids: set[int] = set()

        # Greedy IoU matching: best pairs first.
        candidates: list[tuple[float, int, int]] = []  # (iou, track_id, det_idx)
        for tid, trk in self._tracks.items():
            for di, det in enumerate(detections):
                iou = compute_iou(trk.bbox, det.bbox)
                if iou >= self.iou_floor:
                    candidates.append((iou, tid, di))
        candidates.sort(reverse=True)

        used_dets: set[int] = set()
        for iou, tid, di in candidates:
            if tid in matched_track_ids or di in used_dets:
                continue
            det = detections[di]
            trk = self._tracks[tid]
            trk.bbox = det.bbox
            trk.confidence = det.confidence
            trk.cls_id = det.cls_id
            trk.cls_name = det.cls_name
            trk.trajectory.append(det.center)
            if len(trk.trajectory) > self.max_trajectory:
                trk.trajectory.pop(0)
            matched_track_ids.add(tid)
            used_dets.add(di)
            self._missed[tid] = 0

        unmatched_dets = [i for i in unmatched_dets if i not in used_dets]

        # Spawn new tracks for confident unmatched detections.
        for di in unmatched_dets:
            det = detections[di]
            if det.confidence < self.new_track_thresh:
                continue
            tid = self._next_id
            self._next_id += 1
            self._tracks[tid] = Track(
                id=tid, bbox=det.bbox, confidence=det.confidence,
                cls_id=det.cls_id, cls_name=det.cls_name, trajectory=[det.center],
            )
            self._missed[tid] = 0
            matched_track_ids.add(tid)

        # Age & retire tracks not matched this frame.
        for tid in list(self._tracks.keys()):
            if tid not in matched_track_ids:
                self._missed[tid] = self._missed.get(tid, 0) + 1
                if self._missed[tid] > self.track_buffer:
                    del self._tracks[tid]
                    del self._missed[tid]

        # Return only tracks observed this frame.
        return [self._tracks[tid] for tid in matched_track_ids if tid in self._tracks]
