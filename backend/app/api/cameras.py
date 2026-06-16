"""Camera management endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import get_current_user, require_role
from ..models import Camera
from ..schemas import CameraCreate, CameraOut, CameraUpdate

router = APIRouter(prefix="/api/v1/cameras", tags=["cameras"])


@router.get("", response_model=list[CameraOut])
async def list_cameras(db: AsyncSession = Depends(get_db), _u: dict = Depends(get_current_user)):
    rows = (await db.execute(select(Camera))).scalars().all()
    return list(rows)


@router.post("", response_model=CameraOut, status_code=status.HTTP_201_CREATED)
async def create_camera(body: CameraCreate, db: AsyncSession = Depends(get_db),
                        _u: dict = Depends(require_role("admin"))):
    if await db.get(Camera, body.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Camera id already exists")
    cam = Camera(**body.model_dump())
    db.add(cam)
    await db.commit()
    await db.refresh(cam)
    return cam


@router.patch("/{camera_id}", response_model=CameraOut)
async def update_camera(camera_id: str, body: CameraUpdate, db: AsyncSession = Depends(get_db),
                        _u: dict = Depends(require_role("admin"))):
    cam = await db.get(Camera, camera_id)
    if not cam:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Camera not found")
    for k, val in body.model_dump(exclude_unset=True).items():
        setattr(cam, k, val)
    await db.commit()
    await db.refresh(cam)
    return cam
