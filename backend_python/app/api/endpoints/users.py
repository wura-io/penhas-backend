from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api import deps
from app.models.cliente import Cliente
from app.db.session import get_db
from app.helpers import cliente as cliente_helper

router = APIRouter()


class UpdateProfileRequest(BaseModel):
    """Update profile request"""
    apelido: str | None = None
    minibio: str | None = None
    raca: str | None = None
    nome_social: str | None = None


class ToggleRequest(BaseModel):
    """Toggle boolean field request"""
    active: bool


@router.get("/me")
async def read_user_me(
    current_user: Cliente = Depends(deps.get_current_user),
) -> Any:
    """
    Get current user profile
    Matches Perl GET /me endpoint
    """
    # Get user access modules based on gender
    modules = current_user.access_modules_as_config()
    
    # Build response matching Perl format
    return {
        "user_profile": {
            "avatar_url": current_user.avatar_url_or_default(),
            "ja_foi_vitima_de_violencia": bool(current_user.ja_foi_vitima_de_violencia),
            "modo_camuflado_ativo": bool(current_user.modo_camuflado_ativo),
            "modo_anonimo_ativo": bool(current_user.modo_anonimo_ativo),
            "email": current_user.email,
            "apelido": current_user.apelido,
            "cep": current_user.cep,
            "dt_nasc": current_user.dt_nasc.isoformat() if current_user.dt_nasc else None,
            "nome_completo": current_user.nome_completo,
            "genero": current_user.genero,
            "minibio": current_user.minibio,
            "raca": current_user.raca,
            "cpf_prefix": current_user.cpf_prefix,
            "nome_social": current_user.nome_social,
            "skills": [],  # TODO: Load from skills_cached JSON
            "badges": [],  # TODO: Load user badges
        },
        "app_config": {
            "modules": modules,
            "show_onboarding_assistente_reset": False,  # TODO: Implement quiz logic
        }
    }


@router.put("/me")
async def update_user_me(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    profile_data: UpdateProfileRequest
) -> Any:
    """
    Update current user profile
    Matches Perl PUT /me endpoint
    """
    # Update fields
    if profile_data.apelido is not None:
        current_user.apelido = profile_data.apelido
    if profile_data.minibio is not None:
        current_user.minibio = profile_data.minibio
    if profile_data.raca is not None:
        current_user.raca = profile_data.raca
    if profile_data.nome_social is not None:
        current_user.nome_social = profile_data.nome_social
    
    await db.commit()
    await db.refresh(current_user)
    
    return {"success": True}


@router.post("/me/modo-anonimo-toggle")
async def toggle_modo_anonimo(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    toggle_data: ToggleRequest
) -> Any:
    """
    Toggle anonymous mode
    Matches Perl POST /me/modo-anonimo-toggle
    """
    from datetime import datetime
    
    current_user.modo_anonimo_ativo = toggle_data.active
    current_user.modo_anonimo_atualizado_em = datetime.utcnow()
    
    await db.commit()
    
    return {"success": True, "modo_anonimo_ativo": toggle_data.active}


@router.post("/me/modo-camuflado-toggle")
async def toggle_modo_camuflado(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    toggle_data: ToggleRequest
) -> Any:
    """
    Toggle camouflage mode
    Matches Perl POST /me/modo-camuflado-toggle
    """
    from datetime import datetime
    
    current_user.modo_camuflado_ativo = toggle_data.active
    current_user.modo_camuflado_atualizado_em = datetime.utcnow()
    
    await db.commit()
    
    return {"success": True, "modo_camuflado_ativo": toggle_data.active}


@router.post("/me/ja-foi-vitima-de-violencia-toggle")
async def toggle_ja_foi_vitima(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    toggle_data: ToggleRequest
) -> Any:
    """
    Toggle violence victim status
    Matches Perl POST /me/ja-foi-vitima-de-violencia-toggle
    """
    from datetime import datetime
    
    current_user.ja_foi_vitima_de_violencia = toggle_data.active
    current_user.ja_foi_vitima_de_violencia_atualizado_em = datetime.utcnow()
    
    await db.commit()
    
    return {"success": True, "ja_foi_vitima_de_violencia": toggle_data.active}


@router.post("/me/call-police-pressed")
async def inc_call_police(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user)
) -> Any:
    """
    Increment police call counter
    Matches Perl POST /me/call-police-pressed
    """
    from app.models.activity import ClienteAtivacoesPolicia
    from datetime import datetime
    
    # Increment counter
    current_user.qtde_ligar_para_policia += 1
    
    # Log activation
    activation = ClienteAtivacoesPolicia(
        cliente_id=current_user.id,
        created_at=datetime.utcnow()
    )
    db.add(activation)
    
    await db.commit()
    
    return {"success": True}


@router.post("/report-profile")
async def report_profile(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    reported_cliente_id: int = Body(..., embed=True)
) -> Any:
    """
    Report another user's profile
    Matches Perl POST /report-profile
    """
    result = await cliente_helper.add_report_profile(
        db=db,
        cliente_id=current_user.id,
        reported_cliente_id=reported_cliente_id
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)
    
    return result


@router.post("/block-profile")
async def block_profile(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    blocked_cliente_id: int = Body(..., embed=True)
) -> Any:
    """
    Block another user's profile
    Matches Perl POST /block-profile
    """
    result = await cliente_helper.add_block_profile(
        db=db,
        cliente_id=current_user.id,
        blocked_cliente_id=blocked_cliente_id
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)
    
    return result

