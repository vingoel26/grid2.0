"""Gridlock 2.0 backend — FastAPI entrypoint (port 8000)."""
from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api import analytics, auth, cameras, violations, websocket, challans
from .core.config import settings
from .core.database import Base, engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("backend")

# Repo root when run locally (backend/app/main.py -> grid/); overridable via env
# so the same code works in Docker where layout differs.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EVIDENCE_DIR = Path(os.getenv("EVIDENCE_DIR", _REPO_ROOT / "evidence"))
CONFIG_DIR = Path(os.getenv("CONFIG_DIR", _REPO_ROOT / "configs"))


async def _init_db() -> None:
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        log.info("DB tables ensured")
    except Exception as e:  # pragma: no cover
        log.warning("DB init skipped (%s) — is PostgreSQL up?", e)


async def _seed_cameras() -> None:
    """Load configs/cameras.yaml into the cameras table if empty."""
    import yaml
    from sqlalchemy import func, select

    from .core.database import SessionLocal
    from .models import Camera

    cfg_path = CONFIG_DIR / "cameras.yaml"
    if not cfg_path.exists():
        return
    try:
        async with SessionLocal() as db:
            count = (await db.execute(select(func.count()).select_from(Camera))).scalar_one()
            if count:
                return
            raw = yaml.safe_load(cfg_path.read_text()) or {}
            for c in raw.get("cameras", []):
                loc = c.get("location", {}) or {}
                db.add(Camera(
                    id=c["id"], name=c.get("name", c["id"]),
                    location_lat=loc.get("lat"), location_lng=loc.get("lng"),
                    rtsp_url=c.get("rtsp_url"),
                    expected_flow_direction=c.get("expected_flow_direction", 0.0),
                    stop_line_polygon=c.get("stop_line_polygon"),
                    intersection_polygon=c.get("intersection_polygon"),
                    no_parking_zones=c.get("no_parking_zones"),
                ))
            await db.commit()
            log.info("Seeded %d cameras", len(raw.get("cameras", [])))
    except Exception as e:  # pragma: no cover
        log.warning("Camera seed skipped (%s)", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _init_db()
    await _seed_cameras()
    listener = asyncio.create_task(websocket.redis_listener())
    yield
    listener.cancel()


app = FastAPI(title="Gridlock 2.0 API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(violations.router)
app.include_router(analytics.router)
app.include_router(cameras.router)
app.include_router(challans.router)
app.include_router(websocket.router)

# Serve evidence files (annotated images, clips) for the dashboard.
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/evidence", StaticFiles(directory=str(EVIDENCE_DIR)), name="evidence")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "gridlock-backend", "version": "2.0.0"}
