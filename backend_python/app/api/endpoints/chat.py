from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api import deps
from app.models.cliente import Cliente
from app.db.session import get_db
from app.helpers import chat as chat_helper, chat_support as chat_support_helper

router = APIRouter()


class CreateChatRequest(BaseModel):
    """Create chat session request"""
    other_user_id: int


class SendMessageRequest(BaseModel):
    """Send message request"""
    message: str


class SendSupportMessageRequest(BaseModel):
    """Send support message request"""
    message: str


@router.get("/")
async def list_chats(
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user)
) -> Any:
    """
    List user's chat sessions
    Matches Perl GET /me/chats
    """
    result = await chat_helper.list_chat_sessions(
        db=db,
        user=current_user
    )
    return result


@router.post("/session")
async def create_chat_session(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    chat_data: CreateChatRequest
) -> Any:
    """
    Create or get chat session
    Matches Perl POST /me/chats-session
    """
    result = await chat_helper.create_chat_session(
        db=db,
        user=current_user,
        other_user_id=chat_data.other_user_id
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)
    
    return result


@router.delete("/session/{session_id}")
async def delete_chat_session(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    session_id: int
) -> Any:
    """
    Delete chat session
    Matches Perl DELETE /me/chats-session
    """
    result = await chat_helper.delete_chat_session(
        db=db,
        user=current_user,
        session_id=session_id
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result)
    
    return result


@router.post("/messages")
async def send_message(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    session_id: int = Body(..., embed=True),
    message_data: SendMessageRequest
) -> Any:
    """
    Send message in chat
    Matches Perl POST /me/chats-messages
    """
    result = await chat_helper.send_message(
        db=db,
        user=current_user,
        session_id=session_id,
        message_text=message_data.message
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)
    
    return result


@router.get("/messages")
async def list_messages(
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    session_id: int = None,
    limit: int = 50,
    offset: int = 0
) -> Any:
    """
    List messages in chat
    Matches Perl GET /me/chats-messages
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    
    result = await chat_helper.list_messages(
        db=db,
        user=current_user,
        session_id=session_id,
        limit=limit,
        offset=offset
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result)
    
    return result


# Support chat endpoints
@router.post("/support/messages")
async def send_support_message(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    message_data: SendSupportMessageRequest
) -> Any:
    """
    Send message to support chat
    Matches Perl support chat functionality
    """
    result = await chat_support_helper.send_support_message(
        db=db,
        user=current_user,
        message_text=message_data.message,
        is_admin=False
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)
    
    return result


@router.get("/support/messages")
async def list_support_messages(
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    limit: int = 100,
    offset: int = 0
) -> Any:
    """
    List support chat messages
    Matches Perl support chat functionality
    """
    result = await chat_support_helper.list_support_messages(
        db=db,
        user=current_user,
        limit=limit,
        offset=offset
    )
    return result
