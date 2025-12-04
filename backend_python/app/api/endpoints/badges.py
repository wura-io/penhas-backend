from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.api import deps
from app.db.session import get_db
from app.models.minor import Badge, BadgeInvite
from app.models.cliente import Cliente

router = APIRouter()

@router.get("/accept")
async def accept_badge_invite_page(
    token: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Show badge acceptance page (HTML).
    In API context, return info.
    """
    invite_res = await db.execute(select(BadgeInvite).where(BadgeInvite.token == token))
    invite = invite_res.scalars().first()
    
    if not invite or invite.status != 'pending':
        raise HTTPException(status_code=400, detail="Invalid or expired token")
        
    return {"status": "ok", "badge_id": invite.badge_id, "cliente_id": invite.cliente_id}

@router.post("/accept")
async def accept_badge_invite_process(
    token: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Process badge acceptance.
    """
    invite_res = await db.execute(select(BadgeInvite).where(BadgeInvite.token == token))
    invite = invite_res.scalars().first()
    
    if not invite or invite.status != 'pending':
        raise HTTPException(status_code=400, detail="Invalid token")
        
    invite.status = 'accepted'
    invite.accepted_at = datetime.utcnow()
    # Add logic to create ClienteTag record
    await db.commit()
    
    return {"status": "confirmed_success"}

