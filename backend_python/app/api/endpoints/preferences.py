from typing import Any, List
from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.api import deps
from app.db.session import get_db
from app.models.minor import Preference, ClientesPreference
from app.models.cliente import Cliente

router = APIRouter()

@router.get("/")
async def list_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
) -> Any:
    """
    List user preferences.
    """
    # 1. Get all active preferences
    prefs_result = await db.execute(select(Preference).where(Preference.active == True).order_by(Preference.sort))
    all_prefs = prefs_result.scalars().all()
    
    # 2. Get user values
    user_prefs_result = await db.execute(select(ClientesPreference).where(ClientesPreference.cliente_id == current_user.id))
    user_prefs = {p.preference_id: p.value for p in user_prefs_result.scalars().all()}
    
    result = []
    for pref in all_prefs:
        # TODO: Implement filtering logic (admin only, badge linked) from Perl
        val = user_prefs.get(pref.id, pref.initial_value)
        result.append({
            "key": pref.name,
            "label": pref.label,
            "value": val,
            "type": "boolean"
        })
        
    return {"preferences": result}

@router.post("/")
async def update_preferences(
    prefs: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
) -> Any:
    """
    Update preferences.
    """
    # Logic to iterate keys and upsert ClientesPreference
    # ...
    return {"status": "ok"}

