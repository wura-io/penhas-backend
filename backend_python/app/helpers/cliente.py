"""
Cliente (User) helper module
Port from Perl Penhas::Helpers::Cliente
Business logic for user management, profiles, and Manual de Fuga
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from datetime import datetime
import json

from app.models.cliente import Cliente
from app.models.minor import MfClienteTarefa, MfTarefa, ClienteTag, MfTag
from app.models.blocking import ClienteBloqueio, ClientesReport


async def add_report_profile(
    db: AsyncSession,
    cliente_id: int,
    reported_cliente_id: int,
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Report another user profile
    Matches Perl's add_report_profile
    """
    # Check if already reported
    result = await db.execute(
        select(ClientesReport)
        .where(ClientesReport.cliente_id == cliente_id)
        .where(ClientesReport.reported_cliente_id == reported_cliente_id)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        return {"error": "already_reported", "message": "Você já reportou este perfil"}
    
    # Create report
    report = ClientesReport(
        cliente_id=cliente_id,
        reported_cliente_id=reported_cliente_id,
        reason=reason,
        created_at=datetime.utcnow()
    )
    db.add(report)
    await db.commit()
    
    return {"success": True}


async def add_block_profile(
    db: AsyncSession,
    cliente_id: int,
    blocked_cliente_id: int
) -> Dict[str, Any]:
    """
    Block another user profile
    Matches Perl's add_block_profile
    """
    # Check if already blocked
    result = await db.execute(
        select(ClienteBloqueio)
        .where(ClienteBloqueio.cliente_id == cliente_id)
        .where(ClienteBloqueio.blocked_cliente_id == blocked_cliente_id)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        return {"error": "already_blocked", "message": "Você já bloqueou este perfil"}
    
    # Create block
    block = ClienteBloqueio(
        cliente_id=cliente_id,
        blocked_cliente_id=blocked_cliente_id,
        created_at=datetime.utcnow()
    )
    db.add(block)
    await db.commit()
    
    return {"success": True}


async def remove_blocked_profile(
    db: AsyncSession,
    cliente_id: int,
    blocked_cliente_id: int
) -> Dict[str, Any]:
    """
    Unblock a user profile
    Matches Perl's remove_blocked_profile
    """
    result = await db.execute(
        delete(ClienteBloqueio)
        .where(ClienteBloqueio.cliente_id == cliente_id)
        .where(ClienteBloqueio.blocked_cliente_id == blocked_cliente_id)
    )
    await db.commit()
    
    if result.rowcount > 0:
        return {"success": True}
    else:
        return {"error": "not_blocked", "message": "Este perfil não estava bloqueado"}


async def cliente_lista_tarefas(
    db: AsyncSession,
    user: Cliente
) -> Dict[str, Any]:
    """
    List user tasks (Manual de Fuga)
    Matches Perl's cliente_lista_tarefas
    """
    if not user.is_female():
        return {"rows": []}
    
    # Get user's tasks
    result = await db.execute(
        select(MfClienteTarefa)
        .where(MfClienteTarefa.cliente_id == user.id)
        .where(MfClienteTarefa.removido_em.is_(None))
        .order_by(MfClienteTarefa.created_at)
    )
    tasks = result.scalars().all()
    
    rows = []
    for task in tasks:
        rows.append({
            "id": task.id,
            "titulo": task.titulo,
            "descricao": task.descricao,
            "status": task.status,
            "checkbox_feito": task.checkbox_feito,
            "campo_livre": task.campo_livre,
            "created_at": task.created_at.isoformat() if task.created_at else None,
        })
    
    return {"rows": rows}


async def cliente_sync_lista_tarefas(
    db: AsyncSession,
    user: Cliente,
    tasks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Sync task status (Manual de Fuga)
    Matches Perl's cliente_sync_lista_tarefas
    """
    if not user.is_female():
        return {"success": False, "error": "not_allowed"}
    
    for task_data in tasks:
        task_id = task_data.get('id')
        if not task_id:
            continue
        
        # Update task
        await db.execute(
            update(MfClienteTarefa)
            .where(MfClienteTarefa.id == task_id)
            .where(MfClienteTarefa.cliente_id == user.id)
            .values(
                status=task_data.get('status'),
                checkbox_feito=task_data.get('checkbox_feito', False),
                campo_livre=task_data.get('campo_livre')
            )
        )
    
    await db.commit()
    return {"success": True}


async def cliente_nova_tarefas(
    db: AsyncSession,
    user: Cliente,
    titulo: str,
    descricao: str
) -> Dict[str, Any]:
    """
    Create new custom task (Manual de Fuga)
    Matches Perl's cliente_nova_tarefas
    """
    if not user.is_female():
        return {"success": False, "error": "not_allowed"}
    
    # Create new task
    task = MfClienteTarefa(
        cliente_id=user.id,
        titulo=titulo,
        descricao=descricao,
        status="pending",
        checkbox_feito=False,
        created_at=datetime.utcnow()
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    return {
        "success": True,
        "task": {
            "id": task.id,
            "titulo": task.titulo,
            "descricao": task.descricao,
            "status": task.status,
            "checkbox_feito": task.checkbox_feito,
            "created_at": task.created_at.isoformat() if task.created_at else None
        }
    }


async def cliente_mf_clear_tasks(
    db: AsyncSession,
    user: Cliente
) -> Dict[str, Any]:
    """
    Clear/remove all Manual de Fuga tasks
    Matches Perl's cliente_mf_clear_tasks
    """
    # Mark all tasks as removed
    await db.execute(
        update(MfClienteTarefa)
        .where(MfClienteTarefa.cliente_id == user.id)
        .where(MfClienteTarefa.removido_em.is_(None))
        .values(removido_em=datetime.utcnow())
    )
    await db.commit()
    
    return {"success": True}


async def cliente_mf_add_tarefa_por_codigo(
    db: AsyncSession,
    user: Cliente,
    codigos: List[str]
) -> Dict[str, Any]:
    """
    Add tasks by code (Manual de Fuga)
    Matches Perl's cliente_mf_add_tarefa_por_codigo
    """
    # Get tasks by codes
    result = await db.execute(
        select(MfTarefa)
        .where(MfTarefa.token.in_(codigos))
    )
    tarefas = result.scalars().all()
    
    if not tarefas:
        return {"success": False, "error": "tasks_not_found"}
    
    # Get existing tasks
    result = await db.execute(
        select(MfClienteTarefa.mf_tarefa_id)
        .where(MfClienteTarefa.cliente_id == user.id)
        .where(MfClienteTarefa.mf_tarefa_id.in_([t.id for t in tarefas]))
        .where(MfClienteTarefa.removido_em.is_(None))
    )
    existing_ids = {row[0] for row in result.all()}
    
    # Add new tasks
    added_count = 0
    for tarefa in tarefas:
        if tarefa.id not in existing_ids:
            task = MfClienteTarefa(
                cliente_id=user.id,
                mf_tarefa_id=tarefa.id,
                titulo=tarefa.titulo,
                descricao=tarefa.descricao,
                status="pending",
                checkbox_feito=False,
                created_at=datetime.utcnow()
            )
            db.add(task)
            added_count += 1
    
    await db.commit()
    
    return {"success": True, "added": added_count}


async def cliente_mf_add_tag_by_code(
    db: AsyncSession,
    user: Cliente,
    codigos: List[str]
) -> Dict[str, Any]:
    """
    Add tags by code (Manual de Fuga)
    Matches Perl's cliente_mf_add_tag_by_code
    """
    # Get tags by codes
    result = await db.execute(
        select(MfTag)
        .where(MfTag.code.in_(codigos))
    )
    tags = result.scalars().all()
    
    if not tags:
        return {"success": False, "error": "tags_not_found"}
    
    # Get existing tags
    result = await db.execute(
        select(ClienteTag.mf_tag_id)
        .where(ClienteTag.cliente_id == user.id)
        .where(ClienteTag.mf_tag_id.in_([t.id for t in tags]))
    )
    existing_ids = {row[0] for row in result.all()}
    
    # Add new tags
    added_count = 0
    for tag in tags:
        if tag.id not in existing_ids:
            cliente_tag = ClienteTag(
                cliente_id=user.id,
                mf_tag_id=tag.id,
                created_at=datetime.utcnow()
            )
            db.add(cliente_tag)
            added_count += 1
    
    await db.commit()
    
    return {"success": True, "added": added_count}

