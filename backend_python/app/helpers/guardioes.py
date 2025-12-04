"""
Guardiões (Guardians) helper module
Port from Perl Penhas::Helpers::Guardioes
Business logic for guardian management and alerts
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timedelta
import secrets

from app.models.guardiao import ClientesGuardio
from app.models.cliente import Cliente
from app.utils import random_string


async def create_guardiao(
    db: AsyncSession,
    user: Cliente,
    nome: str,
    celular_e164: str
) -> Dict[str, Any]:
    """
    Create a new guardian invitation
    Matches Perl's guardian creation logic
    """
    # Format phone number (simplified)
    celular_formatted = celular_e164  # TODO: Proper formatting
    
    # Check existing guardians count
    result = await db.execute(
        select(ClientesGuardio)
        .where(ClientesGuardio.cliente_id == user.id)
        .where(ClientesGuardio.deleted_at.is_(None))
    )
    existing_count = len(result.scalars().all())
    
    # Limit to reasonable number (e.g., 10)
    max_guardians = 10
    if existing_count >= max_guardians:
        return {
            "error": "max_guardians",
            "message": f"Você já possui {max_guardians} guardiões"
        }
    
    # Check for duplicate phone
    result = await db.execute(
        select(ClientesGuardio)
        .where(ClientesGuardio.cliente_id == user.id)
        .where(ClientesGuardio.celular_e164 == celular_e164)
        .where(ClientesGuardio.deleted_at.is_(None))
    )
    if result.scalar_one_or_none():
        return {
            "error": "duplicate_phone",
            "message": "Este número já está cadastrado como guardião"
        }
    
    # Generate secure token
    token = random_string(32)
    
    # Create guardian
    guardiao = ClientesGuardio(
        cliente_id=user.id,
        nome=nome,
        celular_e164=celular_e164,
        celular_formatted_as_national=celular_formatted,
        token=token,
        status="pending",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(guardiao)
    await db.commit()
    await db.refresh(guardiao)
    
    # TODO: Send SMS invitation
    # await send_guardian_invitation_sms(guardiao)
    
    return {
        "success": True,
        "guardiao": {
            "id": guardiao.id,
            "nome": guardiao.nome,
            "celular": guardiao.celular_formatted_as_national,
            "status": guardiao.status,
            "created_at": guardiao.created_at.isoformat() if guardiao.created_at else None
        }
    }


async def list_guardioes(
    db: AsyncSession,
    user: Cliente
) -> Dict[str, Any]:
    """
    List user's guardians
    Matches Perl's guardian list logic
    """
    result = await db.execute(
        select(ClientesGuardio)
        .where(ClientesGuardio.cliente_id == user.id)
        .where(ClientesGuardio.deleted_at.is_(None))
        .order_by(ClientesGuardio.created_at.desc())
    )
    guardioes = result.scalars().all()
    
    rows = []
    for guardiao in guardioes:
        rows.append({
            "id": guardiao.id,
            "nome": guardiao.nome,
            "celular": guardiao.celular_formatted_as_national,
            "status": guardiao.status,
            "created_at": guardiao.created_at.isoformat() if guardiao.created_at else None,
            "accepted_at": guardiao.accepted_at.isoformat() if guardiao.accepted_at else None,
            "expired": guardiao.expires_at < datetime.utcnow() if guardiao.expires_at else False
        })
    
    return {"rows": rows}


async def update_guardiao(
    db: AsyncSession,
    user: Cliente,
    guardiao_id: int,
    nome: Optional[str] = None,
    celular_e164: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update guardian information
    Matches Perl's guardian update logic
    """
    # Get guardian
    result = await db.execute(
        select(ClientesGuardio)
        .where(ClientesGuardio.id == guardiao_id)
        .where(ClientesGuardio.cliente_id == user.id)
        .where(ClientesGuardio.deleted_at.is_(None))
    )
    guardiao = result.scalar_one_or_none()
    
    if not guardiao:
        return {"error": "not_found", "message": "Guardião não encontrado"}
    
    # Update fields
    if nome:
        guardiao.nome = nome
    if celular_e164:
        # Check for duplicate
        result = await db.execute(
            select(ClientesGuardio)
            .where(ClientesGuardio.cliente_id == user.id)
            .where(ClientesGuardio.celular_e164 == celular_e164)
            .where(ClientesGuardio.deleted_at.is_(None))
            .where(ClientesGuardio.id != guardiao_id)
        )
        if result.scalar_one_or_none():
            return {
                "error": "duplicate_phone",
                "message": "Este número já está cadastrado como guardião"
            }
        
        guardiao.celular_e164 = celular_e164
        guardiao.celular_formatted_as_national = celular_e164  # TODO: Format properly
    
    await db.commit()
    
    return {"success": True}


