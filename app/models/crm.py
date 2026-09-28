import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Numeric,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.enums import LeadStatus, LeadPriority, AudienceSegment

class Lead(Base):
    __tablename__ = "leads"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_number = Column(String(100), unique=True, index=True, nullable=False)
    
    # Client Contact Profile
    client_name = Column(String(255), nullable=False)
    client_email = Column(String(255), nullable=False, index=True)
    client_phone = Column(String(50), nullable=False)
    alternate_phone = Column(String(50), nullable=True)
    audience = Column(
        SQLEnum(
            AudienceSegment, 
            name="audiencesegment", 
            values_callable=lambda x: [e.value for e in x]
        ),
        default=AudienceSegment.INDIVIDUAL,
        nullable=False,
    )
    practice_area = Column(String(150), nullable=False, index=True)

    # Matter & Litigation Brief
    case_title = Column(String(255), nullable=False)
    case_description = Column(Text, nullable=False)
    court_forum = Column(String(150), nullable=True)          # e.g., High Court of Delhi, NCLT Principal Bench
    opposing_party = Column(String(255), nullable=True)
    case_filing_number = Column(String(100), nullable=True)
    claim_value = Column(Numeric(14, 2), nullable=True)
    
    # Case Ledger Tracking
    status = Column(
        SQLEnum(
            LeadStatus, 
            name="leadstatus", 
            values_callable=lambda x: [e.value for e in x]
        ),
        default=LeadStatus.INTAKE,
        nullable=False,
        index=True,
    )
    priority = Column(
        SQLEnum(
            LeadPriority, 
            name="leadpriority", 
            values_callable=lambda x: [e.value for e in x]
        ),
        default=LeadPriority.MEDIUM,
        nullable=False,
        index=True,
    )

    # Source & Advocate Allocation
    enquiry_id = Column(String, ForeignKey("enquiries.id", ondelete="SET NULL"), unique=True, nullable=True)
    assigned_to_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # ORM Relationships
    enquiry = relationship("Enquiry", back_populates="lead", uselist=False)
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    remarks = relationship(
        "LeadRemark", 
        back_populates="lead", 
        cascade="all, delete-orphan", 
        order_by="desc(LeadRemark.created_at)"
    )
    documents = relationship(
        "LeadDocument", 
        back_populates="lead", 
        cascade="all, delete-orphan",
        order_by="desc(LeadDocument.created_at)"
    )


class LeadRemark(Base):
    __tablename__ = "lead_remarks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id = Column(String, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    remark = Column(Text, nullable=False)
    prev_status = Column(
        SQLEnum(
            LeadStatus, 
            name="leadstatus", 
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=True,
    )
    next_status = Column(
        SQLEnum(
            LeadStatus, 
            name="leadstatus", 
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=True,
    )
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # ORM Relationships
    lead = relationship("Lead", back_populates="remarks")
    author = relationship("User", foreign_keys=[author_id])

    @property
    def author_name(self) -> str:
        """
        Dynamically derives the full name of the authoring chamber advocate.
        Satisfies Pydantic schemas (LeadRemarkResponse) during serialization.
        """
        if self.author and hasattr(self.author, "full_name"):
            return self.author.full_name
        return "Chamber Advocate"


class LeadDocument(Base):
    __tablename__ = "lead_documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id = Column(String, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    public_id = Column(String(255), nullable=False)            # Cloudinary public_id
    secure_url = Column(String(500), nullable=False)           # Cloudinary HTTPS URL
    format = Column(String(50), nullable=False)                # pdf, docx, etc.
    file_size = Column(Integer, nullable=False)                # Size in bytes
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # ORM Relationships
    lead = relationship("Lead", back_populates="documents")