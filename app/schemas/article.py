from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import ContentStatus, AssetType, AudienceSegment

# Asset Schemas
class AssetResponse(BaseModel):
    id: str
    name: str
    public_id: str
    secure_url: str
    resource_type: str
    format: str
    file_size: int
    type: AssetType
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class AssetConfirmPayload(BaseModel):
    name: str
    public_id: str
    secure_url: str
    resource_type: str
    format: str
    file_size: int
    type: AssetType
    article_id: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True)

# Article Schemas
class ArticleBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=255)
    summary: str = Field(..., min_length=20)
    content: str = Field(..., min_length=50)
    cover_image_url: Optional[str] = None
    cover_public_id: Optional[str] = None
    practice_area: str
    target_audience: AudienceSegment = AudienceSegment.BUSINESS
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    canonical_url: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True)

class ArticleCreate(ArticleBase):
    slug: Optional[str] = None  # If not provided, generated automatically
    status: ContentStatus = ContentStatus.DRAFT

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    cover_image_url: Optional[str] = None
    cover_public_id: Optional[str] = None
    practice_area: Optional[str] = None
    target_audience: Optional[AudienceSegment] = None
    status: Optional[ContentStatus] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    canonical_url: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True)

class ArticleStatusUpdate(BaseModel):
    status: ContentStatus

    model_config = ConfigDict(use_enum_values=True)

class AuthorSnippet(BaseModel):
    id: str
    full_name: str
    designation: str
    avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ArticleResponse(ArticleBase):
    id: str
    slug: str
    status: ContentStatus
    reading_time_min: int
    author_id: str
    author: Optional[AuthorSnippet] = None
    media_assets: List[AssetResponse] = []
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class ArticleListItem(BaseModel):
    id: str
    slug: str
    title: str
    summary: str
    cover_image_url: Optional[str] = None
    practice_area: str
    target_audience: AudienceSegment
    status: ContentStatus
    reading_time_min: int
    author_name: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)