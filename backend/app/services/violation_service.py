"""Violation persistence + query logic."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Camera, Violation
from ..schemas import ViolationCreate


import httpx
from ..core.config import settings

async def _fetch_mappls_jurisdiction(lat: float, lng: float) -> str | None:
    if not settings.mappls_api_key:
        return None
    url = f"https://apis.mappls.com/advancedmaps/v1/{settings.mappls_api_key}/rev_geocode?lat={lat}&lng={lng}"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                if results and isinstance(results, list):
                    item = results[0]
                    addr = item.get("formatted_address", "")
                    city = item.get("city", "") or item.get("district", "Unknown")
                    pincode = item.get("pincode", "")
                    return f"{addr} [Jurisdiction: {city} Traffic Police, Pin: {pincode}]"
    except Exception as e:
        import logging
        logging.getLogger("backend").warning(f"Mappls rev-geocode failed: {e}")
    return None

async def create_violation(db: AsyncSession, payload: ViolationCreate) -> Violation:
    data = payload.model_dump()
    # enrich location from camera if known
    cam = await db.get(Camera, payload.camera_id)
    v = Violation(**data)
    if cam:
        v.camera_name = cam.name
        v.location_lat = cam.location_lat
        v.location_lng = cam.location_lng
        v.location_name = cam.name
        
        # Mappls Killer Feature: Automated E-Challan Jurisdiction Routing
        if cam.location_lat and cam.location_lng:
            jurisdiction = await _fetch_mappls_jurisdiction(cam.location_lat, cam.location_lng)
            if jurisdiction:
                v.location_name = jurisdiction

    db.add(v)
    await db.commit()
    await db.refresh(v)
    return v


async def get_violation(db: AsyncSession, violation_id: str) -> Optional[Violation]:
    # accept either UUID pk or the business violation_id
    v = await db.get(Violation, violation_id)
    if v:
        return v
    res = await db.execute(select(Violation).where(Violation.violation_id == violation_id))
    return res.scalar_one_or_none()


async def list_violations(db: AsyncSession, *, page: int = 1, page_size: int = 50,
                          violation_type: str | None = None, camera_id: str | None = None,
                          status: str | None = None, action: str | None = None,
                          plate: str | None = None, date_from: datetime | None = None,
                          date_to: datetime | None = None) -> tuple[int, list[Violation]]:
    q = select(Violation)
    count_q = select(func.count()).select_from(Violation)
    conds = []
    if violation_type:
        conds.append(Violation.violation_type == violation_type)
    if camera_id:
        conds.append(Violation.camera_id == camera_id)
    if status:
        conds.append(Violation.status == status)
    if action:
        conds.append(Violation.enforcement_action == action)
    if plate:
        conds.append(Violation.plate_number.ilike(f"%{plate}%"))
    if date_from:
        conds.append(Violation.occurred_at >= date_from)
    if date_to:
        conds.append(Violation.occurred_at <= date_to)
    for c in conds:
        q = q.where(c)
        count_q = count_q.where(c)

    total = (await db.execute(count_q)).scalar_one()
    q = q.order_by(Violation.occurred_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items = list((await db.execute(q)).scalars().all())
    return total, items


async def review_violation(db: AsyncSession, violation_id: str, status: str,
                           notes: str | None, reviewer: str) -> Optional[Violation]:
    v = await get_violation(db, violation_id)
    if not v:
        return None
    v.status = status
    v.review_notes = notes
    v.reviewed_by = reviewer
    v.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(v)
    return v
