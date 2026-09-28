from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel

class PipelineCounts(BaseModel):
    total_enquiries: int
    new_enquiries: int
    converted_to_leads: int
    total_active_leads: int
    retained_cases: int
    in_litigation_cases: int

class EditorialCounts(BaseModel):
    total_articles: int
    published: int
    drafts: int
    pending_review: int

class AudienceBreakdown(BaseModel):
    individual_count: int
    business_count: int
    individual_pct: float
    business_pct: float

class PracticeAreaStat(BaseModel):
    practice_area: str
    count: int

class ActivityFeedItem(BaseModel):
    id: str
    type: str  # "ENQUIRY_RECEIVED", "LEAD_STATUS_UPGRADED", "ARTICLE_PUBLISHED"
    title: str
    subtitle: str
    timestamp: datetime
    badge: Optional[str] = None

class DashboardMetricsResponse(BaseModel):
    pipeline: PipelineCounts
    editorial: EditorialCounts
    audience: AudienceBreakdown
    practice_concentration: List[PracticeAreaStat]
    recent_activity: List[ActivityFeedItem]