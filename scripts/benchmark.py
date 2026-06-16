#!/usr/bin/env python3
"""Latency profiler — measures per-stage and end-to-end timing (Part 10)."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.config import PipelineConfig  # noqa: E402
from ml.orchestrator import TrafficViolationOrchestrator  # noqa: E402


def main(iterations: int = 50, h: int = 720, w: int = 1280):
    cfg = PipelineConfig()
    orch = TrafficViolationOrchestrator(cfg)
    print(f"Benchmark | device={cfg.device} | imgsz={cfg.img_size} | {iterations} iters")

    frame = (np.random.rand(h, w, 3) * 255).astype("uint8")
    orch.process_frame(frame, time.time(), "BTP_MG_ROAD_01")  # warmup

    times = []
    for _ in range(iterations):
        f = (np.random.rand(h, w, 3) * 255).astype("uint8")
        t0 = time.perf_counter()
        orch.process_frame(f, time.time(), "BTP_MG_ROAD_01")
        times.append((time.perf_counter() - t0) * 1000)

    times.sort()
    mean = sum(times) / len(times)
    p50, p95, p99 = times[len(times)//2], times[int(len(times)*0.95)], times[-1]
    print(f"\n  mean : {mean:7.1f} ms  ({1000/mean:5.1f} FPS)")
    print(f"  p50  : {p50:7.1f} ms")
    print(f"  p95  : {p95:7.1f} ms")
    print(f"  p99  : {p99:7.1f} ms")
    target = 22 if cfg.is_gpu else 205
    status = "PASS" if mean <= target * 1.5 else "REVIEW"
    print(f"\n  target ~{target}ms ({'GPU' if cfg.is_gpu else 'CPU'} mode) -> {status}")
    print("  (note: stub models when weights absent — real latency differs)")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--iters", type=int, default=50)
    main(ap.parse_args().iters)
