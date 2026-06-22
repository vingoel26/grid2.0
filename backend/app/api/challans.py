"""Challans API endpoints."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import FileResponse
from pathlib import Path

from ..core.database import get_db
from ..core.security import get_current_user, require_role
from ..schemas.challan import ChallanList, ChallanOut
from ..services import challan_service as svc
from ..main import EVIDENCE_DIR

router = APIRouter(prefix="/api/v1/challans", tags=["challans"])


@router.get("", response_model=ChallanList)
async def list_all(
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    payment_status: Optional[str] = None,
    plate: Optional[str] = None,
):
    total, items = await svc.list_challans(
        db, page=page, page_size=page_size, status=status, 
        payment_status=payment_status, plate=plate
    )
    return ChallanList(total=total, page=page, page_size=page_size,
                       items=[ChallanOut.model_validate(i) for i in items])


@router.get("/{challan_id}", response_model=ChallanOut)
async def get_one(challan_id: str, db: AsyncSession = Depends(get_db),
                  _user: dict = Depends(get_current_user)):
    c = await svc.get_challan(db, challan_id)
    if not c:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Challan not found")
    return c


@router.get("/{challan_id}/pdf")
async def download_pdf(challan_id: str, db: AsyncSession = Depends(get_db),
                       _user: dict = Depends(get_current_user)):
    c = await svc.get_challan(db, challan_id)
    if not c or not c.pdf_path:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "PDF not found")
        
    pdf_rel = c.pdf_path.replace("/evidence/", "")
    pdf_path = EVIDENCE_DIR / pdf_rel
    
    if not pdf_path.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "PDF file missing on disk")
        
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=pdf_path.name
    )


from pydantic import BaseModel
class PaymentRequest(BaseModel):
    payment_ref: str


@router.patch("/{challan_id}/payment", response_model=ChallanOut)
async def mark_paid(challan_id: str, body: PaymentRequest,
                    db: AsyncSession = Depends(get_db),
                    user: dict = Depends(require_role("officer", "admin"))):
    c = await svc.update_payment(db, challan_id, body.payment_ref)
    if not c:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Challan not found")
    return c
