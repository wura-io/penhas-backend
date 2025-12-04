"""
Chat Support helper module
Port from Perl Penhas::Helpers::ChatSupport
Business logic for support chat with admin assistants
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from datetime import datetime

from app.models.cliente import Cliente
from app.models.chat import ChatSupport, ChatSupportMessage
from app.models.admin import AdminUser


async def get_or_create_support_chat(
    db: AsyncSession,
    user: Cliente
) -> Dict[str, Any]:
    """
    Get or create support chat session for user
    Matches Perl's support chat creation logic
    """
    # Check for existing active chat
    result = await db.execute(
        select(ChatSupport)
        .where(ChatSupport.cliente_id == user.id)
        .where(ChatSupport.status == 'active')
        .order_by(ChatSupport.created_at.desc())
    )
    existing_chat = result.scalar_one_or_none()
    
    if existing_chat:
        return {
            "success": True,
            "chat_id": existing_chat.id,
            "exists": True
        }
    
    # Create new support chat
    chat = ChatSupport(
        cliente_id=user.id,
        status='active',
        created_at=datetime.utcnow()
    )
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    
    return {
        "success": True,
        "chat_id": chat.id,
        "exists": False
    }


async def send_support_message(
    db: AsyncSession,
    user: Cliente,
    message_text: str,
    is_admin: bool = False,
    admin_user: Optional[AdminUser] = None
) -> Dict[str, Any]:
    """
    Send message in support chat
    Can be called by user or admin
    """
    # Get or create chat
    chat_result = await get_or_create_support_chat(db, user)
    chat_id = chat_result.get("chat_id")
    
    if not chat_id:
        return {"error": "Failed to get support chat"}
    
    # Create message
    message = ChatSupportMessage(
        chat_support_id=chat_id,
        cliente_id=user.id if not is_admin else None,
        admin_user_id=admin_user.id if admin_user else None,
        message=message_text,
        is_admin=is_admin,
        created_at=datetime.utcnow()
    )
    db.add(message)
    
    # Update chat last activity
    await db.execute(
        update(ChatSupport)
        .where(ChatSupport.id == chat_id)
        .values(last_message_at=datetime.utcnow())
    )
    
    await db.commit()
    await db.refresh(message)
    
    # Update user's sent message count if user sent it
    if not is_admin:
        user.support_chat_messages_sent = (user.support_chat_messages_sent or 0) + 1
        await db.commit()
    
    return {
        "success": True,
        "message_id": message.id,
        "created_at": message.created_at.isoformat()
    }


async def list_support_messages(
    db: AsyncSession,
    user: Cliente,
    limit: int = 100,
    offset: int = 0
) -> Dict[str, Any]:
    """
    List messages in user's support chat
    """
    # Get user's active chat
    result = await db.execute(
        select(ChatSupport)
        .where(ChatSupport.cliente_id == user.id)
        .where(ChatSupport.status == 'active')
        .order_by(ChatSupport.created_at.desc())
    )
    chat = result.scalar_one_or_none()
    
    if not chat:
        return {"rows": []}
    
    # Get messages
    result = await db.execute(
        select(ChatSupportMessage)
        .where(ChatSupportMessage.chat_support_id == chat.id)
        .order_by(ChatSupportMessage.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    messages = result.scalars().all()
    
    rows = []
    for msg in messages:
        rows.append({
            "id": msg.id,
            "message": msg.message,
            "is_admin": msg.is_admin,
            "created_at": msg.created_at.isoformat() if msg.created_at else None
        })
    
    return {"rows": rows}


async def close_support_chat(
    db: AsyncSession,
    chat_id: int,
    admin_user: AdminUser
) -> Dict[str, Any]:
    """
    Close support chat (admin only)
    """
    result = await db.execute(
        update(ChatSupport)
        .where(ChatSupport.id == chat_id)
        .values(
            status='closed',
            closed_at=datetime.utcnow(),
            closed_by_admin_id=admin_user.id
        )
    )
    await db.commit()
    
    if result.rowcount > 0:
        return {"success": True}
    else:
        return {"error": "Chat not found"}


async def list_open_support_chats(
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """
    List open support chats (admin view)
    """
    result = await db.execute(
        select(ChatSupport)
        .where(ChatSupport.status == 'active')
        .order_by(ChatSupport.last_message_at.desc())
        .limit(limit)
        .offset(offset)
    )
    chats = result.scalars().all()
    
    rows = []
    for chat in chats:
        # Get user info
        result = await db.execute(
            select(Cliente).where(Cliente.id == chat.cliente_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Get unread count (messages sent by user after last admin message)
            result = await db.execute(
                select(ChatSupportMessage)
                .where(ChatSupportMessage.chat_support_id == chat.id)
                .where(ChatSupportMessage.is_admin == False)
                .where(ChatSupportMessage.created_at > (chat.last_admin_read_at or datetime.min))
            )
            unread_count = len(result.scalars().all())
            
            rows.append({
                "chat_id": chat.id,
                "user": {
                    "id": user.id,
                    "apelido": user.apelido,
                    "email": user.email
                },
                "last_message_at": chat.last_message_at.isoformat() if chat.last_message_at else None,
                "unread_count": unread_count,
                "created_at": chat.created_at.isoformat() if chat.created_at else None
            })
    
    return {"rows": rows}

