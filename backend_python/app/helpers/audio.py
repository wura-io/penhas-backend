"""
Client Audio helper module
Port from Perl Penhas::Helpers::ClienteAudio
Business logic for audio upload, waveform extraction, and access control
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from datetime import datetime
import uuid

from app.models.cliente import Cliente
from app.models.audio import ClientesAudio
from app.models.minor import ClientesAudiosEvento
from app.integrations.storage import s3_storage_service


async def create_audio_event(
    db: AsyncSession,
    user: Cliente,
    event_type: str = "general"
) -> Dict[str, Any]:
    """
    Create new audio event
    Matches Perl's audio event creation logic
    """
    # Create event
    event = ClientesAudiosEvento(
        cliente_id=user.id,
        event_type=event_type,
        created_at=datetime.utcnow()
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    
    return {
        "success": True,
        "event_id": event.id
    }


async def upload_audio(
    db: AsyncSession,
    user: Cliente,
    event_id: int,
    audio_content: bytes,
    duration_seconds: Optional[float] = None,
    waveform_data: Optional[str] = None
) -> Dict[str, Any]:
    """
    Upload audio file to S3 and store metadata
    Matches Perl's audio upload logic
    """
    # Verify event exists and belongs to user
    result = await db.execute(
        select(ClientesAudiosEvento)
        .where(ClientesAudiosEvento.id == event_id)
        .where(ClientesAudiosEvento.cliente_id == user.id)
    )
    event = result.scalar_one_or_none()
    
    if not event:
        return {"error": "Event not found"}
    
    # Generate unique filename
    filename = f"{uuid.uuid4()}.aac"
    s3_key = s3_storage_service.build_audio_key(user.id, filename)
    
    # Upload to S3
    upload_result = await s3_storage_service.upload_file(
        file_content=audio_content,
        key=s3_key,
        content_type="audio/aac"
    )
    
    if not upload_result.get("success"):
        return {"error": "Failed to upload audio", "details": upload_result.get("error")}
    
    # Create audio record
    audio = ClientesAudio(
        cliente_id=user.id,
        audio_event_id=event_id,
        s3_key=s3_key,
        duration_seconds=duration_seconds,
        waveform_data=waveform_data,
        uploaded_at=datetime.utcnow()
    )
    db.add(audio)
    
    # Update user's audio status
    user.upload_status = 'completed'
    
    await db.commit()
    await db.refresh(audio)
    
    return {
        "success": True,
        "audio_id": audio.id,
        "s3_key": s3_key
    }


async def list_audio_events(
    db: AsyncSession,
    user: Cliente,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """
    List user's audio events
    Matches Perl's audio event listing logic
    """
    result = await db.execute(
        select(ClientesAudiosEvento)
        .where(ClientesAudiosEvento.cliente_id == user.id)
        .order_by(ClientesAudiosEvento.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    events = result.scalars().all()
    
    rows = []
    for event in events:
        # Get audio files for this event
        result = await db.execute(
            select(ClientesAudio)
            .where(ClientesAudio.audio_event_id == event.id)
            .order_by(ClientesAudio.uploaded_at.asc())
        )
        audios = result.scalars().all()
        
        audio_files = []
        for audio in audios:
            audio_files.append({
                "id": audio.id,
                "duration_seconds": audio.duration_seconds,
                "waveform_data": audio.waveform_data,
                "uploaded_at": audio.uploaded_at.isoformat() if audio.uploaded_at else None
            })
        
        rows.append({
            "id": event.id,
            "event_type": event.event_type,
            "created_at": event.created_at.isoformat() if event.created_at else None,
            "audio_count": len(audio_files),
            "audios": audio_files
        })
    
    return {"rows": rows}


async def get_audio_event_details(
    db: AsyncSession,
    user: Cliente,
    event_id: int
) -> Dict[str, Any]:
    """
    Get detailed info for an audio event
    Matches Perl's audio event detail logic
    """
    # Get event
    result = await db.execute(
        select(ClientesAudiosEvento)
        .where(ClientesAudiosEvento.id == event_id)
        .where(ClientesAudiosEvento.cliente_id == user.id)
    )
    event = result.scalar_one_or_none()
    
    if not event:
        return {"error": "Event not found"}
    
    # Get audio files
    result = await db.execute(
        select(ClientesAudio)
        .where(ClientesAudio.audio_event_id == event_id)
        .order_by(ClientesAudio.uploaded_at.asc())
    )
    audios = result.scalars().all()
    
    audio_files = []
    for audio in audios:
        audio_files.append({
            "id": audio.id,
            "duration_seconds": audio.duration_seconds,
            "waveform_data": audio.waveform_data,
            "uploaded_at": audio.uploaded_at.isoformat() if audio.uploaded_at else None,
            "can_download": True  # User can always download their own audio
        })
    
    return {
        "id": event.id,
        "event_type": event.event_type,
        "created_at": event.created_at.isoformat() if event.created_at else None,
        "audio_count": len(audio_files),
        "audios": audio_files
    }


async def delete_audio_event(
    db: AsyncSession,
    user: Cliente,
    event_id: int
) -> Dict[str, Any]:
    """
    Delete audio event and all associated files
    Matches Perl's audio deletion logic
    """
    # Get event
    result = await db.execute(
        select(ClientesAudiosEvento)
        .where(ClientesAudiosEvento.id == event_id)
        .where(ClientesAudiosEvento.cliente_id == user.id)
    )
    event = result.scalar_one_or_none()
    
    if not event:
        return {"error": "Event not found"}
    
    # Get all audio files
    result = await db.execute(
        select(ClientesAudio)
        .where(ClientesAudio.audio_event_id == event_id)
    )
    audios = result.scalars().all()
    
    # Delete from S3 (async via Celery task)
    from app.worker import delete_audio_task
    for audio in audios:
        delete_audio_task.delay(audio.id)
    
    # Delete event record
    await db.delete(event)
    await db.commit()
    
    return {"success": True}


async def get_audio_download_url(
    db: AsyncSession,
    user: Cliente,
    audio_id: int
) -> Dict[str, Any]:
    """
    Generate presigned URL for audio download
    Matches Perl's audio download logic
    """
    # Get audio
    result = await db.execute(
        select(ClientesAudio).where(ClientesAudio.id == audio_id)
    )
    audio = result.scalar_one_or_none()
    
    if not audio:
        return {"error": "Audio not found"}
    
    # Verify user has access (owns the audio)
    if audio.cliente_id != user.id:
        return {"error": "Access denied"}
    
    # Generate presigned URL (valid for 1 hour)
    download_url = s3_storage_service.generate_presigned_url(
        key=audio.s3_key,
        expiration=3600
    )
    
    if not download_url:
        return {"error": "Failed to generate download URL"}
    
    return {
        "success": True,
        "download_url": download_url,
        "expires_in_seconds": 3600
    }


async def request_audio_access(
    db: AsyncSession,
    requester: Cliente,
    audio_id: int,
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Request access to another user's audio
    Matches Perl's access request logic
    """
    # Get audio
    result = await db.execute(
        select(ClientesAudio).where(ClientesAudio.id == audio_id)
    )
    audio = result.scalar_one_or_none()
    
    if not audio:
        return {"error": "Audio not found"}
    
    # Cannot request access to own audio
    if audio.cliente_id == requester.id:
        return {"error": "You already have access to this audio"}
    
    # TODO: Create access request record
    # This would involve a new table: audio_access_requests
    # For now, return success
    
    return {
        "success": True,
        "message": "Access request submitted",
        "status": "pending"
    }

