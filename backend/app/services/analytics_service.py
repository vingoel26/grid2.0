"""Dashboard analytics aggregations."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Camera, Violation


def _day_bounds(offset_days: int = 0) -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=offset_days)).replace(hour=0, minute=0, second=0, microsecond=0)
    return start, start + timedelta(days=1)


async def summary(db: AsyncSession) -> dict:
    today_start, today_end = _day_bounds(0)
    y_start, y_end = _day_bounds(1)

    async def _count(*conds) -> int:
        q = select(func.count()).select_from(Violation)
        for c in conds:
            q = q.where(c)
        return (await db.execute(q)).scalar_one()

    total_today = await _count(Violation.occurred_at >= today_start,
                               Violation.occurred_at < today_end)
    total_yesterday = await _count(Violation.occurred_at >= y_start,
                                   Violation.occurred_at < y_end)
    total_all = await _count()
    auto = await _count(Violation.enforcement_action == "AUTO_ENFORCE")
    pending = await _count(Violation.status == "PENDING",
                           Violation.enforcement_action == "HUMAN_REVIEW")

    avg_lat = (await db.execute(
        select(func.coalesce(func.avg(Violation.pipeline_latency_ms), 0.0))
    )).scalar_one()

    by_type_rows = (await db.execute(
        select(Violation.violation_type, func.count()).group_by(Violation.violation_type)
    )).all()
    by_action_rows = (await db.execute(
        select(Violation.enforcement_action, func.count()).group_by(Violation.enforcement_action)
    )).all()

    pct = 0.0
    if total_yesterday:
        pct = round((total_today - total_yesterday) / total_yesterday * 100, 1)

    return {
        "total_today": total_today,
        "total_all_time": total_all,
        "auto_enforced": auto,
        "pending_review": pending,
        "avg_latency_ms": round(float(avg_lat), 1),
        "by_type": {t: c for t, c in by_type_rows},
        "by_action": {a: c for a, c in by_action_rows},
        "pct_change_vs_yesterday": pct,
    }


async def hourly(db: AsyncSession, hours: int = 24) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    bucket = func.date_trunc("hour", Violation.occurred_at)
    rows = (await db.execute(
        select(bucket.label("hour"), func.count())
        .where(Violation.occurred_at >= since)
        .group_by("hour").order_by("hour")
    )).all()
    return [{"hour": h.isoformat() if hasattr(h, "isoformat") else str(h), "count": c}
            for h, c in rows]


async def heatmap(db: AsyncSession) -> list[dict]:
    rows = (await db.execute(
        select(Violation.camera_id, Violation.camera_name,
               Violation.location_lat, Violation.location_lng, func.count())
        .where(Violation.location_lat.isnot(None))
        .group_by(Violation.camera_id, Violation.camera_name,
                  Violation.location_lat, Violation.location_lng)
    )).all()
    return [{"camera_id": cid, "camera_name": cname, "lat": lat, "lng": lng, "count": cnt}
            for cid, cname, lat, lng, cnt in rows]
