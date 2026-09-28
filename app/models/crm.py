import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, String, Text, DateTime, Enum as SQLEnum, ForeignKey, Numeric, Integer
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.enums import LeadStatus, LeadPriority, AudienceSegment

class Lead(Base):
    __tablename__ = "leads"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_number = Column(String(50), unique=True, index=True, nullable=False)
    
    # Client Contact
    client_name = Column(String(255), nullable=False)
    client_email = Column(String(255), nullable=False, index=True)
    client_phone = Column(String(50), nullable=False)
    alternate_phone = Column(String(50), nullable=True)
    audience = Column(
        SQLEnum(AudienceSegment, name="audiencesegment", values_callable=lambda x: [e.value for e in x]),
        default=AudienceSegment.INDIVIDUAL,
        nullable=False
    )
    practice_area = Column(String(100), nullable=False, index=True)

    # Matter & Litigation Profile
    case_title = Column(String(255), nullable=False)
    case_description = Column(Text, nullable=False)
    court_forum = Column(String(255), nullable=True)          # e.g., Supreme Court of India, NCLT Delhi
    opposing_party = Column(String(255), nullable=True)
    case_filing_number = Column(String(100), nullable=True)
    claim_value = Column(Numeric(14, 2), nullable=True)
    
    # Ledger Tracking
    status = Column(
        SQLEnum(LeadStatus, name="leadstatus", values_callable=lambda x: [e.value for e in x]),
        default=LeadStatus.INTAKE,
        nullable=False,
        index=True
    )
    priority = Column(
        SQLEnum(LeadPriority, name="leadpriority", values_callable=lambda x: [e.value for e in x]),
        default=LeadPriority.MEDIUM,
        nullable=False,
        index=True
    )

    # Source & Advocate Allocation
    enquiry_id = Column(String, ForeignKey("enquiries.id", ondelete="SET NULL"), unique=True, nullable=True)
    assigned_to_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    remarks = relationship("LeadRemark", back_populates="lead", cascade="all, delete-orphan", order_by="desc(LeadRemark.created_at)")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])

class LeadRemark(Base):
    __tablename__ = "lead_remarks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id = Column(String, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    remark = Column(Text, nullable=False)
    prev_status = Column(
        SQLEnum(LeadStatus, name="leadstatus", values_callable=lambda x: [e.value for e in x]),
        nullable=True
    )
    next_status = Column(
        SQLEnum(LeadStatus, name="leadstatus", values_callable=lambda x: [e.value for e in x]),
        nullable=True
    )
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    lead = relationship("Lead", back_populates="remarks")
    author = relationship("User", foreign_keys=[author_id])