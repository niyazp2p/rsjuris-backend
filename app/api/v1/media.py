from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from app.db.session import get_db
from app.models.cms import Asset
from app.models.enums import Role, AssetType
from app.schemas.article import AssetResponse, AssetConfirmPayload
from app.api.deps import RequireRole
from app.core.cloudinary import (
    generate_signed_upload_params,
    upload_file_stream,
    delete_cloudinary_asset,
)

router = APIRouter(prefix="/media", tags=["Cloudinary Media & Document Vault"])

allow_media_managers = RequireRole([Role.SUPER_ADMIN, Role.SENIOR_PARTNER, Role.ASSOCIATE_EDITOR])

@router.post("/sign", summary="Get Signed Parameters for Direct Browser-to-Cloudinary Upload")
async def get_direct_upload_signature(
    folder: str = Query("rsjuris/articles"),
    current_user = Depends(allow_media_managers),
):
    """
    Returns API Key, Timestamp, and HMAC-SHA1 Signature so the client 
    can upload 50MB+ videos/PDFs directly to Cloudinary without hitting server RAM.
    """
    return generate_signed_upload_params(folder)

@router.post("/upload", response_model=AssetResponse, summary="Direct Server Binary Upload (Images, Videos, PDFs, DOCX)")
async def upload_asset_server_side(
    file: UploadFile = File(...),
    article_id: Optional[str] = Query(None),
    current_user = Depends(allow_media_managers),
    db: AsyncSession = Depends(get_db),
):
    """
    Direct multipart file upload route. Streams file straight to Cloudinary 
    and saves the resulting secure URL and format into PostgreSQL.
    """
    data = await upload_file_stream(file)

    asset = Asset(
        name=data["name"],
        public_id=data["public_id"],
        secure_url=data["secure_url"],
        resource_type=data["resource_type"],
        format=data["format"],
        file_size=data["file_size"],
        type=data["asset_type"],
        article_id=article_id,
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset

@router.post("/confirm", response_model=AssetResponse, summary="Confirm Direct Client Upload")
async def confirm_client_upload(
    payload: AssetConfirmPayload,
    current_user = Depends(allow_media_managers),
    db: AsyncSession = Depends(get_db),
):
    """
    After client finishes direct upload via signed params, it posts the asset 
    metadata here to persist it in PostgreSQL.
    """
    asset = Asset(
        name=payload.name,
        public_id=payload.public_id,
        secure_url=payload.secure_url,
        resource_type=payload.resource_type,
        format=payload.format,
        file_size=payload.file_size,
        type=payload.type,
        article_id=payload.article_id,
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset

@router.get("", response_model=List[AssetResponse], dependencies=[Depends(allow_media_managers)])
async def list_vault_assets(
    type_filter: Optional[AssetType] = Query(None, alias="type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Asset).order_by(desc(Asset.created_at))
    if type_filter:
        query = query.where(Asset.type == type_filter)

    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RequireRole([Role.SUPER_ADMIN, Role.SENIOR_PARTNER]))])
async def delete_vault_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    delete_cloudinary_asset(asset.public_id, asset.resource_type)
    await db.delete(asset)
    await db.commit()
    return None