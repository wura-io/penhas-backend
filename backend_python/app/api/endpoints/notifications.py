from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api import deps
from app.models.cliente import Cliente
from app.db.session import get_db
from app.helpers import notifications as notifications_helper

router = APIRouter()


@router.get("/count")
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user)
) -> Any:
    """
    Get unread notification count
    Matches Perl GET /me/unread-notif-count
    """
    count = await notifications_helper.get_unread_notification_count(
        db=db,
        user=current_user
    )
    return {"count": count}


@router.get("/")
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    limit: int = 50,
    offset: int = 0
) -> Any:
    """
    List user notifications
    Matches Perl GET /me/notifications
    """
    result = await notifications_helper.list_notifications(
        db=db,
        user=current_user,
        limit=limit,
        offset=offset
    )
    return result


@router.post("/{notification_id}/read")
async def mark_as_read(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    notification_id: int
) -> Any:
    """
    Mark notification as read
    Matches Perl POST /me/notifications/:id/read
    """
    result = await notifications_helper.mark_notification_as_read(
        db=db,
        user=current_user,
        notification_id=notification_id
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result)
    
    return result


@router.post("/read-all")
async def mark_all_as_read(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user)
) -> Any:
    """
    Mark all notifications as read
    Matches Perl POST /me/notifications/read-all
    """
    result = await notifications_helper.mark_all_notifications_as_read(
        db=db,
        user=current_user
    )
    return result

