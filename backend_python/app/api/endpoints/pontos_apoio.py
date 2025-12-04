from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api import deps
from app.models.ponto_apoio import PontoApoio
from app.schemas.ponto_apoio import PontoApoio as PontoApoioSchema
from app.db.session import get_db

router = APIRouter()

@router.get("/", response_model=List[PontoApoioSchema])
async def read_pontos_apoio(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve pontos de apoio.
    """
    result = await db.execute(select(PontoApoio).offset(skip).limit(limit))
    return result.scalars().all()

