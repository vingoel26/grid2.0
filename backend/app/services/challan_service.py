"""Challan orchestrator service."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Challan, Violation
from .owner_lookup import lookup_owner
from .challan_generator import generate_pdf
from .notification_service import notify_owner
from ..core import redis_bus

log = logging.getLogger("backend.challan_service")


async def generate_challan_number(db: AsyncSession) -> str:
    """Generate the next challan number: GRD-YYYY-NNNNNN"""
    year = datetime.now().year
    prefix = f"GRD-{year}-"
    
    # Get the latest challan number for this year
    stmt = select(Challan.challan_number).where(Challan.challan_number.startswith(prefix)).order_by(Challan.challan_number.desc()).limit(1)
    result = await db.execute(stmt)
    latest = result.scalar_one_or_none()
    
    if latest:
        # Extract the sequence number
        try:
            seq = int(latest.replace(prefix, ""))
            next_seq = seq + 1
        except ValueError:
            next_seq = 1
    else:
        next_seq = 1
        
    return f"{prefix}{next_seq:06d}"


async def dispatch_challan(db: AsyncSession, violation: Violation) -> Challan | None:
    """
    Main orchestration logic:
    1. Lookup owner
    2. Create DB record
    3. Generate PDF
    4. Notify
    """
    if not violation.plate_number:
        log.warning(f"Cannot dispatch challan for {violation.violation_id}: No plate number")
        return None
        
    # Check if a challan already exists for this violation
    stmt = select(Challan).where(Challan.violation_id == violation.violation_id)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        log.info(f"Challan already exists for violation {violation.violation_id}: {existing.challan_number}")
        return existing

    # 1. Lookup owner
    owner = lookup_owner(violation.plate_number)
    if not owner:
        log.warning(f"Owner lookup failed for plate {violation.plate_number}")
        owner_name = None
        owner_phone = None
        owner_email = None
        owner_address = None
    else:
        owner_name = owner.name
        owner_phone = owner.phone
        owner_email = owner.email
        owner_address = owner.address

    # 2. Create DB Record (GENERATED state)
    challan_num = await generate_challan_number(db)
    due_date = datetime.now(timezone.utc) + timedelta(days=15)
    
    challan = Challan(
        challan_number=challan_num,
        violation_id=violation.violation_id,
        owner_name=owner_name,
        owner_phone=owner_phone,
        owner_email=owner_email,
        owner_address=owner_address,
        status="GENERATED",
        payment_due_date=due_date,
        payment_status="UNPAID"
    )
    db.add(challan)
    await db.commit()
    await db.refresh(challan)
    
    # 3. Generate PDF
    if owner:
        try:
            pdf_path = generate_pdf(challan_num, violation, owner, due_date)
            challan.pdf_path = pdf_path
            await db.commit()
        except Exception as e:
            log.error(f"Error generating PDF for {challan_num}: {e}")
            challan.status = "FAILED"
            await db.commit()
            return challan
            
        # 4. Send Notifications
        try:
            success_channels = notify_owner(challan_num, violation, owner, pdf_path, violation.fine_inr)
            if success_channels:
                challan.status = "SENT"
                challan.sent_via = ",".join(success_channels)
                challan.sent_at = datetime.now(timezone.utc)
            else:
                challan.status = "FAILED"
        except Exception as e:
            log.error(f"Error sending notifications for {challan_num}: {e}")
            challan.status = "FAILED"
            
        await db.commit()
        await db.refresh(challan)
        
    # Broadcast event
    await redis_bus.publish({
        "type": "challan_issued",
        "data": {
            "challan_number": challan.challan_number,
            "violation_id": challan.violation_id,
            "plate_number": violation.plate_number,
            "status": challan.status
        }
    })
    
    return challan


async def list_challans(db: AsyncSession, *, page: int = 1, page_size: int = 50,
                        status: str | None = None, payment_status: str | None = None,
                        plate: str | None = None) -> tuple[int, list[Challan]]:
    """List challans with filtering and pagination."""
    q = select(Challan)
    count_q = select(func.count()).select_from(Challan)
    
    conds = []
    if status:
        conds.append(Challan.status == status)
    if payment_status:
        conds.append(Challan.payment_status == payment_status)
    if plate:
        # Join with violation to filter by plate if needed, or if we want to add plate to challan
        # For simplicity, since we need plate, we can do a subquery or join
        # But we don't have plate on Challan. Let's do a join with Violation.
        q = q.join(Violation, Challan.violation_id == Violation.violation_id)
        count_q = count_q.join(Violation, Challan.violation_id == Violation.violation_id)
        conds.append(Violation.plate_number.ilike(f"%{plate}%"))

    for c in conds:
        q = q.where(c)
        count_q = count_q.where(c)

    total = (await db.execute(count_q)).scalar_one()
    q = q.order_by(Challan.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items = list((await db.execute(q)).scalars().all())
    return total, items


async def get_challan(db: AsyncSession, challan_identifier: str) -> Optional[Challan]:
    """Get a challan by its PK or challan_number."""
    c = await db.get(Challan, challan_identifier)
    if c:
        return c
    stmt = select(Challan).where(Challan.challan_number == challan_identifier)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


async def update_payment(db: AsyncSession, challan_id: str, payment_ref: str) -> Optional[Challan]:
    """Mark a challan as paid."""
    challan = await get_challan(db, challan_id)
    if not challan:
        return None
        
    challan.payment_status = "PAID"
    challan.payment_ref = payment_ref
    challan.status = "DELIVERED" # Assuming if paid, it was delivered.
    await db.commit()
    await db.refresh(challan)
    return challan
