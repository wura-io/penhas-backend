"""
Admin panel endpoints
Port from Perl admin controller
"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api import deps
from app.models.admin import AdminUser
from app.db.session import get_db
from app.helpers import admin as admin_helper

router = APIRouter()


# For now, simple admin check - in production, implement proper admin auth
async def get_current_admin_user() -> AdminUser:
    """Get current admin user - simplified for now"""
    # TODO: Implement proper admin JWT authentication
    admin = AdminUser(id=1, email="admin@penhas.app.br")
    return admin


class NotificationBroadcastRequest(BaseModel):
    """Notification broadcast request"""
    title: str
    content: str
    notification_type: str = "general"
    segment_id: int | None = None


class ScheduleDeletionRequest(BaseModel):
    """Schedule user deletion request"""
    days: int = 15


class ReviewSuggestionRequest(BaseModel):
    """Review support point suggestion"""
    action: str  # 'approve' or 'reject'
    reason: str | None = None


@router.get("/dashboard")
async def admin_dashboard(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin_user)
) -> Any:
    """
    Get admin dashboard statistics
    Matches Perl GET /admin
    """
    stats = await admin_helper.get_dashboard_stats(db=db)
    return stats


@router.get("/users")
async def search_users(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin_user),
    query: str | None = None,
    limit: int = 50,
    offset: int = 0
) -> Any:
    """
    Search users
    Matches Perl GET /admin/users
    """
    result = await admin_helper.search_users(
        db=db,
        query=query,
        limit=limit,
        offset=offset
    )
    return result


@router.get("/users/{user_id}")
async def get_user_details(
    *,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin_user),
    user_id: int
) -> Any:
    """
    Get user details
    Matches Perl GET /admin/user/:id
    """
    result = await admin_helper.get_user_details(
        db=db,
        user_id=user_id
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result)
    
    return result


@router.post("/users/{user_id}/schedule-delete")
async def schedule_user_deletion(
    *,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin_user),
    user_id: int,
    deletion_data: ScheduleDeletionRequest
) -> Any:
    """
    Schedule user for deletion
    Matches Perl POST /admin/schedule-delete
    """
    result = await admin_helper.schedule_user_deletion(
        db=db,
        user_id=user_id,
        days=deletion_data.days
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result)
    
    return result


@router.post("/users/{user_id}/cancel-delete")
async def cancel_user_deletion(
    *,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin_user),
    user_id: int
) -> Any:
    """
    Cancel scheduled user deletion
    Matches Perl GET /admin/unschedule-delete
    """
    result = await admin_helper.cancel_user_deletion(
        db=db,
        user_id=user_id
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result)
    
    return result


@router.post("/notifications/broadcast")
async def create_notification_broadcast(
    *,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin_user),
    notification_data: NotificationBroadcastRequest
) -> Any:
    """
    Create notification broadcast
    Matches Perl POST /admin/add-notification
    """
    result = await admin_helper.create_notification_broadcast(
        db=db,
        admin_user=admin,
        title=notification_data.title,
        content=notification_data.content,
        notification_type=notification_data.notification_type,
        segment_id=notification_data.segment_id
    )
    
    return result


@router.get("/ponto-apoio/suggestions")
async def list_ponto_apoio_suggestions(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin_user),
    status: str | None = None,
    limit: int = 50,
    offset: int = 0
) -> Any:
    """
    List support point suggestions
    Matches Perl GET /admin/ponto-apoio-sugg
    """
    result = await admin_helper.list_ponto_apoio_suggestions(
        db=db,
        status=status,
        limit=limit,
        offset=offset
    )
    return result


@router.post("/ponto-apoio/suggestions/{suggestion_id}/review")
async def review_ponto_apoio_suggestion(
    *,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin_user),
    suggestion_id: int,
    review_data: ReviewSuggestionRequest
) -> Any:
    """
    Review (approve/reject) support point suggestion
    Matches Perl POST /admin/analisar-sugestao-ponto-apoio
    """
    if review_data.action == "approve":
        result = await admin_helper.approve_ponto_apoio_suggestion(
            db=db,
            suggestion_id=suggestion_id,
            admin_user=admin
        )
    elif review_data.action == "reject":
        result = await admin_helper.reject_ponto_apoio_suggestion(
            db=db,
            suggestion_id=suggestion_id,
            admin_user=admin,
            reason=review_data.reason
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Must be 'approve' or 'reject'")
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result)
    
    return result


@router.get("/support-chats")
async def list_open_support_chats(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin_user),
    limit: int = 50,
    offset: int = 0
) -> Any:
    """
    List open support chats
    Matches Perl admin support chat list
    """
    from app.helpers import chat_support as chat_support_helper
    
    result = await chat_support_helper.list_open_support_chats(
        db=db,
        limit=limit,
        offset=offset
    )
    return result


@router.post("/support-chats/{chat_id}/close")
async def close_support_chat(
    *,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin_user),
    chat_id: int
) -> Any:
    """
    Close support chat
    Matches Perl admin close chat
    """
    from app.helpers import chat_support as chat_support_helper
    
    result = await chat_support_helper.close_support_chat(
        db=db,
        chat_id=chat_id,
        admin_user=admin
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result)
    
    return result

