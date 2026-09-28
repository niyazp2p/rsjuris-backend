import re
import math
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import desc

from app.db.session import get_db
from app.models.cms import Article, Asset
from app.models.user import User
from app.models.enums import ContentStatus, Role, AudienceSegment
from app.schemas.article import (
    ArticleCreate,
    ArticleUpdate,
    ArticleResponse,
    ArticleListItem,
    ArticleStatusUpdate,
)
from app.api.deps import RequireRole, get_current_user
from app.core.cloudinary import delete_cloudinary_asset

router = APIRouter(prefix="/articles", tags=["Articles & Publications CMS"])

# Access Rules
allow_editors = RequireRole([Role.SUPER_ADMIN, Role.SENIOR_PARTNER, Role.ASSOCIATE_EDITOR])
allow_publishers = RequireRole([Role.SUPER_ADMIN, Role.SENIOR_PARTNER])

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")

def calculate_reading_time(content: str) -> int:
    words = len(re.findall(r"\w+", content))
    return max(1, math.ceil(words / 200))

# -----------------------------------------------------------------------------
# 1. PUBLIC ENDPOINTS (Consumed by Next.js Articles/page.tsx)
# -----------------------------------------------------------------------------
@router.get("/feed", response_model=List[ArticleListItem], summary="Public Published Articles Feed")
async def get_public_feed(
    practice_area: Optional[str] = Query(None),
    audience: Optional[AudienceSegment] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(12, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Article)
        .options(selectinload(Article.author))
        .where(Article.status == ContentStatus.PUBLISHED)
        .order_by(desc(Article.published_at))
    )

    if practice_area:
        query = query.where(Article.practice_area.ilike(f"%{practice_area}%"))
    if audience:
        query = query.where(Article.target_audience == audience)

    result = await db.execute(query.offset(skip).limit(limit))
    articles = result.scalars().all()

    items = []
    for art in articles:
        items.append(
            ArticleListItem(
                id=art.id,
                slug=art.slug,
                title=art.title,
                summary=art.summary,
                cover_image_url=art.cover_image_url,
                practice_area=art.practice_area,
                target_audience=art.target_audience,
                status=art.status,
                reading_time_min=art.reading_time_min,
                author_name=art.author.full_name if art.author else "RS Juris Editorial Board",
                published_at=art.published_at,
                created_at=art.created_at,
            )
        )
    return items

@router.get("/feed/{slug}", response_model=ArticleResponse, summary="Public Single Article by Slug")
async def get_public_article_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Article)
        .options(selectinload(Article.author), selectinload(Article.media_assets))
        .where(Article.slug == slug, Article.status == ContentStatus.PUBLISHED)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found or not yet published")
    return article

# -----------------------------------------------------------------------------
# 2. ADMIN CMS ENDPOINTS (Drafting, Editing, Publishing)
# -----------------------------------------------------------------------------
@router.get("/admin", response_model=List[ArticleListItem], dependencies=[Depends(allow_editors)])
async def list_admin_articles(
    status_filter: Optional[ContentStatus] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Article).options(selectinload(Article.author)).order_by(desc(Article.updated_at))

    if status_filter:
        query = query.where(Article.status == status_filter)
    if search:
        query = query.where(Article.title.ilike(f"%{search}%") | Article.summary.ilike(f"%{search}%"))

    result = await db.execute(query.offset(skip).limit(limit))
    articles = result.scalars().all()

    return [
        ArticleListItem(
            id=art.id,
            slug=art.slug,
            title=art.title,
            summary=art.summary,
            cover_image_url=art.cover_image_url,
            practice_area=art.practice_area,
            target_audience=art.target_audience,
            status=art.status,
            reading_time_min=art.reading_time_min,
            author_name=art.author.full_name if art.author else "Unknown",
            published_at=art.published_at,
            created_at=art.created_at,
        )
        for art in articles
    ]

