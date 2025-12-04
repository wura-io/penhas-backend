"""
Notifications helper module
Port from Perl Penhas::Helpers::Notifications
Business logic for in-app notifications and push notifications
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from datetime import datetime

from app.models.cliente import Cliente
from app.models.activity import ClientesAppNotification
from app.models.admin import NotificationMessage, NotificationLog
from app.integrations.fcm import fcm_service


async def get_unread_notification_count(
    db: AsyncSession,
    user: Cliente
) -> int:
    """
    Get count of unread notifications for user
    Matches Perl's unread notification count logic
    """
    result = await db.execute(
        select(ClientesAppNotification)
        .where(ClientesAppNotification.cliente_id == user.id)
        .where(ClientesAppNotification.is_read == False)
    )
    notifications = result.scalars().all()
    return len(notifications)


async def list_notifications(
    db: AsyncSession,
    user: Cliente,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """
    List user's notifications
    Matches Perl's notification list logic
    """
    result = await db.execute(
        select(ClientesAppNotification)
        .where(ClientesAppNotification.cliente_id == user.id)
        .order_by(ClientesAppNotification.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    notifications = result.scalars().all()
    
    rows = []
    for notif in notifications:
        rows.append({
            "id": notif.id,
            "title": notif.title,
            "content": notif.content,
            "type": notif.notification_type,
            "is_read": notif.is_read,
            "created_at": notif.created_at.isoformat() if notif.created_at else None,
            "meta": notif.meta
        })
    
    return {"rows": rows}


async def mark_notification_as_read(
    db: AsyncSession,
    user: Cliente,
    notification_id: int
) -> Dict[str, Any]:
    """
    Mark notification as read
    Matches Perl's mark_as_read logic
    """
    result = await db.execute(
        update(ClientesAppNotification)
        .where(ClientesAppNotification.id == notification_id)
        .where(ClientesAppNotification.cliente_id == user.id)
        .values(
            is_read=True,
            read_at=datetime.utcnow()
        )
    )
    await db.commit()
    
    if result.rowcount > 0:
        return {"success": True}
    else:
        return {"error": "Notification not found"}


async def mark_all_notifications_as_read(
    db: AsyncSession,
    user: Cliente
) -> Dict[str, Any]:
    """
    Mark all notifications as read
    Matches Perl's mark_all_as_read logic
    """
    await db.execute(
        update(ClientesAppNotification)
        .where(ClientesAppNotification.cliente_id == user.id)
        .where(ClientesAppNotification.is_read == False)
        .values(
            is_read=True,
            read_at=datetime.utcnow()
        )
    )
    await db.commit()
    
    return {"success": True}


async def create_notification(
    db: AsyncSession,
    cliente_id: int,
    title: str,
    content: str,
    notification_type: str = "general",
    meta: Optional[Dict[str, Any]] = None,
    send_push: bool = True
) -> Dict[str, Any]:
    """
    Create in-app notification for user
    Optionally send push notification
    
    Args:
        cliente_id: User ID
        title: Notification title
        content: Notification content
        notification_type: Type (general, alert, message, etc.)
        meta: Additional metadata
        send_push: Whether to send push notification
    """
    # Create in-app notification
    notif = ClientesAppNotification(
        cliente_id=cliente_id,
        title=title,
        content=content,
        notification_type=notification_type,
        meta=meta,
        is_read=False,
        created_at=datetime.utcnow()
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)
    
    # Send push notification if requested
    if send_push:
        # TODO: Get user's FCM token from database
        # For now, skip push notification
        pass
    
    return {
        "success": True,
        "notification_id": notif.id
    }


async def send_push_notification_to_user(
    db: AsyncSession,
    cliente_id: int,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Send push notification to specific user
    Matches Perl's push notification logic
    """
    # Get user
    result = await db.execute(
        select(Cliente).where(Cliente.id == cliente_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        return {"error": "User not found"}
    
    # TODO: Get user's FCM tokens from app_activity or similar table
    # For now, return success without actually sending
    
    # fcm_tokens = user.fcm_tokens  # Need to implement token storage
    # if fcm_tokens:
    #     result = await fcm_service.send_notification(
    #         device_tokens=fcm_tokens,
    #         title=title,
    #         body=body,
    #         data=data
    #     )
    #     return result
    
    return {
        "success": False,
        "error": "FCM token not available for user"
    }


async def send_broadcast_notification(
    db: AsyncSession,
    notification_message_id: int
) -> Dict[str, Any]:
    """
    Send broadcast notification to users in a segment
    Called from Celery task
    """
    # Get notification message
    result = await db.execute(
        select(NotificationMessage).where(NotificationMessage.id == notification_message_id)
    )
    notif_message = result.scalar_one_or_none()
    
    if not notif_message:
        return {"error": "Notification message not found"}
    
    # Get target users based on segment
    # TODO: Implement segment filtering logic
    result = await db.execute(
        select(Cliente).where(Cliente.active == True)
    )
    users = result.scalars().all()
    
    sent_count = 0
    failed_count = 0
    
    for user in users:
        # Create in-app notification
        try:
            await create_notification(
                db=db,
                cliente_id=user.id,
                title=notif_message.title,
                content=notif_message.content,
                notification_type=notif_message.notification_type or "broadcast",
                send_push=True
            )
            sent_count += 1
        except Exception as e:
            print(f"Error sending notification to user {user.id}: {e}")
            failed_count += 1
    
    return {
        "success": True,
        "sent_count": sent_count,
        "failed_count": failed_count
    }

