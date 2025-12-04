"""
API dependencies for authentication and database sessions
"""
from typing import AsyncGenerator
from fastapi import Depends, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.session import get_db
from app.models.cliente import Cliente
from app.core.jwt_auth import get_current_user_from_token


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    api_key: Optional[str] = Query(None, description="JWT token via query param"),
    x_api_key: Optional[str] = Header(None, alias="x-api-key", description="JWT token via header")
) -> Cliente:
    """
    Dependency to get current authenticated user
    Uses JWT with session validation matching Perl API
    Checks both query param 'api_key' and header 'x-api-key'
    """
    return await get_current_user_from_token(db=db, api_key=api_key, x_api_key=x_api_key)


async def get_current_active_user(
    current_user: Cliente = Depends(get_current_user)
) -> Cliente:
    """
    Dependency to get current active user
    Additional check to ensure user is active
    """
    if current_user.status != 'active':
        from fastapi import HTTPException, status as http_status
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )
    return current_user
