"""
Public onboarding endpoints
Enhanced signup, password reset, and guardian invitation acceptance
"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import secrets

from app.db.session import get_db
from app.models.cliente import Cliente
from app.models.onboarding import ClientesResetPassword
from app.models.guardiao import ClientesGuardio
from app.core.security import get_password_hash, create_access_token
from app.core.crypto import decrypt_guardian_token
from app.integrations.email import email_service
from app.integrations.cpf import cpf_validation_service
from app.integrations.cep import cep_service
from app.utils import is_valid_email_mx

router = APIRouter()


class SignupRequest(BaseModel):
    """User signup request with CPF validation"""
    nome_completo: str
    cpf: str
    dt_nasc: str  # YYYY-MM-DD
    email: EmailStr
    senha: str
    apelido: str
    cep: str | None = None
    genero: str | None = None
    raca: str | None = None


class ResetPasswordRequest(BaseModel):
    """Password reset request"""
    email: EmailStr


class ResetPasswordConfirm(BaseModel):
    """Password reset confirmation"""
    token: str
    new_password: str


class GuardianInviteAccept(BaseModel):
    """Guardian invitation acceptance"""
    token: str


@router.post("/signup")
async def signup(
    *,
    db: AsyncSession = Depends(get_db),
    user_data: SignupRequest
) -> Any:
    """
    User registration with CPF validation
    Matches Perl POST /signup
    """
    # Validate email format and MX records
    if not await is_valid_email_mx(user_data.email):
        raise HTTPException(
            status_code=400,
            detail={"error": "Email inválido ou domínio não existe"}
        )
    
    # Check if email already exists
    result = await db.execute(
        select(Cliente).where(Cliente.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail={"error": "Email já cadastrado"}
        )
    
    # Validate CPF with iWebService (optional - can be async)
    cpf_clean = "".join(filter(str.isdigit, user_data.cpf))
    
    # Basic CPF format validation
    if not cpf_validation_service.validate_cpf_format(cpf_clean):
        raise HTTPException(
            status_code=400,
            detail={"error": "CPF inválido"}
        )
    
    # Validate with external service (can be made async)
    # cpf_validation = await cpf_validation_service.validate_cpf(
    #     db=db,
    #     cpf=cpf_clean,
    #     nome=user_data.nome_completo,
    #     dt_nasc=user_data.dt_nasc
    # )
    # if not cpf_validation.get("valid"):
    #     raise HTTPException(
    #         status_code=400,
    #         detail={"error": cpf_validation.get("message", "CPF não validado")}
    #     )
    
    # Lookup CEP if provided
    municipio = None
    estado = None
    if user_data.cep:
        cep_data = await cep_service.find(user_data.cep)
        if cep_data:
            municipio = cep_data.get('city')
            estado = cep_data.get('state')
    
    # Create user
    user = Cliente(
        email=user_data.email,
        senha=get_password_hash(user_data.senha),
        nome_completo=user_data.nome_completo,
        apelido=user_data.apelido,
        cpf_prefix=cpf_clean[:6] if len(cpf_clean) >= 6 else None,
        dt_nasc=datetime.strptime(user_data.dt_nasc, "%Y-%m-%d").date(),
        genero=user_data.genero,
        raca=user_data.raca,
        cep=user_data.cep,
        municipio=municipio,
        estado=estado,
        active=True,
        created_at=datetime.utcnow()
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Create access token
    access_token = create_access_token(user_id=user.id, session_id=secrets.token_urlsafe(32))
    
    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "apelido": user.apelido
        }
    }


@router.post("/reset-password")
async def request_password_reset(
    *,
    db: AsyncSession = Depends(get_db),
    reset_data: ResetPasswordRequest
) -> Any:
    """
    Request password reset
    Matches Perl POST /reset-password
    """
    # Find user
    result = await db.execute(
        select(Cliente).where(Cliente.email == reset_data.email)
    )
    user = result.scalar_one_or_none()
    
    # Always return success (security - don't leak if email exists)
    if not user:
        return {
            "success": True,
            "message": "Se o email existir, um link de recuperação será enviado"
        }
    
    # Generate reset token
    token = secrets.token_urlsafe(32)
    
    # Save reset token
    reset_record = ClientesResetPassword(
        cliente_id=user.id,
        token=token,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db.add(reset_record)
    await db.commit()
    
    # Send email
    await email_service.send_forgot_password_email(
        to_email=user.email,
        nome=user.nome_completo or user.apelido,
        reset_token=token
    )
    
    return {
        "success": True,
        "message": "Email de recuperação enviado"
    }


@router.post("/reset-password/confirm")
async def confirm_password_reset(
    *,
    db: AsyncSession = Depends(get_db),
    confirm_data: ResetPasswordConfirm
) -> Any:
    """
    Confirm password reset with token
    Matches Perl POST /reset-password/confirm
    """
    # Find valid reset token
    result = await db.execute(
        select(ClientesResetPassword)
        .where(ClientesResetPassword.token == confirm_data.token)
        .where(ClientesResetPassword.used_at.is_(None))
        .where(ClientesResetPassword.expires_at > datetime.utcnow())
    )
    reset_record = result.scalar_one_or_none()
    
    if not reset_record:
        raise HTTPException(
            status_code=400,
            detail={"error": "Token inválido ou expirado"}
        )
    
    # Get user
    result = await db.execute(
        select(Cliente).where(Cliente.id == reset_record.cliente_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail={"error": "Usuário não encontrado"}
        )
    
    # Update password
    user.senha = get_password_hash(confirm_data.new_password)
    
    # Mark token as used
    reset_record.used_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "success": True,
        "message": "Senha alterada com sucesso"
    }


@router.get("/web/guardiao")
async def guardian_invite_page(
    token: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Guardian invitation page
    Matches Perl GET /web/guardiao
    """
    try:
        # Decrypt token to get guardiao_id
        from app.core.config import settings
        decrypted = decrypt_guardian_token(token, settings.SECRET_KEY)
        guardiao_id = int(decrypted)
        
        # Get guardian invite
        result = await db.execute(
            select(ClientesGuardio).where(ClientesGuardio.id == guardiao_id)
        )
        guardiao = result.scalar_one_or_none()
        
        if not guardiao:
            return {
                "error": "Convite não encontrado",
                "valid": False
            }
        
        if guardiao.status != 'pending':
            return {
                "error": "Convite já foi aceito ou expirou",
                "valid": False,
                "status": guardiao.status
            }
        
        # Get inviter info
        result = await db.execute(
            select(Cliente).where(Cliente.id == guardiao.cliente_id)
        )
        inviter = result.scalar_one_or_none()
        
        return {
            "valid": True,
            "guardiao_id": guardiao.id,
            "nome": guardiao.nome,
            "inviter": {
                "apelido": inviter.apelido if inviter else "Uma usuária"
            },
            "token": token
        }
        
    except Exception as e:
        return {
            "error": "Token inválido",
            "valid": False
        }


