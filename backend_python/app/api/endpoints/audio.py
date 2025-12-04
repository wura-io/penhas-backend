from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Body, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api import deps
from app.models.cliente import Cliente
from app.db.session import get_db
from app.helpers import audio as audio_helper

router = APIRouter()


class CreateAudioEventRequest(BaseModel):
    """Create audio event request"""
    event_type: str = "general"


@router.post("/events")
async def create_audio_event(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    event_data: CreateAudioEventRequest
) -> Any:
    """
    Create new audio event
    Matches Perl audio event creation
    """
    result = await audio_helper.create_audio_event(
        db=db,
        user=current_user,
        event_type=event_data.event_type
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)
    
    return result


@router.post("/upload")
async def upload_audio(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    event_id: int = Form(...),
    audio_file: UploadFile = File(...),
    duration_seconds: float | None = Form(None),
    waveform_data: str | None = Form(None)
) -> Any:
    """
    Upload audio file
    Matches Perl POST /me/audios
    """
    # Read audio content
    audio_content = await audio_file.read()
    
    # Validate file type
    if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="Invalid file type. Must be audio file.")
    
    result = await audio_helper.upload_audio(
        db=db,
        user=current_user,
        event_id=event_id,
        audio_content=audio_content,
        duration_seconds=duration_seconds,
        waveform_data=waveform_data
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)
    
    return result


@router.get("/events")
async def list_audio_events(
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    limit: int = 50,
    offset: int = 0
) -> Any:
    """
    List user's audio events
    Matches Perl GET /me/audios
    """
    result = await audio_helper.list_audio_events(
        db=db,
        user=current_user,
        limit=limit,
        offset=offset
    )
    return result


@router.get("/events/{event_id}")
async def get_audio_event_details(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    event_id: int
) -> Any:
    """
    Get audio event details
    Matches Perl GET /me/audios/:event_id
    """
    result = await audio_helper.get_audio_event_details(
        db=db,
        user=current_user,
        event_id=event_id
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result)
    
    return result


@router.delete("/events/{event_id}")
async def delete_audio_event(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    event_id: int
) -> Any:
    """
    Delete audio event and all files
    Matches Perl DELETE /me/audios/:event_id
    """
    result = await audio_helper.delete_audio_event(
        db=db,
        user=current_user,
        event_id=event_id
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result)
    
    return result


@router.get("/download/{audio_id}")
async def get_audio_download_url(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    audio_id: int
) -> Any:
    """
    Get presigned URL for audio download
    Matches Perl GET /me/audios/:event_id/download
    """
    result = await audio_helper.get_audio_download_url(
        db=db,
        user=current_user,
        audio_id=audio_id
    )
    
    if "error" in result:
        raise HTTPException(status_code=403, detail=result)
    
    return result


@router.post("/request-access/{audio_id}")
async def request_audio_access(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    audio_id: int,
    reason: str | None = Body(None, embed=True)
) -> Any:
    """
    Request access to another user's audio
    Matches Perl POST /me/audios/:event_id/request-access
    """
    result = await audio_helper.request_audio_access(
        db=db,
        requester=current_user,
        audio_id=audio_id,
        reason=reason
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)
    
    return result

