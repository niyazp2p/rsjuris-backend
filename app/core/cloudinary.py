import time
import cloudinary
import cloudinary.uploader
import cloudinary.utils
from fastapi import UploadFile, HTTPException
from app.core.config import settings
from app.models.enums import AssetType

# Configure Cloudinary SDK
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)

def generate_signed_upload_params(folder: str = "rsjuris/articles"):
    """
    Generates a secure timestamp and signature for client-side direct uploads.
    """
    timestamp = int(time.time())
    params_to_sign = {
        "timestamp": timestamp,
        "folder": folder,
    }
    signature = cloudinary.utils.api_sign_request(
        params_to_sign,
        settings.CLOUDINARY_API_SECRET
    )
    return {
        "signature": signature,
        "timestamp": timestamp,
        "cloud_name": settings.CLOUDINARY_CLOUD_NAME,
        "api_key": settings.CLOUDINARY_API_KEY,
        "folder": folder,
    }

async def upload_file_stream(file: UploadFile, folder: str = "rsjuris/articles") -> dict:
    """
    Direct server-side binary upload handler with automatic mime-type inspection.
    """
    content_type = file.content_type or ""
    
    # Classify asset resource type
    if content_type.startswith("image/"):
        resource_type = "image"
        asset_type = AssetType.IMAGE
    elif content_type.startswith("video/"):
        resource_type = "video"
        asset_type = AssetType.VIDEO
    elif content_type == "application/pdf":
        resource_type = "raw"
        asset_type = AssetType.DOCUMENT_PDF
    elif "wordprocessingml" in content_type or content_type == "application/msword":
        resource_type = "raw"
        asset_type = AssetType.DOCUMENT_DOCX
    else:
        resource_type = "auto"
        asset_type = AssetType.DOCUMENT_PDF

    try:
        file_bytes = await file.read()
        file_size = len(file_bytes)

        upload_result = cloudinary.uploader.upload(
            file_bytes,
            folder=folder,
            resource_type=resource_type,
            use_filename=True,
            unique_filename=True
        )

        return {
            "name": file.filename,
            "public_id": upload_result["public_id"],
            "secure_url": upload_result["secure_url"],
            "resource_type": resource_type,
            "format": upload_result.get("format") or file.filename.split(".")[-1],
            "file_size": file_size,
            "asset_type": asset_type,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cloudinary upload failed: {str(e)}")

def delete_cloudinary_asset(public_id: str, resource_type: str = "image"):
    try:
        cloudinary.uploader.destroy(public_id, resource_type=resource_type)
    except Exception as e:
        print(f"Warning: Cloudinary deletion failed for {public_id}: {e}")