@router.post("/web/guardiao/accept")
async def accept_guardian_invite(
    *,
    db: AsyncSession = Depends(get_db),
    accept_data: GuardianInviteAccept
) -> Any:
    """
    Accept guardian invitation
    Matches Perl POST /web/guardiao
    """
    try:
        # Decrypt token
        from app.core.config import settings
        decrypted = decrypt_guardian_token(accept_data.token, settings.SECRET_KEY)
        guardiao_id = int(decrypted)
        
        # Get and update guardian
        result = await db.execute(
            select(ClientesGuardio).where(ClientesGuardio.id == guardiao_id)
        )
        guardiao = result.scalar_one_or_none()
        
        if not guardiao:
            raise HTTPException(
                status_code=404,
                detail={"error": "Convite não encontrado"}
            )
        
        if guardiao.status != 'pending':
            raise HTTPException(
                status_code=400,
                detail={"error": "Convite já foi processado"}
            )
        
        # Accept invitation
        guardiao.status = 'active'
        guardiao.accepted_at = datetime.utcnow()
        
        # Update user's active guardian count
        from app.helpers import guardioes as guardioes_helper
        await guardioes_helper.recalc_qtde_guardioes_ativos(db, guardiao.cliente_id)
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Convite aceito com sucesso!",
            "guardiao_id": guardiao.id
        }
        
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"error": "Token inválido"}
        )


@router.get("/web/termos-de-uso")
async def terms_of_service() -> Any:
    """
    Terms of service page
    Matches Perl GET /web/termos-de-uso
    """
    return {
        "title": "Termos de Uso - PenhaS",
        "content": "Termos de uso do aplicativo PenhaS...",
        "last_updated": "2025-01-01"
    }


@router.get("/web/politica-privacidade")
async def privacy_policy() -> Any:
    """
    Privacy policy page
    Matches Perl GET /web/politica-privacidade
    """
    return {
        "title": "Política de Privacidade - PenhaS",
        "content": "Política de privacidade do aplicativo PenhaS...",
        "last_updated": "2025-01-01"
    }


@router.get("/health")
async def health_check() -> Any:
    """
    Simple health check endpoint
    """
    return {
        "status": "ok",
        "service": "penhas-api",
        "timestamp": datetime.utcnow().isoformat()
    }

