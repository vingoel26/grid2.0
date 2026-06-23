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

import httpx
from ..core.config import settings

@router.get("/{camera_id}/emergency_route")
async def get_emergency_route(camera_id: str, db: AsyncSession = Depends(get_db), _u: dict = Depends(get_current_user)):
    """Mappls Killer Feature: First-Responder Routing. 
    Returns the fastest route from a predefined Emergency Hub to the camera location."""
    cam = await db.get(Camera, camera_id)
    if not cam or not cam.location_lat or not cam.location_lng:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Camera location not configured")
    
    if not settings.mappls_api_key:
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Mappls API key not configured")

    # Hardcoded Emergency Hub for Hackathon (e.g., Central Police Station)
    # Using approx center of Bangalore for demo purposes: 12.9716, 77.5946
    start_lat, start_lng = 12.9716, 77.5946
    
    url = f"https://apis.mappls.com/advancedmaps/v1/{settings.mappls_api_key}/route_adv/driving/{start_lng},{start_lat};{cam.location_lng},{cam.location_lat}"
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                routes = data.get("routes", [])
                if routes:
                    route = routes[0]
                    return {
                        "status": "success",
                        "distance_meters": route.get("distance"),
                        "duration_seconds": route.get("duration"),
                        "geometry": route.get("geometry"),
                        "hub": {"lat": start_lat, "lng": start_lng},
                        "destination": {"lat": cam.location_lat, "lng": cam.location_lng}
                    }
            return {"status": "error", "message": "Mappls routing failed or no route found"}
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Routing API error: {e}")

