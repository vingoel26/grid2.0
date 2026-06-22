from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ChallanOut(BaseModel):
    id: str
    challan_number: str
    violation_id: str
    
    owner_name: Optional[str]
    owner_phone: Optional[str]
    owner_email: Optional[str]
    owner_address: Optional[str]
    
    status: str
    sent_via: Optional[str]
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    
    pdf_path: Optional[str]
    
    payment_due_date: Optional[datetime]
    payment_status: str
    payment_ref: Optional[str]
    
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChallanList(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ChallanOut]