@router.post("/admin", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(allow_editors)])
async def create_article(
    payload: ArticleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    base_slug = payload.slug or slugify(payload.title)
    unique_slug = base_slug
    
    # Ensure slug uniqueness
    counter = 1
    while True:
        existing = await db.execute(select(Article).where(Article.slug == unique_slug))
        if not existing.scalar_one_or_none():
            break
        unique_slug = f"{base_slug}-{counter}"
        counter += 1

    reading_time = calculate_reading_time(payload.content)

    published_timestamp = None
    if payload.status == ContentStatus.PUBLISHED:
        # Only Partners and Admins can create in PUBLISHED state directly
        if current_user.role not in [Role.SUPER_ADMIN, Role.SENIOR_PARTNER]:
            payload.status = ContentStatus.PENDING_REVIEW
        else:
            published_timestamp = datetime.utcnow()

    article = Article(
        slug=unique_slug,
        title=payload.title,
        summary=payload.summary,
        content=payload.content,
        cover_image_url=payload.cover_image_url,
        cover_public_id=payload.cover_public_id,
        practice_area=payload.practice_area,
        target_audience=payload.target_audience,
        status=payload.status,
        reading_time_min=reading_time,
        meta_title=payload.meta_title or payload.title,
        meta_description=payload.meta_description or payload.summary[:155],
        canonical_url=payload.canonical_url,
        author_id=current_user.id,
        published_at=published_timestamp,
    )
    db.add(article)
    await db.commit()

    res = await db.execute(
        select(Article)
        .options(selectinload(Article.author), selectinload(Article.media_assets))
        .where(Article.id == article.id)
    )
    return res.scalar_one()

@router.get("/admin/{article_id}", response_model=ArticleResponse, dependencies=[Depends(allow_editors)])
async def get_admin_article(
    article_id: str,
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Article)
        .options(selectinload(Article.author), selectinload(Article.media_assets))
        .where(Article.id == article_id)
    )
    article = res.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@router.patch("/admin/{article_id}", response_model=ArticleResponse, dependencies=[Depends(allow_editors)])
async def update_article(
    article_id: str,
    payload: ArticleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Article)
        .options(selectinload(Article.author), selectinload(Article.media_assets))
        .where(Article.id == article_id)
    )
    article = res.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    update_data = payload.model_dump(exclude_unset=True)

    if "content" in update_data:
        article.reading_time_min = calculate_reading_time(update_data["content"])

    if "status" in update_data and update_data["status"] == ContentStatus.PUBLISHED:
        if current_user.role not in [Role.SUPER_ADMIN, Role.SENIOR_PARTNER]:
            raise HTTPException(status_code=403, detail="Only Partners or Admins can publish articles")
        if not article.published_at:
            article.published_at = datetime.utcnow()

    for k, v in update_data.items():
        setattr(article, k, v)

    await db.commit()
    await db.refresh(article)
    return article

@router.patch("/admin/{article_id}/status", response_model=ArticleResponse, dependencies=[Depends(allow_publishers)])
async def update_article_status(
    article_id: str,
    payload: ArticleStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Article)
        .options(selectinload(Article.author), selectinload(Article.media_assets))
        .where(Article.id == article_id)
    )
    article = res.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    article.status = payload.status
    if payload.status == ContentStatus.PUBLISHED and not article.published_at:
        article.published_at = datetime.utcnow()

    await db.commit()
    await db.refresh(article)
    return article

@router.delete("/admin/{article_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(allow_publishers)])
async def delete_article(
    article_id: str,
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Article)
        .options(selectinload(Article.media_assets))
        .where(Article.id == article_id)
    )
    article = res.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Clean up Cloudinary cover image if exists
    if article.cover_public_id:
        delete_cloudinary_asset(article.cover_public_id, "image")

    # Clean up associated assets from Cloudinary
    for asset in article.media_assets:
        delete_cloudinary_asset(asset.public_id, asset.resource_type)

    await db.delete(article)
    await db.commit()
    return None