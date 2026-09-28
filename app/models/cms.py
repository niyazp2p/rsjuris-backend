import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Enum as SQLEnum, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.enums import ContentStatus, AssetType, AudienceSegment

class Article(Base):
    __tablename__ = "articles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    slug = Column(String(255), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    content = Column(Text, nullable=False)  # Rich HTML or Serialized Block JSON
    
    # Hero/Cover Media
    cover_image_url = Column(String(500), nullable=True)
    cover_public_id = Column(String(255), nullable=True)
    
    # Categorization & Targeting
    practice_area = Column(String(100), nullable=False, index=True)
    target_audience = Column(
        SQLEnum(AudienceSegment, name="audiencesegment", values_callable=lambda x: [e.value for e in x]),
        default=AudienceSegment.BUSINESS,
        nullable=False
    )
    status = Column(
        SQLEnum(ContentStatus, name="contentstatus", values_callable=lambda x: [e.value for e in x]),
        default=ContentStatus.DRAFT,
        nullable=False,
        index=True
    )
    reading_time_min = Column(Integer, default=3, nullable=False)

    # SEO Metadata
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(String(500), nullable=True)
    canonical_url = Column(String(500), nullable=True)

    # Attribution & Lifecycle
    author_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    published_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    author = relationship("User", foreign_keys=[author_id])
    media_assets = relationship("Asset", back_populates="article", cascade="all, delete-orphan")

class Asset(Base):
    __tablename__ = "assets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    public_id = Column(String(255), unique=True, nullable=False)  # Cloudinary public_id
    secure_url = Column(String(500), nullable=False)              # Cloudinary HTTPS URL
    resource_type = Column(String(50), nullable=False)            # "image", "video", "raw"
    format = Column(String(50), nullable=False)                   # "webp", "pdf", "mp4", etc.
    file_size = Column(Integer, nullable=False)                   # Size in bytes
    type = Column(
        SQLEnum(AssetType, name="assettype", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )

    article_id = Column(String, ForeignKey("articles.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    article = relationship("Article", back_populates="media_assets")