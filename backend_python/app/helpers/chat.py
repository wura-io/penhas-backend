"""
Chat helper module
Port from Perl Penhas::Helpers::Chat
Business logic for private chat between users
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, delete
from datetime import datetime

from app.models.cliente import Cliente
from app.models.chat import ChatSupport, ChatSupportMessage
from app.models.private_chat import PrivateChatSessionMetadata


async def create_chat_session(
    db: AsyncSession,
    user: Cliente,
    other_user_id: int
) -> Dict[str, Any]:
    """
    Create or get existing chat session between two users
    Matches Perl's chat session creation logic
    """
    # Check if other user exists and is not blocked
    result = await db.execute(
        select(Cliente).where(Cliente.id == other_user_id)
    )
    other_user = result.scalar_one_or_none()
    
    if not other_user:
        return {"error": "User not found"}
    
    # Check for existing session
    result = await db.execute(
        select(PrivateChatSessionMetadata)
        .where(
            or_(
                and_(
                    PrivateChatSessionMetadata.cliente_id == user.id,
                    PrivateChatSessionMetadata.other_cliente_id == other_user_id
                ),
                and_(
                    PrivateChatSessionMetadata.cliente_id == other_user_id,
                    PrivateChatSessionMetadata.other_cliente_id == user.id
                )
            )
        )
        .where(PrivateChatSessionMetadata.deleted_at.is_(None))
    )
    existing_session = result.scalar_one_or_none()
    
    if existing_session:
        return {
            "success": True,
            "session_id": existing_session.id,
            "exists": True
        }
    
    # Create new session
    session = PrivateChatSessionMetadata(
        cliente_id=user.id,
        other_cliente_id=other_user_id,
        created_at=datetime.utcnow()
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return {
        "success": True,
        "session_id": session.id,
        "exists": False
    }


async def delete_chat_session(
    db: AsyncSession,
    user: Cliente,
    session_id: int
) -> Dict[str, Any]:
    """
    Delete chat session (soft delete)
    Matches Perl's chat session deletion logic
    """
    result = await db.execute(
        update(PrivateChatSessionMetadata)
        .where(PrivateChatSessionMetadata.id == session_id)
        .where(
            or_(
                PrivateChatSessionMetadata.cliente_id == user.id,
                PrivateChatSessionMetadata.other_cliente_id == user.id
            )
        )
        .values(deleted_at=datetime.utcnow())
    )
    await db.commit()
    
    if result.rowcount > 0:
        return {"success": True}
    else:
        return {"error": "Session not found"}


async def list_chat_sessions(
    db: AsyncSession,
    user: Cliente
) -> Dict[str, Any]:
    """
    List user's chat sessions
    Matches Perl's chat list logic
    """
    result = await db.execute(
        select(PrivateChatSessionMetadata)
        .where(
            or_(
                PrivateChatSessionMetadata.cliente_id == user.id,
                PrivateChatSessionMetadata.other_cliente_id == user.id
            )
        )
        .where(PrivateChatSessionMetadata.deleted_at.is_(None))
        .order_by(PrivateChatSessionMetadata.last_message_at.desc())
    )
    sessions = result.scalars().all()
    
    rows = []
    for session in sessions:
        # Determine other user
        other_user_id = (
            session.other_cliente_id 
            if session.cliente_id == user.id 
            else session.cliente_id
        )
        
        # Get other user info
        result = await db.execute(
            select(Cliente).where(Cliente.id == other_user_id)
        )
        other_user = result.scalar_one_or_none()
        
        if other_user:
            rows.append({
                "session_id": session.id,
                "other_user": {
                    "id": other_user.id,
                    "apelido": other_user.apelido,
                    "avatar_url": other_user.avatar_url_or_default()
                },
                "last_message_at": session.last_message_at.isoformat() if session.last_message_at else None,
                "unread_count": 0  # TODO: Implement unread count
            })
    
    return {"rows": rows}


async def send_message(
    db: AsyncSession,
    user: Cliente,
    session_id: int,
    message_text: str
) -> Dict[str, Any]:
    """
    Send message in chat session
    Matches Perl's send message logic
    """
    # Get session and verify user is participant
    result = await db.execute(
        select(PrivateChatSessionMetadata)
        .where(PrivateChatSessionMetadata.id == session_id)
        .where(
            or_(
                PrivateChatSessionMetadata.cliente_id == user.id,
                PrivateChatSessionMetadata.other_cliente_id == user.id
            )
        )
        .where(PrivateChatSessionMetadata.deleted_at.is_(None))
    )
    session = result.scalar_one_or_none()
    
    if not session:
        return {"error": "Session not found"}
    
    # Create message (stored in support chat table for now)
    # TODO: Create dedicated private_chat_messages table
    message = ChatSupportMessage(
        cliente_id=user.id,
        message=message_text,
        is_admin=False,
        created_at=datetime.utcnow()
    )
    db.add(message)
    
    # Update session last message time
    session.last_message_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(message)
    
    # Update user's sent message count
    user.private_chat_messages_sent = (user.private_chat_messages_sent or 0) + 1
    await db.commit()
    
    return {
        "success": True,
        "message_id": message.id,
        "created_at": message.created_at.isoformat()
    }


async def list_messages(
    db: AsyncSession,
    user: Cliente,
    session_id: int,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """
    List messages in chat session
    Matches Perl's message list logic
    """
    # Verify user is participant
    result = await db.execute(
        select(PrivateChatSessionMetadata)
        .where(PrivateChatSessionMetadata.id == session_id)
        .where(
            or_(
                PrivateChatSessionMetadata.cliente_id == user.id,
                PrivateChatSessionMetadata.other_cliente_id == user.id
            )
        )
        .where(PrivateChatSessionMetadata.deleted_at.is_(None))
    )
    session = result.scalar_one_or_none()
    
    if not session:
        return {"error": "Session not found"}
    
    # Get messages
    # TODO: Filter by session_id when dedicated table exists
    result = await db.execute(
        select(ChatSupportMessage)
        .order_by(ChatSupportMessage.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    messages = result.scalars().all()
    
    rows = []
    for msg in messages:
        rows.append({
            "id": msg.id,
            "sender_id": msg.cliente_id,
            "message": msg.message,
            "created_at": msg.created_at.isoformat() if msg.created_at else None
        })
    
    return {"rows": rows}

