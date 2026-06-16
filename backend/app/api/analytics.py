"""Analytics endpoints — summary / hourly / heatmap."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import get_current_user
from ..schemas import HeatmapPoint, HourlyPoint, SummaryOut
from ..services import analytics_service as svc

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/summary", response_model=SummaryOut)
async def summary(db: AsyncSession = Depends(get_db), _u: dict = Depends(get_current_user)):
    return await svc.summary(db)


@router.get("/hourly", response_model=list[HourlyPoint])
async def hourly(hours: int = Query(24, ge=1, le=168),
                 db: AsyncSession = Depends(get_db), _u: dict = Depends(get_current_user)):
    return await svc.hourly(db, hours)


@router.get("/heatmap", response_model=list[HeatmapPoint])
async def heatmap(db: AsyncSession = Depends(get_db), _u: dict = Depends(get_current_user)):
    return await svc.heatmap(db)
