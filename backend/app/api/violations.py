"""Violation CRUD + review endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core import redis_bus
from ..core.database import get_db
from ..core.security import get_current_user, require_role, verify_api_key
from ..schemas import ViolationCreate, ViolationList, ViolationOut, ViolationReview
from ..services import violation_service as svc

router = APIRouter(prefix="/api/v1/violations", tags=["violations"])


@router.post("", response_model=ViolationOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(verify_api_key)])
async def create(payload: ViolationCreate, db: AsyncSession = Depends(get_db)):
    """ML service submits a new violation (API-key auth)."""
    v = await svc.create_violation(db, payload)
    await redis_bus.publish({
        "type": "new_violation",
        "data": {
            "violation_id": v.violation_id, "type": v.violation_type,
            "camera": v.camera_id, "confidence": v.final_confidence,
            "action": v.enforcement_action, "plate_number": v.plate_number,
            "thumbnail_url": f"/api/v1/violations/{v.violation_id}/thumbnail",
        },
    })
    return v


@router.get("", response_model=ViolationList)
async def list_all(
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    violation_type: Optional[str] = None,
    camera_id: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    action: Optional[str] = None,
    plate: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
):
    total, items = await svc.list_violations(
        db, page=page, page_size=page_size, violation_type=violation_type,
        camera_id=camera_id, status=status_filter, action=action, plate=plate,
        date_from=date_from, date_to=date_to,
    )
    return ViolationList(total=total, page=page, page_size=page_size,
                         items=[ViolationOut.model_validate(i) for i in items])


@router.get("/{violation_id}", response_model=ViolationOut)
async def get_one(violation_id: str, db: AsyncSession = Depends(get_db),
                  _user: dict = Depends(get_current_user)):
    v = await svc.get_violation(db, violation_id)
    if not v:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Violation not found")
    return v


@router.patch("/{violation_id}/review", response_model=ViolationOut)
async def review(violation_id: str, body: ViolationReview,
                 db: AsyncSession = Depends(get_db),
                 user: dict = Depends(require_role("officer", "admin"))):
    v = await svc.review_violation(db, violation_id, body.status, body.review_notes,
                                   user["username"])
    if not v:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Violation not found")
    await redis_bus.publish({
        "type": "review_update",
        "data": {"violation_id": v.violation_id, "status": v.status,
                 "reviewed_by": v.reviewed_by},
    })
    return v
