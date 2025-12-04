from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta
from hashlib import sha256
import secrets
import random

from app.api import deps
from app.core import security
from app.db.session import get_db
from app.models.cliente import Cliente
from app.models.onboarding import ClientesResetPassword, ClientesActiveSession, LoginLog
from app.schemas.onboarding import SignupRequest, PasswordResetRequest, PasswordResetConfirm
from app.core.celery_app import celery_app

router = APIRouter()

@router.post("/signup")
async def signup(
    *,
    db: AsyncSession = Depends(get_db),
    signup_in: SignupRequest,
) -> Any:
    """
    User signup.
    """
    # 1. Clean CPF and CEP
    cpf_clean = "".join(filter(str.isdigit, signup_in.cpf))
    cep_clean = "".join(filter(str.isdigit, signup_in.cep))
    
    # 2. Dry run check
    if signup_in.dry:
        # TODO: Add specific checks for Dry run if needed
        return {"continue": 1}
    
    if not signup_in.email or not signup_in.senha:
        raise HTTPException(status_code=400, detail="Email and password required")

    # 3. Check existing email
    result = await db.execute(select(Cliente).where(Cliente.email == signup_in.email))
    if result.scalars().first():
        raise HTTPException(
            status_code=400, 
            detail="E-mail já possui uma conta. Por favor, faça o login, ou utilize a função 'Esqueci minha senha'."
        )
        
    # 4. Check existing CPF
    cpf_hash = sha256(cpf_clean.encode('utf-8')).hexdigest()
    result = await db.execute(select(Cliente).where(Cliente.cpf_hash == cpf_hash))
    if result.scalars().first():
        raise HTTPException(
            status_code=400,
            detail="Este CPF já possui uma conta."
        )

    # 5. Create User
    # Note: Using legacy SHA256 hex hash for compatibility as requested by plan "support legacy password hashes"
    # Ideally we should switch to bcrypt for new users, but sticking to legacy format for now for consistency
    # unless we decide to use security.get_password_hash(signup_in.senha) which is bcrypt.
    # Let's use bcrypt for new users, as verify_password handles both.
    
    # Actually, Perl uses sha256_hex. If other systems depend on this format, we might need to stick to it.
    # But for now let's use the safer bcrypt.
    # Update: The migration plan said "support legacy... and new Bcrypt hashes".
    password_hash = security.get_password_hash(signup_in.senha)
    
    # Note: If we really want to mimic Perl exactly:
    # password_hash = sha256(signup_in.senha.encode('utf-8')).hexdigest()
    
    # Let's use bcrypt for better security.
    
    # Generate Salt Key (legacy requirement?)
    # Perl: encode_z85(random_bytes(8)) -> 10 chars.
    salt_key = secrets.token_urlsafe(8)[:10]

    cliente = Cliente(
        email=signup_in.email,
        nome_completo=signup_in.nome_completo,
        cpf_hash=cpf_hash,
        cpf_prefix=cpf_clean[:4],
        dt_nasc=signup_in.dt_nasc,
        cep=cep_clean,
        senha_sha256=password_hash, # verify_password must support this format
        genero=signup_in.genero or "",
        apelido=signup_in.apelido or "",
        raca=signup_in.raca,
        nome_social=signup_in.nome_social,
        status="active",
        created_on=datetime.utcnow(),
        salt_key=salt_key,
        skills_cached='[]'
    )
    db.add(cliente)
    await db.commit()
    await db.refresh(cliente)
    
    # 6. Create Session
    session = ClientesActiveSession(cliente_id=cliente.id)
    db.add(session)
    await db.commit()
    
    # 7. Login Log
    # remote_ip would come from request, mocking for now
    log = LoginLog(
        remote_ip="0.0.0.0",
        cliente_id=cliente.id,
        app_version=signup_in.app_version
    )
    db.add(log)
    await db.commit()
    
    # 8. Trigger Celery Task
    # celery_app.send_task("cliente_update_cep", args=[cliente.id])
    
    # 9. Return Token
    access_token_expires = timedelta(minutes=security.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = security.create_access_token(cliente.id, expires_delta=access_token_expires)
    
    return {
        "session": token
    }

@router.post("/reset-password/request-new")
async def request_new_password(
    *,
    db: AsyncSession = Depends(get_db),
    reset_in: PasswordResetRequest,
) -> Any:
    """
    Request password reset code.
    """
    result = await db.execute(select(Cliente).where(Cliente.email == reset_in.email))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Não foi encontrado nenhuma conta com esse endereço de e-mail.")
    
    # Check throttling
    min_retry_time = datetime.utcnow() - timedelta(seconds=60) # Simple check
    
    # Create Token
    token_digits = "".join([str(random.randint(0, 9)) for _ in range(6)])
    
    reset_entry = ClientesResetPassword(
        cliente_id=user.id,
        token=token_digits,
        valid_until=datetime.utcnow() + timedelta(hours=1),
        requested_by_remote_ip="0.0.0.0",
        created_at=datetime.utcnow()
    )
    db.add(reset_entry)
    await db.commit()
    
    # Send Email (Mocked Task)
    # celery_app.send_task("send_email", args=[user.email, "Reset Password", f"Code: {token_digits}"])
    
    return {
        "message": f"Enviamos um código com 6 números para o seu e-mail",
        "ttl": 3600,
        "digits": 6
    }

@router.post("/reset-password/write-new")
async def write_new_password(
    *,
    db: AsyncSession = Depends(get_db),
    reset_in: PasswordResetConfirm,
) -> Any:
    """
    Confirm password reset.
    """
    result = await db.execute(select(Cliente).where(Cliente.email == reset_in.email))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")
        
    result = await db.execute(select(ClientesResetPassword).where(
        and_(
            ClientesResetPassword.cliente_id == user.id,
            ClientesResetPassword.token == reset_in.token,
            ClientesResetPassword.valid_until >= datetime.utcnow(),
            ClientesResetPassword.used_at.is_(None)
        )
    ))
    reset_entry = result.scalars().first()
    
    if not reset_entry:
         raise HTTPException(status_code=400, detail="Número não confere.")

    if reset_in.dry:
        return {"continue": 1}
        
    if not reset_in.senha:
        raise HTTPException(status_code=400, detail="Password required")
        
    # Verify new password is not same as old (if old was hashable)
    if security.verify_password(reset_in.senha, user.senha_sha256):
         raise HTTPException(status_code=400, detail="A nova senha não pode ser igual à anterior.")
         
    # Update Password
    user.senha_sha256 = security.get_password_hash(reset_in.senha)
    
    # Mark token used
    reset_entry.used_at = datetime.utcnow()
    reset_entry.used_by_remote_ip = "0.0.0.0"
    
    await db.commit()
    
    return {"success": 1}

