"""
Badges (Círculo Penhas) helper module
Port from Perl Penhas::Helpers::Badges
Business logic for badge assignment and invitation system
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from datetime import datetime, timedelta

from app.models.cliente import Cliente
from app.models.admin import BadgeInvite
from app.integrations.email import email_service


async def create_badge_invite(
    db: AsyncSession,
    email: str,
    badge_name: str,
    inviter_admin_id: int
) -> Dict[str, Any]:
    """
    Create badge invitation
    Matches Perl's badge invite creation logic
    """
    # Generate unique token
    import secrets
    token = secrets.token_urlsafe(32)
    
    # Create invite
    invite = BadgeInvite(
        email=email,
        badge_name=badge_name,
        token=token,
        inviter_admin_id=inviter_admin_id,
        status='pending',
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    db.add(invite)
    await db.commit()
    await db.refresh(invite)
    
    # Send invitation email
    acceptance_url = f"{settings.FRONTEND_URL}/badge/accept?token={token}"
    
    await email_service.send_circulo_penhas_invite_email(
        to_email=email,
        nome=email.split('@')[0],  # Use part before @ as name
        badge_name=badge_name,
        acceptance_url=acceptance_url
    )
    
    return {
        "success": True,
        "invite_id": invite.id,
        "token": token
    }


async def accept_badge_invite(
    db: AsyncSession,
    token: str,
    user: Cliente
) -> Dict[str, Any]:
    """
    Accept badge invitation
    Matches Perl's badge acceptance logic
    """
    # Find invite by token
    result = await db.execute(
        select(BadgeInvite)
        .where(BadgeInvite.token == token)
        .where(BadgeInvite.status == 'pending')
    )
    invite = result.scalar_one_or_none()
    
    if not invite:
        return {"error": "Invalid or expired invitation"}
    
    # Check expiration
    if invite.expires_at and invite.expires_at < datetime.utcnow():
        return {"error": "This invitation has expired"}
    
    # Verify email matches
    if invite.email.lower() != user.email.lower():
        return {
            "error": "This invitation is for a different email address",
            "expected_email": invite.email
        }
    
    # Accept invite
    invite.status = 'accepted'
    invite.accepted_at = datetime.utcnow()
    invite.accepted_by_cliente_id = user.id
    
    # Update user's badge
    # TODO: Implement badge assignment to user
    # This might involve creating a clientes_badges table entry
    
    await db.commit()
    
    return {
        "success": True,
        "badge_name": invite.badge_name,
        "message": f"Você agora faz parte do {invite.badge_name}!"
    }


async def list_user_badges(
    db: AsyncSession,
    user: Cliente
) -> Dict[str, Any]:
    """
    List user's badges
    Matches Perl's badge listing logic
    """
    # TODO: Implement when clientes_badges table is ready
    # For now, return empty list
    
    return {"rows": []}


async def revoke_badge(
    db: AsyncSession,
    user_id: int,
    badge_name: str,
    admin_id: int
) -> Dict[str, Any]:
    """
    Revoke badge from user
    Admin action
    """
    # TODO: Implement badge revocation
    # Update clientes_badges table to mark as revoked
    
    return {"success": True}


async def list_pending_invites(
    db: AsyncSession,
    admin_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    List pending badge invitations
    Admin view
    """
    query = select(BadgeInvite).where(BadgeInvite.status == 'pending')
    
    if admin_id:
        query = query.where(BadgeInvite.inviter_admin_id == admin_id)
    
    query = query.order_by(BadgeInvite.created_at.desc())
    
    result = await db.execute(query)
    invites = result.scalars().all()
    
    rows = []
    for invite in invites:
        rows.append({
            "id": invite.id,
            "email": invite.email,
            "badge_name": invite.badge_name,
            "created_at": invite.created_at.isoformat() if invite.created_at else None,
            "expires_at": invite.expires_at.isoformat() if invite.expires_at else None,
            "expired": invite.expires_at < datetime.utcnow() if invite.expires_at else False
        })
    
    return {"rows": rows}


async def cancel_badge_invite(
    db: AsyncSession,
    invite_id: int,
    admin_id: int
) -> Dict[str, Any]:
    """
    Cancel badge invitation
    Admin action
    """
    result = await db.execute(
        update(BadgeInvite)
        .where(BadgeInvite.id == invite_id)
        .where(BadgeInvite.inviter_admin_id == admin_id)
        .values(
            status='cancelled',
            cancelled_at=datetime.utcnow()
        )
    )
    await db.commit()
    
    if result.rowcount > 0:
        return {"success": True}
    else:
        return {"error": "Invitation not found"}

