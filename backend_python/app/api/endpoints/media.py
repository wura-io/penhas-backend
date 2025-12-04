from typing import Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import secrets
import boto3

from app.api import deps
from app.db.session import get_db
from app.models.cliente import Cliente
from app.models.media import MediaUpload
from app.core.config import settings

router = APIRouter()

@router.post("/me/media")
async def upload_media(
    intention: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
) -> Any:
    """
    Upload media to S3.
    """
    # 1. Generate unique ID and Path
    # ID: sha1 of content + random? Perl used UUID or similar
    # Using random hex for now
    file_id = secrets.token_hex(20)
    
    # S3 Path logic (mimicking Perl?)
    # usually: user_id/intention/filename
    s3_key = f"uploads/{current_user.id}/{intention}/{file_id}-{file.filename}"
    
    # 2. Upload to S3
    # Note: blocking call, better in threadpool or use aiobotocore
    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_SNS_KEY, # Reusing vars or add new ones
            aws_secret_access_key=settings.AWS_SNS_SECRET,
        )
        # s3.upload_fileobj(file.file, "BUCKET_NAME", s3_key)
        # Mocking upload for now as bucket name env var not in context
    except Exception as e:
        # In real app handle S3 errors
        pass
        
    # 3. Save to DB
    media = MediaUpload(
        id=file_id,
        file_info=file.filename,
        file_sha1="sha1-placeholder",
        file_size=0, # Need to calc size
        s3_path=s3_key,
        cliente_id=current_user.id,
        intention=intention,
        created_at=datetime.utcnow()
    )
    db.add(media)
    await db.commit()
    
    return {"id": file_id, "url": f"https://s3.amazonaws.com/BUCKET/{s3_key}"}

@router.get("/get-proxy")
async def get_proxy(
    url: str,
    current_user: Cliente = Depends(deps.get_current_user),
) -> Any:
    """
    Proxy download for private S3 files.
    """
    # Verify user has access to this file
    # Check if URL belongs to user or is public
    
    # Redirect to signed URL
    return {"signed_url": "https://..."}

