"""
Admin helper module
Business logic for admin user management and operations
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from datetime import datetime, timedelta

from app.models.cliente import Cliente
from app.models.admin import AdminUser, NotificationMessage, NotificationLog
from app.models.chat import ChatSupport, ChatSupportMessage
from app.models.ponto_apoio import PontoApoioSugestoe


async def search_users(
    db: AsyncSession,
    query: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Search users for admin panel
    """
    stmt = select(Cliente)
    
    if query:
        # Search by email, name, or nickname
        search_pattern = f"%{query}%"
        stmt = stmt.where(
            or_(
                Cliente.email.ilike(search_pattern),
                Cliente.nome_completo.ilike(search_pattern),
                Cliente.apelido.ilike(search_pattern)
            )
        )
    
    stmt = stmt.order_by(Cliente.created_at.desc()).limit(limit).offset(offset)
    
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    rows = []
    for user in users:
        rows.append({
            "id": user.id,
            "email": user.email,
            "apelido": user.apelido,
            "nome_completo": user.nome_completo,
            "genero": user.genero,
            "active": user.active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "deleted_at": user.deleted_at.isoformat() if user.deleted_at else None
        })
    
    return {"rows": rows, "total": len(rows)}


async def get_user_details(
    db: AsyncSession,
    user_id: int
) -> Dict[str, Any]:
    """
    Get detailed user information for admin
    """
    result = await db.execute(
        select(Cliente).where(Cliente.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        return {"error": "User not found"}
    
    # Get user stats
    from app.models.guardiao import ClientesGuardio
    from app.models.timeline import ClientesTweet
    from app.models.audio import ClientesAudio
    
    result = await db.execute(
        select(func.count(ClientesGuardio.id))
        .where(ClientesGuardio.cliente_id == user_id)
        .where(ClientesGuardio.deleted_at.is_(None))
    )
    guardian_count = result.scalar()
    
    result = await db.execute(
        select(func.count(ClientesTweet.id))
        .where(ClientesTweet.cliente_id == user_id)
        .where(ClientesTweet.deleted_at.is_(None))
    )
    tweet_count = result.scalar()
    
    result = await db.execute(
        select(func.count(ClientesAudio.id))
        .where(ClientesAudio.cliente_id == user_id)
    )
    audio_count = result.scalar()
    
    return {
        "id": user.id,
        "email": user.email,
        "apelido": user.apelido,
        "nome_completo": user.nome_completo,
        "cpf_prefix": user.cpf_prefix,
        "dt_nasc": user.dt_nasc.isoformat() if user.dt_nasc else None,
        "genero": user.genero,
        "raca": user.raca,
        "municipio": user.municipio,
        "estado": user.estado,
        "cep": user.cep,
        "active": user.active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "deleted_at": user.deleted_at.isoformat() if user.deleted_at else None,
        "perform_delete_at": user.perform_delete_at.isoformat() if user.perform_delete_at else None,
        "stats": {
            "guardian_count": guardian_count,
            "tweet_count": tweet_count,
            "audio_count": audio_count,
            "login_count": user.qtde_login_senha_normal or 0
        }
    }


async def schedule_user_deletion(
    db: AsyncSession,
    user_id: int,
    days: int = 15
) -> Dict[str, Any]:
    """
    Schedule user for deletion
    """
    result = await db.execute(
        select(Cliente).where(Cliente.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        return {"error": "User not found"}
    
    user.perform_delete_at = datetime.utcnow() + timedelta(days=days)
    user.deleted_scheduled_meta = {"scheduled_by": "admin", "days": days}
    
    await db.commit()
    
    # Send notification email
    from app.integrations.email import email_service
    await email_service.send_account_deletion_email(
        to_email=user.email,
        nome=user.nome_completo or user.apelido,
        deletion_date=user.perform_delete_at.strftime("%d/%m/%Y")
    )
    
    return {
        "success": True,
        "deletion_scheduled_for": user.perform_delete_at.isoformat()
    }


async def cancel_user_deletion(
    db: AsyncSession,
    user_id: int
) -> Dict[str, Any]:
    """
    Cancel scheduled user deletion
    """
    result = await db.execute(
        update(Cliente)
        .where(Cliente.id == user_id)
        .values(
            perform_delete_at=None,
            deleted_scheduled_meta=None
        )
    )
    await db.commit()
    
    if result.rowcount > 0:
        return {"success": True}
    else:
        return {"error": "User not found"}


async def get_dashboard_stats(
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Get dashboard statistics for admin panel
    """
    # Total users
    result = await db.execute(select(func.count(Cliente.id)))
    total_users = result.scalar()
    
    # Active users
    result = await db.execute(
        select(func.count(Cliente.id)).where(Cliente.active == True)
    )
    active_users = result.scalar()
    
    # Users created last 30 days
    cutoff = datetime.utcnow() - timedelta(days=30)
    result = await db.execute(
        select(func.count(Cliente.id)).where(Cliente.created_at >= cutoff)
    )
    new_users_30d = result.scalar()
    
    # Total tweets
    from app.models.timeline import ClientesTweet
    result = await db.execute(
        select(func.count(ClientesTweet.id))
        .where(ClientesTweet.deleted_at.is_(None))
    )
    total_tweets = result.scalar()
    
    # Total audio recordings
    from app.models.audio import ClientesAudio
    result = await db.execute(select(func.count(ClientesAudio.id)))
    total_audios = result.scalar()
    
    # Open support chats
    result = await db.execute(
        select(func.count(ChatSupport.id))
        .where(ChatSupport.status == 'active')
    )
    open_support_chats = result.scalar()
    
    # Pending notifications
    result = await db.execute(
        select(func.count(NotificationMessage.id))
        .where(NotificationMessage.status == 'pending')
    )
    pending_notifications = result.scalar()
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "new_last_30_days": new_users_30d
        },
        "content": {
            "tweets": total_tweets,
            "audios": total_audios
        },
        "support": {
            "open_chats": open_support_chats
        },
        "notifications": {
            "pending": pending_notifications
        }
    }


async def create_notification_broadcast(
    db: AsyncSession,
    admin_user: AdminUser,
    title: str,
    content: str,
    notification_type: str = "general",
    segment_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create notification for broadcasting
    """
    notif = NotificationMessage(
        admin_user_id=admin_user.id,
        title=title,
        content=content,
        notification_type=notification_type,
        segment_id=segment_id,
        status='pending',
        created_at=datetime.utcnow(),
        scheduled_at=datetime.utcnow()
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)
    
    # Queue for sending
    from app.worker import new_notification_task
    new_notification_task.delay(notif.id)
    
    return {
        "success": True,
        "notification_id": notif.id
    }


async def list_ponto_apoio_suggestions(
    db: AsyncSession,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """
    List support point suggestions for review
    """
    stmt = select(PontoApoioSugestoe).order_by(PontoApoioSugestoe.created_at.desc())
    
    if status:
        stmt = stmt.where(PontoApoioSugestoe.status == status)
    
    stmt = stmt.limit(limit).offset(offset)
    
    result = await db.execute(stmt)
    suggestions = result.scalars().all()
    
    rows = []
    for sugg in suggestions:
        # Get submitter info
        result = await db.execute(
            select(Cliente).where(Cliente.id == sugg.cliente_id)
        )
        user = result.scalar_one_or_none()
        
        rows.append({
            "id": sugg.id,
            "nome": sugg.nome,
            "categoria": sugg.categoria,
            "municipio": sugg.municipio,
            "estado": sugg.estado,
            "status": sugg.status,
            "created_at": sugg.created_at.isoformat() if sugg.created_at else None,
            "submitter": {
                "id": user.id if user else None,
                "email": user.email if user else None,
                "apelido": user.apelido if user else None
            }
        })
    
    return {"rows": rows}


async def approve_ponto_apoio_suggestion(
    db: AsyncSession,
    suggestion_id: int,
    admin_user: AdminUser
) -> Dict[str, Any]:
    """
    Approve support point suggestion
    """
    result = await db.execute(
        select(PontoApoioSugestoe).where(PontoApoioSugestoe.id == suggestion_id)
    )
    suggestion = result.scalar_one_or_none()
    
    if not suggestion:
        return {"error": "Suggestion not found"}
    
    # Create actual ponto apoio from suggestion
    from app.models.ponto_apoio import PontoApoio
    
    ponto = PontoApoio(
        nome=suggestion.nome,
        categoria=suggestion.categoria,
        municipio=suggestion.municipio,
        estado=suggestion.estado,
        endereco=suggestion.endereco,
        telefone=suggestion.telefone,
        email=suggestion.email,
        descricao=suggestion.descricao,
        eh_24h=suggestion.eh_24h,
        created_at=datetime.utcnow()
    )
    db.add(ponto)
    
    # Update suggestion status
    suggestion.status = 'approved'
    suggestion.reviewed_at = datetime.utcnow()
    suggestion.reviewed_by_admin_id = admin_user.id
    
    await db.commit()
    await db.refresh(ponto)
    
    return {
        "success": True,
        "ponto_apoio_id": ponto.id
    }


async def reject_ponto_apoio_suggestion(
    db: AsyncSession,
    suggestion_id: int,
    admin_user: AdminUser,
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Reject support point suggestion
    """
    result = await db.execute(
        update(PontoApoioSugestoe)
        .where(PontoApoioSugestoe.id == suggestion_id)
        .values(
            status='rejected',
            reviewed_at=datetime.utcnow(),
            reviewed_by_admin_id=admin_user.id,
            rejection_reason=reason
        )
    )
    await db.commit()
    
    if result.rowcount > 0:
        return {"success": True}
    else:
        return {"error": "Suggestion not found"}