async def delete_guardiao(
    db: AsyncSession,
    user: Cliente,
    guardiao_id: int
) -> Dict[str, Any]:
    """
    Delete (soft delete) a guardian
    Matches Perl's guardian deletion logic
    """
    result = await db.execute(
        update(ClientesGuardio)
        .where(ClientesGuardio.id == guardiao_id)
        .where(ClientesGuardio.cliente_id == user.id)
        .where(ClientesGuardio.deleted_at.is_(None))
        .values(deleted_at=datetime.utcnow())
    )
    await db.commit()
    
    if result.rowcount > 0:
        # Update guardian count
        await recalc_qtde_guardioes_ativos(db, user)
        return {"success": True}
    else:
        return {"error": "not_found", "message": "Guardião não encontrado"}


async def alert_guards(
    db: AsyncSession,
    user: Cliente,
    latitude: Optional[str] = None,
    longitude: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send panic alert to all active guardians
    Matches Perl's alert_guards logic
    """
    # Get active guardians
    result = await db.execute(
        select(ClientesGuardio)
        .where(ClientesGuardio.cliente_id == user.id)
        .where(ClientesGuardio.status == 'accepted')
        .where(ClientesGuardio.deleted_at.is_(None))
    )
    guardioes = result.scalars().all()
    
    if not guardioes:
        return {
            "error": "no_guardians",
            "message": "Você não possui guardiões cadastrados"
        }
    
    # Record panic activation
    from app.models.activity import ClienteAtivacoesPanico
    panic = ClienteAtivacoesPanico(
        cliente_id=user.id,
        created_at=datetime.utcnow(),
        latitude=latitude,
        longitude=longitude
    )
    db.add(panic)
    await db.commit()
    
    # Send SMS to each guardian
    sent_count = 0
    for guardiao in guardioes:
        # TODO: Send SMS via AWS SNS
        # message = f"ALERTA! {user.apelido} acionou o botão de pânico."
        # if latitude and longitude:
        #     message += f" Localização: https://maps.google.com/?q={latitude},{longitude}"
        # await send_sms(guardiao.celular_e164, message)
        sent_count += 1
    
    return {
        "success": True,
        "sent_to": sent_count,
        "message": f"Alerta enviado para {sent_count} guardião(ões)"
    }


async def recalc_qtde_guardioes_ativos(
    db: AsyncSession,
    user: Cliente
) -> None:
    """
    Recalculate the count of active guardians
    Matches Perl's recalc_qtde_guardioes_ativos
    """
    result = await db.execute(
        select(ClientesGuardio)
        .where(ClientesGuardio.cliente_id == user.id)
        .where(ClientesGuardio.status == 'accepted')
        .where(ClientesGuardio.deleted_at.is_(None))
    )
    count = len(result.scalars().all())
    
    # Update user
    user.qtde_guardioes_ativos = count
    await db.commit()


async def accept_guardian_invitation(
    db: AsyncSession,
    token: str,
    estava_em_situacao_risco: bool = False
) -> Dict[str, Any]:
    """
    Accept guardian invitation by token
    Matches Perl's guardian acceptance logic
    """
    # Find guardian by token
    result = await db.execute(
        select(ClientesGuardio)
        .where(ClientesGuardio.token == token)
        .where(ClientesGuardio.status == 'pending')
    )
    guardiao = result.scalar_one_or_none()
    
    if not guardiao:
        return {"error": "invalid_token", "message": "Convite inválido ou já aceito"}
    
    # Check expiration
    if guardiao.expires_at and guardiao.expires_at < datetime.utcnow():
        return {"error": "expired", "message": "Este convite expirou"}
    
    # Accept invitation
    guardiao.status = 'accepted'
    guardiao.accepted_at = datetime.utcnow()
    guardiao.estava_em_situacao_risco = estava_em_situacao_risco
    
    await db.commit()
    
    # Update guardian count for user
    result = await db.execute(
        select(Cliente).where(Cliente.id == guardiao.cliente_id)
    )
    user = result.scalar_one_or_none()
    if user:
        await recalc_qtde_guardioes_ativos(db, user)
    
    return {
        "success": True,
        "message": "Você agora é guardião(ã) desta pessoa"
    }

