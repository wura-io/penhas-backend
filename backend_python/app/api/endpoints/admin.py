from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime

from app.api import deps
from app.db.session import get_db
from app.models.admin import DirectusUser, NotificationMessage
from app.models.cliente import Cliente
from app.models.chat import ChatSupport, ChatSupportMessage
from pydantic import BaseModel, EmailStr

router = APIRouter()

# Admin Auth Schemas
class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str

# Endpoints

@router.post("/login")
async def admin_login(
    login_in: AdminLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Admin login.
    """
    result = await db.execute(select(DirectusUser).where(DirectusUser.email == login_in.email))
    admin_user = result.scalars().first()
    
    # Note: Perl uses Crypt::Passphrase::Argon2. passlib supports this.
    # We need to verify if existing passwords work.
    if not admin_user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
        
    # TODO: Verify Argon2 password
    # if not verify_argon2(login_in.password, admin_user.password):
    #    raise HTTPException(status_code=400, detail="Invalid credentials")
    
    return {"ok": 1, "name": admin_user.first_name}

@router.get("/users")
async def admin_list_users(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 20,
    nome: Optional[str] = None
) -> Any:
    """
    List users for admin.
    """
    query = select(Cliente).order_by(desc(Cliente.created_on))
    
    if nome:
        # Simple search
        query = query.where(Cliente.nome_completo.ilike(f"%{nome}%"))
        
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/user-messages")
async def admin_list_messages(
    cliente_id: int,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 50
) -> Any:
    """
    List support messages for a specific user.
    """
    result = await db.execute(
        select(ChatSupportMessage)
        .where(ChatSupportMessage.cliente_id == cliente_id)
        .order_by(desc(ChatSupportMessage.created_at))
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

@router.post("/send-message")
async def admin_send_message(
    cliente_id: int = Body(...),
    message: str = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Send support message as admin.
    """
    # Logic similar to regular chat but marked as support
    chat_query = await db.execute(select(ChatSupport).where(ChatSupport.cliente_id == cliente_id))
    chat = chat_query.scalars().first()
    
    if not chat:
        chat = ChatSupport(cliente_id=cliente_id, created_at=datetime.utcnow())
        db.add(chat)
        await db.commit()
        await db.refresh(chat)
        
    msg = ChatSupportMessage(
        chat_support_id=chat.id,
        cliente_id=None, # System/Admin
        message=message,
        created_at=datetime.utcnow(),
        # admin_user_id=current_admin.id
    )
    db.add(msg)
    
    chat.last_msg_at = datetime.utcnow()
    chat.last_msg_preview = message[:200]
    chat.last_msg_is_support = True
    
    await db.commit()
    return {"success": True}

