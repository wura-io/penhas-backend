from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api import deps
from app.models.noticia import Noticia
from app.schemas.noticia import Noticia as NoticiaSchema
from app.db.session import get_db

router = APIRouter()

@router.get("/", response_model=List[NoticiaSchema])
async def read_noticias(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 20,
) -> Any:
    """
    Retrieve news.
    """
    result = await db.execute(select(Noticia).where(Noticia.published == 'published').order_by(Noticia.display_created_time.desc()).offset(skip).limit(limit))
    return result.scalars().all()

