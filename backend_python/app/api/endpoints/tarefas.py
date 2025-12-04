from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api import deps
from app.models.cliente import Cliente
from app.db.session import get_db
from app.helpers import cliente as cliente_helper

router = APIRouter()


class TarefaCreate(BaseModel):
    """Create custom task"""
    titulo: str
    descricao: str


class TarefaSyncItem(BaseModel):
    """Sync task item"""
    id: int
    status: str | None = None
    checkbox_feito: bool | None = None
    campo_livre: str | None = None


class TarefaSyncRequest(BaseModel):
    """Sync tasks request"""
    tasks: List[TarefaSyncItem]


class BatchSyncRequest(BaseModel):
    """Batch sync request"""
    tasks: List[TarefaSyncItem]


@router.get("/")
async def me_t_list(
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user)
) -> Any:
    """
    List user tasks (Manual de Fuga)
    Matches Perl GET /me/tarefas
    """
    result = await cliente_helper.cliente_lista_tarefas(
        db=db,
        user=current_user
    )
    return result


@router.post("/sync")
async def me_t_sync(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    sync_data: TarefaSyncRequest
) -> Any:
    """
    Sync task status
    Matches Perl POST /me/tarefas/sync
    """
    result = await cliente_helper.cliente_sync_lista_tarefas(
        db=db,
        user=current_user,
        tasks=[task.dict() for task in sync_data.tasks]
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)
    
    return result


@router.post("/nova")
async def me_t_nova(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    task_data: TarefaCreate
) -> Any:
    """
    Create new custom task
    Matches Perl POST /me/tarefas/nova
    """
    result = await cliente_helper.cliente_nova_tarefas(
        db=db,
        user=current_user,
        titulo=task_data.titulo,
        descricao=task_data.descricao
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)
    
    return result


@router.post("/batch")
async def me_t_batch_sync(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    batch_data: BatchSyncRequest
) -> Any:
    """
    Batch sync tasks
    Matches Perl POST /me/tarefas/batch
    """
    result = await cliente_helper.cliente_sync_lista_tarefas(
        db=db,
        user=current_user,
        tasks=[task.dict() for task in batch_data.tasks]
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)
    
    return result
