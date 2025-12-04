from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api import deps
from app.models.guardiao import ClientesGuardio
from app.models.cliente import Cliente
from app.schemas.guardiao import Guardiao, GuardiaoCreate
from app.db.session import get_db
from app.helpers import guardioes as guardioes_helper

router = APIRouter()


class AlertRequest(BaseModel):
    """Panic alert request"""
    latitude: str | None = None
    longitude: str | None = None


@router.get("/", response_model=List[dict])
async def read_guardioes(
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user)
) -> Any:
    """
    Retrieve user's guardians
    Matches Perl GET /me/guardioes
    """
    result = await guardioes_helper.list_guardioes(db=db, user=current_user)
    return result.get("rows", [])


@router.post("/", response_model=dict)
async def create_guardiao(
    *,
    db: AsyncSession = Depends(get_db),
    guardiao_in: GuardiaoCreate,
    current_user: Cliente = Depends(deps.get_current_user)
) -> Any:
    """
    Create new guardian invitation
    Matches Perl POST /me/guardioes
    """
    result = await guardioes_helper.create_guardiao(
        db=db,
        user=current_user,
        nome=guardiao_in.nome,
        celular_e164=guardiao_in.celular_e164
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)
    
    return result


@router.put("/{guard_id}")
async def update_guardiao(
    *,
    db: AsyncSession = Depends(get_db),
    guard_id: int,
    guardiao_in: GuardiaoCreate,
    current_user: Cliente = Depends(deps.get_current_user)
) -> Any:
    """
    Update guardian
    Matches Perl PUT /me/guardioes/:guard_id
    """
    result = await guardioes_helper.update_guardiao(
        db=db,
        user=current_user,
        guardiao_id=guard_id,
        nome=guardiao_in.nome,
        celular_e164=guardiao_in.celular_e164
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)
    
    return result


@router.delete("/{guard_id}")
async def delete_guardiao(
    *,
    db: AsyncSession = Depends(get_db),
    guard_id: int,
    current_user: Cliente = Depends(deps.get_current_user)
) -> Any:
    """
    Delete guardian
    Matches Perl DELETE /me/guardioes/:guard_id
    """
    result = await guardioes_helper.delete_guardiao(
        db=db,
        user=current_user,
        guardiao_id=guard_id
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result)
    
    return result


@router.post("/alert")
async def alert_guards(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    alert_data: AlertRequest
) -> Any:
    """
    Send panic alert to all active guardians
    Matches Perl POST /me/guardioes/alert
    """
    result = await guardioes_helper.alert_guards(
        db=db,
        user=current_user,
        latitude=alert_data.latitude,
        longitude=alert_data.longitude
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)
    
    return result
