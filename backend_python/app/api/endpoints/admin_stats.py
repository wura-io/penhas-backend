from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import time
import jwt
from datetime import datetime, timedelta

from app.api import deps
from app.db.session import get_db
from app.models.minor import AdminBigNumber
from app.core.config import settings

router = APIRouter()

@router.get("/bignum")
async def get_admin_bignums(
    db: AsyncSession = Depends(get_db),
    # current_admin = Depends(deps.get_current_admin) # TODO: Implement admin auth dep
) -> Any:
    """
    Get big numbers for admin dashboard.
    """
    # Fetch queries
    result = await db.execute(select(AdminBigNumber).where(AdminBigNumber.status == 'published').order_by(AdminBigNumber.sort))
    bignums = result.scalars().all()
    
    results = []
    start_time = time.time()
    
    for row in bignums:
        # Execute raw SQL stored in DB
        # CAUTION: This is dangerous if SQL is not sanitized. 
        # In Perl it was: $c->schema2->storage->dbh->selectrow_array($r->{sql})
        try:
            sql_res = await db.execute(text(row.sql))
            number = sql_res.scalar()
            results.append({
                "id": row.id,
                "label": row.label,
                "number": number,
                "background_class": row.background_class,
                "text_class": row.text_class
            })
        except Exception as e:
            results.append({
                "id": row.id,
                "label": row.label,
                "number": "Error",
                "error": str(e)
            })
            
    elapsed = time.time() - start_time
    
    # Metabase Embedding logic (Ported from Perl)
    metabase_secret = settings.SECRET_KEY # Placeholder, usually distinct
    dashboards = [
        {"name": 'Aplicativo PenhaS', "resource": {"dashboard": 4}},
        {"name": 'Twitter Penha',     "resource": {"dashboard": 5}},
    ]
    reports = []
    
    for dash in dashboards:
        payload = {
            "resource": dash["resource"],
            "params": {},
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, metabase_secret, algorithm="HS256")
        url = f"https://analytics.penhas.com.br/embed/dashboard/{token}#bordered=false&titled=false"
        reports.append({"name": dash["name"], "url": url})

    return {
        "results": results,
        "reports": reports,
        "elapsed": elapsed
    }

