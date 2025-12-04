from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr

from app.api import deps
from app.core import security
from app.core.jwt_auth import create_user_jwt_token
from app.models.cliente import Cliente
from app.models.onboarding import ClientesActiveSession, LoginLog
from app.db.session import get_db
from datetime import datetime

router = APIRouter()


class LoginRequest(BaseModel):
    """Login request matching Perl API format"""
    email: EmailStr
    senha: str  # Matches Perl field name


class LoginResponse(BaseModel):
    """Login response matching Perl API format"""
    session: str  # JWT token
    user_profile: dict  # Optional: can add user profile data


@router.post("/login")
async def login(
    *,
    db: AsyncSession = Depends(get_db),
    login_data: LoginRequest
) -> Any:
    """
    User login endpoint
    Matches Perl POST /login behavior
    Returns JWT token with session ID
    """
    # Find user by email
    result = await db.execute(
        select(Cliente).where(Cliente.email == login_data.email.lower())
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_credentials", "message": "Email ou senha incorretos"}
        )
    
    # Verify password (supports both legacy SHA256 and bcrypt)
    if not security.verify_password(login_data.senha, user.senha_sha256):
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_credentials", "message": "Email ou senha incorretos"}
        )
    
    # Check if user is active
    if user.status != 'active':
        if user.status == 'blocked':
            raise HTTPException(
                status_code=403,
                detail={"error": "account_blocked", "message": "Sua conta está bloqueada"}
            )
        else:
            raise HTTPException(
                status_code=403,
                detail={"error": "account_inactive", "message": "Sua conta não está ativa"}
            )
    
    # Create new session
    session = ClientesActiveSession(
        cliente_id=user.id,
        created_at=datetime.utcnow()
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    # Log login
    login_log = LoginLog(
        cliente_id=user.id,
        remote_ip="0.0.0.0",  # TODO: Get from request
        app_version="",  # TODO: Get from request headers
        created_at=datetime.utcnow()
    )
    db.add(login_log)
    await db.commit()
    
    # Create JWT token with session ID (matches Perl format)
    jwt_token = create_user_jwt_token(session.id)
    
    return {
        "session": jwt_token
    }

