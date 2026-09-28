from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.enums import EnquiryStatus, MatterType

# Public Form Submission Schema
class EnquiryCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: str = Field(..., min_length=7, max_length=30)
    email: EmailStr
    matter_type: MatterType
    summary: str = Field(..., min_length=15)

    model_config = ConfigDict(use_enum_values=True)

# Admin Status Update Schema
class EnquiryStatusUpdate(BaseModel):
    status: EnquiryStatus

    model_config = ConfigDict(use_enum_values=True)

# Admin Response Schema
class EnquiryResponse(BaseModel):
    id: str
    reference_number: str
    full_name: str
    phone: str
    email: EmailStr
    matter_type: MatterType
    summary: str
    status: EnquiryStatus
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

# Public Confirmation Schema
class EnquiryPublicConfirmation(BaseModel):
    reference_number: str
    message: str
    received_at: datetime