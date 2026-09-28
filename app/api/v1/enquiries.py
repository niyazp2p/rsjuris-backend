import random
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc

from app.db.session import get_db
from app.models.enquiry import Enquiry
from app.models.enums import EnquiryStatus, MatterType, Role
from app.schemas.enquiry import (
    EnquiryCreate,
    EnquiryResponse,
    EnquiryStatusUpdate,
    EnquiryPublicConfirmation,
)
from app.api.deps import RequireRole

router = APIRouter(prefix="/enquiries", tags=["Enquiries & Contact Intake"])

# Access control: Super Admin, Senior Partner, and Inquiry Officer
allow_intake_officers = RequireRole([
    Role.SUPER_ADMIN,
    Role.SENIOR_PARTNER,
    Role.INQUIRY_OFFICER,
])

def generate_reference_number() -> str:
    year = datetime.utcnow().year
    random_digits = random.randint(1000, 9999)
    return f"RSJ-ENQ-{year}-{random_digits}"

# ---------------------------------------------------------------------------
# Public Intake Endpoint (Website Contact Page)
# ---------------------------------------------------------------------------
@router.post(
    "",
    response_model=EnquiryPublicConfirmation,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Contact Page Consultation Brief",
)
async def submit_public_enquiry(
    payload: EnquiryCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Public intake receiver connected directly to the website contact form.
    Generates a tracking reference and logs submission metadata.
    """
    # Generate unique reference number
    ref_num = generate_reference_number()
    existing_ref = await db.execute(select(Enquiry).where(Enquiry.reference_number == ref_num))
    while existing_ref.scalar_one_or_none():
        ref_num = generate_reference_number()
        existing_ref = await db.execute(select(Enquiry).where(Enquiry.reference_number == ref_num))

    # Extract client network headers
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    enquiry = Enquiry(
        reference_number=ref_num,
        full_name=payload.full_name,
        phone=payload.phone,
        email=payload.email,
        matter_type=payload.matter_type,
        summary=payload.summary,
        status=EnquiryStatus.NEW,
        ip_address=client_ip,
        user_agent=user_agent[:255] if user_agent else None,
    )
    db.add(enquiry)
    await db.commit()
    await db.refresh(enquiry)

    return EnquiryPublicConfirmation(
        reference_number=enquiry.reference_number,
        message="Your brief has been registered with the chamber registry. A partner will contact you shortly.",
        received_at=enquiry.created_at,
    )

# ---------------------------------------------------------------------------
# Admin Protected Endpoints
# ---------------------------------------------------------------------------
@router.get(
    "/admin",
    response_model=List[EnquiryResponse],
    dependencies=[Depends(allow_intake_officers)],
    summary="List & Filter Enquiries (Chamber Dashboard)",
)
async def list_enquiries(
    status_filter: Optional[EnquiryStatus] = Query(None, alias="status"),
    matter_filter: Optional[MatterType] = Query(None, alias="matter_type"),
    search: Optional[str] = Query(None, min_length=2, description="Search client name, email, or reference number"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Enquiry).order_by(desc(Enquiry.created_at))

    if status_filter:
        query = query.where(Enquiry.status == status_filter)
    if matter_filter:
        query = query.where(Enquiry.matter_type == matter_filter)
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Enquiry.full_name.ilike(search_pattern)) |
            (Enquiry.email.ilike(search_pattern)) |
            (Enquiry.reference_number.ilike(search_pattern))
        )

    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

@router.get(
    "/admin/{enquiry_id}",
    response_model=EnquiryResponse,
    dependencies=[Depends(allow_intake_officers)],
    summary="Get Single Enquiry Details",
)
async def get_enquiry(
    enquiry_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Enquiry).where(Enquiry.id == enquiry_id))
    enquiry = result.scalar_one_or_none()
    if not enquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enquiry not found",
        )
    return enquiry

@router.patch(
    "/admin/{enquiry_id}/status",
    response_model=EnquiryResponse,
    dependencies=[Depends(allow_intake_officers)],
    summary="Update Enquiry Triage Status",
)
async def update_enquiry_status(
    enquiry_id: str,
    payload: EnquiryStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Enquiry).where(Enquiry.id == enquiry_id))
    enquiry = result.scalar_one_or_none()
    if not enquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enquiry not found",
        )

    enquiry.status = payload.status
    await db.commit()
    await db.refresh(enquiry)
    return enquiry

@router.delete(
    "/admin/{enquiry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(RequireRole([Role.SUPER_ADMIN]))],
    summary="Delete Enquiry (Super Admin only)",
)
async def delete_enquiry(
    enquiry_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Enquiry).where(Enquiry.id == enquiry_id))
    enquiry = result.scalar_one_or_none()
    if not enquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enquiry not found",
        )

    await db.delete(enquiry)
    await db.commit()
    return None