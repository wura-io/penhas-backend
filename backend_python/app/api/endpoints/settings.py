from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.session import get_db
from app.models.cliente import Cliente

router = APIRouter()

@router.post("/me/modo-anonimo-toggle")
async def toggle_modo_anonimo(
    active: bool = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
) -> Any:
    """
    Toggle Anonymous Mode.
    """
    current_user.modo_anonimo_ativo = active
    # Trigger logic: hide name/avatar in cached things?
    await db.commit()
    return {"success": True, "active": active}

@router.post("/me/modo-camuflado-toggle")
async def toggle_modo_camuflado(
    active: bool = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
) -> Any:
    """
    Toggle Camouflaged Mode (Panic/Safety).
    """
    current_user.modo_camuflado_ativo = active
    await db.commit()
    return {"success": True, "active": active}

@router.post("/me/call-police-pressed")
async def call_police_pressed(
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
) -> Any:
    """
    Log police call button press.
    """
    current_user.qtde_ligar_para_policia = (current_user.qtde_ligar_para_policia or 0) + 1
    await db.commit()
    return {"success": True}

