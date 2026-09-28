from collections import Counter
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, desc

from app.db.session import get_db
from app.models.enquiry import Enquiry
from app.models.crm import Lead, LeadRemark
from app.models.cms import Article
from app.models.enums import EnquiryStatus, LeadStatus, ContentStatus, AudienceSegment, Role
from app.schemas.dashboard import (
    DashboardMetricsResponse,
    PipelineCounts,
    EditorialCounts,
    AudienceBreakdown,
    PracticeAreaStat,
    ActivityFeedItem,
)
from app.api.deps import RequireRole

router = APIRouter(prefix="/dashboard", tags=["Executive Dashboard Analytics"])

allow_chamber_staff = RequireRole([
    Role.SUPER_ADMIN,
    Role.SENIOR_PARTNER,
    Role.ASSOCIATE_EDITOR,
    Role.INQUIRY_OFFICER,
])

@router.get(
    "/stats",
    response_model=DashboardMetricsResponse,
    dependencies=[Depends(allow_chamber_staff)],
    summary="Get Chamber Master Executive Metrics",
)
async def get_chamber_dashboard_stats(db: AsyncSession = Depends(get_db)):
    # 1. Pipeline Counters
    total_enquiries = await db.scalar(select(func.count(Enquiry.id))) or 0
    new_enquiries = await db.scalar(
        select(func.count(Enquiry.id)).where(Enquiry.status == EnquiryStatus.NEW)
    ) or 0
    converted_leads = await db.scalar(
        select(func.count(Enquiry.id)).where(Enquiry.status == EnquiryStatus.CONVERTED_TO_LEAD)
    ) or 0

    total_leads = await db.scalar(select(func.count(Lead.id))) or 0
    retained_cases = await db.scalar(
        select(func.count(Lead.id)).where(Lead.status == LeadStatus.RETAINED)
    ) or 0
    in_litigation_cases = await db.scalar(
        select(func.count(Lead.id)).where(Lead.status == LeadStatus.IN_LITIGATION)
    ) or 0

    # 2. Editorial Counters
    total_articles = await db.scalar(select(func.count(Article.id))) or 0
    published_articles = await db.scalar(
        select(func.count(Article.id)).where(Article.status == ContentStatus.PUBLISHED)
    ) or 0
    draft_articles = await db.scalar(
        select(func.count(Article.id)).where(Article.status == ContentStatus.DRAFT)
    ) or 0
    pending_articles = await db.scalar(
        select(func.count(Article.id)).where(Article.status == ContentStatus.PENDING_REVIEW)
    ) or 0

    # 3. Audience Segmentation Ratio
    indiv_leads = await db.scalar(
        select(func.count(Lead.id)).where(Lead.audience == AudienceSegment.INDIVIDUAL)
    ) or 0
    biz_leads = await db.scalar(
        select(func.count(Lead.id)).where(Lead.audience == AudienceSegment.BUSINESS)
    ) or 0
    
    audience_total = indiv_leads + biz_leads
    indiv_pct = round((indiv_leads / audience_total) * 100, 1) if audience_total > 0 else 0.0
    biz_pct = round((biz_leads / audience_total) * 100, 1) if audience_total > 0 else 0.0

    # 4. Practice Concentration
    lead_practices_res = await db.execute(
        select(Lead.practice_area, func.count(Lead.id))
        .group_by(Lead.practice_area)
        .order_by(desc(func.count(Lead.id)))
    )
    practice_concentration = [
        PracticeAreaStat(practice_area=row[0], count=row[1])
        for row in lead_practices_res.all()
    ]

    # 5. Activity Feed Aggregation
    recent_enquiries_res = await db.execute(
        select(Enquiry).order_by(desc(Enquiry.created_at)).limit(5)
    )
    recent_enquiries = recent_enquiries_res.scalars().all()

    recent_remarks_res = await db.execute(
        select(LeadRemark)
        .options(selectinload(LeadRemark.lead), selectinload(LeadRemark.author))
        .order_by(desc(LeadRemark.created_at))
        .limit(5)
    )
    recent_remarks = recent_remarks_res.scalars().all()

    activity: List[ActivityFeedItem] = []

    for enq in recent_enquiries:
        matter_val = enq.matter_type.value if hasattr(enq.matter_type, "value") else str(enq.matter_type)
        status_val = enq.status.value if hasattr(enq.status, "value") else str(enq.status)
        activity.append(
            ActivityFeedItem(
                id=enq.id,
                type="ENQUIRY_RECEIVED",
                title=f"Web Intake: {enq.full_name}",
                subtitle=f"{matter_val} • Ref: {enq.reference_number}",
                timestamp=enq.created_at,
                badge=status_val,
            )
        )

    for rem in recent_remarks:
        lead_num = rem.lead.lead_number if rem.lead else "Matter"
        author_name = rem.author.full_name if rem.author else "Advocate"
        status_label = f"Upgraded to {rem.next_status.value if hasattr(rem.next_status, 'value') else rem.next_status}" if rem.next_status else "Remark Added"
        activity.append(
            ActivityFeedItem(
                id=rem.id,
                type="LEAD_STATUS_UPGRADED" if rem.next_status else "LEAD_REMARK",
                title=f"{lead_num}: {rem.lead.case_title if rem.lead else 'Litigation Update'}",
                subtitle=f"{author_name}: {rem.remark[:80]}...",
                timestamp=rem.created_at,
                badge=status_label,
            )
        )

    activity.sort(key=lambda x: x.timestamp, reverse=True)

    return DashboardMetricsResponse(
        pipeline=PipelineCounts(
            total_enquiries=total_enquiries,
            new_enquiries=new_enquiries,
            converted_to_leads=converted_leads,
            total_active_leads=total_leads,
            retained_cases=retained_cases,
            in_litigation_cases=in_litigation_cases,
        ),
        editorial=EditorialCounts(
            total_articles=total_articles,
            published=published_articles,
            drafts=draft_articles,
            pending_review=pending_articles,
        ),
        audience=AudienceBreakdown(
            individual_count=indiv_leads,
            business_count=biz_leads,
            individual_pct=indiv_pct,
            business_pct=biz_pct,
        ),
        practice_concentration=practice_concentration,
        recent_activity=activity[:10],
    )