import random
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import desc

from app.db.session import get_db
from app.models.crm import Lead, LeadRemark
from app.models.enquiry import Enquiry
from app.models.user import User
from app.models.enums import LeadStatus, LeadPriority, Role, EnquiryStatus
from app.schemas.lead import (
    LeadCreate,
    LeadUpdate,
    LeadResponse,
    LeadRemarkCreate,
    LeadRemarkResponse,
    ConvertEnquiryPayload,
)
from app.api.deps import RequireRole, get_current_user

router = APIRouter(prefix="/leads", tags=["Lead Management & Case Ledger"])

# Access: Super Admin, Senior Partner, and Inquiry Officer
allow_lead_officers = RequireRole([
    Role.SUPER_ADMIN,
    Role.SENIOR_PARTNER,
    Role.INQUIRY_OFFICER,
])

def generate_case_number() -> str:
    year = datetime.utcnow().year
    random_digits = random.randint(1000, 9999)
    return f"RSJ-CAS-{year}-{random_digits}"

@router.get("", response_model=List[LeadResponse], dependencies=[Depends(allow_lead_officers)])
async def list_leads(
    status_filter: Optional[LeadStatus] = Query(None, alias="status"),
    priority_filter: Optional[LeadPriority] = Query(None, alias="priority"),
    practice_filter: Optional[str] = Query(None, alias="practice_area"),
    search: Optional[str] = Query(None, min_length=2),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Lead)
        .options(selectinload(Lead.remarks).selectinload(LeadRemark.author))
        .order_by(desc(Lead.created_at))
    )

    if status_filter:
        query = query.where(Lead.status == status_filter)
    if priority_filter:
        query = query.where(Lead.priority == priority_filter)
    if practice_filter:
        query = query.where(Lead.practice_area.ilike(f"%{practice_filter}%"))
    if search:
        p = f"%{search}%"
        query = query.where(
            (Lead.client_name.ilike(p)) |
            (Lead.client_email.ilike(p)) |
            (Lead.case_title.ilike(p)) |
            (Lead.lead_number.ilike(p))
        )

    result = await db.execute(query.offset(skip).limit(limit))
    leads = result.scalars().all()

    # Flatten author names onto remark response objects
    for lead in leads:
        for remark in lead.remarks:
            if remark.author:
                remark.author_name = remark.author.full_name

    return leads

@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(allow_lead_officers)])
async def create_lead_manually(
    payload: LeadCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    case_num = generate_case_number()
    lead = Lead(
        lead_number=case_num,
        client_name=payload.client_name,
        client_email=payload.client_email,
        client_phone=payload.client_phone,
        alternate_phone=payload.alternate_phone,
        audience=payload.audience,
        practice_area=payload.practice_area,
        case_title=payload.case_title,
        case_description=payload.case_description,
        court_forum=payload.court_forum,
        opposing_party=payload.opposing_party,
        case_filing_number=payload.case_filing_number,
        claim_value=payload.claim_value,
        status=LeadStatus.INTAKE,
        priority=payload.priority,
        assigned_to_id=payload.assigned_to_id,
    )
    db.add(lead)
    await db.flush()

    if payload.initial_remark:
        first_remark = LeadRemark(
            lead_id=lead.id,
            author_id=current_user.id,
            remark=payload.initial_remark,
            next_status=LeadStatus.INTAKE
        )
        db.add(first_remark)

    await db.commit()

    # Re-fetch with relations
    res = await db.execute(
        select(Lead)
        .options(selectinload(Lead.remarks).selectinload(LeadRemark.author))
        .where(Lead.id == lead.id)
    )
    created = res.scalar_one()
    for rem in created.remarks:
        rem.author_name = current_user.full_name
    return created

@router.post("/convert-enquiry/{enquiry_id}", response_model=LeadResponse, dependencies=[Depends(allow_lead_officers)])
async def convert_enquiry_to_lead(
    enquiry_id: str,
    payload: ConvertEnquiryPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    enq_res = await db.execute(select(Enquiry).where(Enquiry.id == enquiry_id))
    enquiry = enq_res.scalar_one_or_none()

    if not enquiry:
        raise HTTPException(status_code=404, detail="Enquiry not found")
    if enquiry.status == EnquiryStatus.CONVERTED_TO_LEAD:
        raise HTTPException(status_code=400, detail="Enquiry is already converted to a Lead")

    case_num = generate_case_number()
    lead = Lead(
        lead_number=case_num,
        client_name=enquiry.full_name,
        client_email=enquiry.email,
        client_phone=enquiry.phone,
        audience=payload.audience,
        practice_area=enquiry.matter_type.value if hasattr(enquiry.matter_type, "value") else str(enquiry.matter_type),
        case_title=payload.case_title or f"Brief: {enquiry.matter_type}",
        case_description=payload.case_description or enquiry.summary,
        court_forum=payload.court_forum,
        status=LeadStatus.INTAKE,
        priority=payload.priority,
        enquiry_id=enquiry.id,
        assigned_to_id=payload.assigned_to_id,
    )
    db.add(lead)
    await db.flush()

    enquiry.status = EnquiryStatus.CONVERTED_TO_LEAD

    remark = LeadRemark(
        lead_id=lead.id,
        author_id=current_user.id,
        remark=payload.initial_remark or f"Enquiry {enquiry.reference_number} upgraded to Active Lead Ledger",
        next_status=LeadStatus.INTAKE
    )
    db.add(remark)

    await db.commit()

    res = await db.execute(
        select(Lead)
        .options(selectinload(Lead.remarks).selectinload(LeadRemark.author))
        .where(Lead.id == lead.id)
    )
    created = res.scalar_one()
    for rem in created.remarks:
        rem.author_name = current_user.full_name
    return created

@router.get("/{lead_id}", response_model=LeadResponse, dependencies=[Depends(allow_lead_officers)])
async def get_lead_details(
    lead_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lead)
        .options(selectinload(Lead.remarks).selectinload(LeadRemark.author))
        .where(Lead.id == lead_id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    for rem in lead.remarks:
        if rem.author:
            rem.author_name = rem.author.full_name

    return lead

@router.patch("/{lead_id}", response_model=LeadResponse, dependencies=[Depends(allow_lead_officers)])
async def update_lead_details(
    lead_id: str,
    payload: LeadUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lead)
        .options(selectinload(Lead.remarks).selectinload(LeadRemark.author))
        .where(Lead.id == lead_id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    update_dict = payload.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(lead, field, value)

    await db.commit()
    await db.refresh(lead)

    for rem in lead.remarks:
        if rem.author:
            rem.author_name = rem.author.full_name

    return lead

@router.post("/{lead_id}/remarks", response_model=LeadRemarkResponse, dependencies=[Depends(allow_lead_officers)])
async def add_lead_remark_and_upgrade_status(
    lead_id: str,
    payload: LeadRemarkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    prev = lead.status
    nxt = payload.next_status if payload.next_status else prev

    remark = LeadRemark(
        lead_id=lead.id,
        author_id=current_user.id,
        remark=payload.remark,
        prev_status=prev,
        next_status=nxt,
    )
    db.add(remark)

    if payload.next_status and payload.next_status != prev:
        lead.status = payload.next_status

    await db.commit()
    await db.refresh(remark)

    remark.author_name = current_user.full_name
    return remark

@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RequireRole([Role.SUPER_ADMIN]))])
async def delete_lead(
    lead_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    await db.delete(lead)
    await db.commit()
    return None