from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.enums import LeadStatus, LeadPriority, AudienceSegment

# Remark Schemas
class LeadRemarkCreate(BaseModel):
    remark: str = Field(..., min_length=2)
    next_status: Optional[LeadStatus] = None

    model_config = ConfigDict(use_enum_values=True)

class LeadRemarkResponse(BaseModel):
    id: str
    lead_id: str
    author_id: str
    author_name: Optional[str] = None
    remark: str
    prev_status: Optional[LeadStatus] = None
    next_status: Optional[LeadStatus] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

# Lead Schemas
class LeadBase(BaseModel):
    client_name: str = Field(..., min_length=2, max_length=255)
    client_email: EmailStr
    client_phone: str = Field(..., min_length=7, max_length=50)
    alternate_phone: Optional[str] = None
    audience: AudienceSegment = AudienceSegment.INDIVIDUAL
    practice_area: str
    case_title: str = Field(..., min_length=3, max_length=255)
    case_description: str = Field(..., min_length=10)
    court_forum: Optional[str] = None
    opposing_party: Optional[str] = None
    case_filing_number: Optional[str] = None
    claim_value: Optional[Decimal] = None
    priority: LeadPriority = LeadPriority.MEDIUM
    assigned_to_id: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True)

class LeadCreate(LeadBase):
    initial_remark: Optional[str] = None

class LeadUpdate(BaseModel):
    client_name: Optional[str] = None
    client_email: Optional[EmailStr] = None
    client_phone: Optional[str] = None
    alternate_phone: Optional[str] = None
    audience: Optional[AudienceSegment] = None
    practice_area: Optional[str] = None
    case_title: Optional[str] = None
    case_description: Optional[str] = None
    court_forum: Optional[str] = None
    opposing_party: Optional[str] = None
    case_filing_number: Optional[str] = None
    claim_value: Optional[Decimal] = None
    status: Optional[LeadStatus] = None
    priority: Optional[LeadPriority] = None
    assigned_to_id: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True)

class LeadResponse(LeadBase):
    id: str
    lead_number: str
    status: LeadStatus
    enquiry_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    remarks: List[LeadRemarkResponse] = []

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

# Convert Enquiry Schema
class ConvertEnquiryPayload(BaseModel):
    case_title: Optional[str] = None
    case_description: Optional[str] = None
    court_forum: Optional[str] = None
    audience: AudienceSegment = AudienceSegment.INDIVIDUAL
    priority: LeadPriority = LeadPriority.MEDIUM
    assigned_to_id: Optional[str] = None
    initial_remark: Optional[str] = "Converted from Web Intake Brief"

    model_config = ConfigDict(use_enum_values=True)