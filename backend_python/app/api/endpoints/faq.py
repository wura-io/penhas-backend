from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api import deps
from app.db.session import get_db
from app.models.minor import FaqTelaSobre, FaqTelaSobreCategoria

router = APIRouter()

@router.get("/")
async def list_faq(
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    List FAQs.
    """
    result = await db.execute(
        select(FaqTelaSobre)
        .where(FaqTelaSobre.status == 'published')
        .order_by(FaqTelaSobre.sort)
    )
    faqs = result.scalars().all()
    # Group by category logic needed if fully replicating Perl structure
    return faqs

@router.get("/{faq_id}")
async def get_faq_detail(
    faq_id: int,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get FAQ detail.
    """
    faq = await db.get(FaqTelaSobre, faq_id)
    return faq

