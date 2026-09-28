import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Enum as SQLEnum
from app.db.session import Base
from app.models.enums import EnquiryStatus, MatterType

class Enquiry(Base):
    __tablename__ = "enquiries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    reference_number = Column(String(50), unique=True, index=True, nullable=False)
    
    # Form submission fields
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    
    # Pass enum VALUES to Postgres rather than variable names
    matter_type = Column(
        SQLEnum(
            MatterType,
            name="mattertype",
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        index=True
    )
    summary = Column(Text, nullable=False)
    
    # Chamber triage fields
    status = Column(
        SQLEnum(
            EnquiryStatus,
            name="enquirystatus",
            values_callable=lambda x: [e.value for e in x]
        ),
        default=EnquiryStatus.NEW,
        nullable=False,
        index=True
    )
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)