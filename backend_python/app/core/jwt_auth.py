"""
JWT Authentication with session validation
Port from Perl Penhas::Controller::JWT
100% compatible with Perl API JWT format
"""
from typing import Optional, Dict, Any
from fastapi import Header, Query, HTTPException, status
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.redis_client import get_redis
from app.models.onboarding import ClientesActiveSession
from app.models.cliente import Cliente


class JWTAuthException(HTTPException):
    """Custom JWT authentication exception"""
    pass


async def decode_and_validate_jwt(
    token: str,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Decode and validate JWT token with session validation
    Matches Perl's check_user_jwt behavior
    
    Returns dict with user_id, session_id, and user object
    Raises JWTAuthException if invalid
    """
    try:
        # Decode JWT
        claims = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
    except JWTError as e:
        raise JWTAuthException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "expired_jwt", "message": "Bad request - Invalid JWT"}
        )
    
    # Check if it's a user token (matches Perl: typ == 'usr')
    if not claims or claims.get('typ') != 'usr':
        raise JWTAuthException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_jwt", "message": "Invalid token type"}
        )
    
    # Get session ID from claims
    session_id = claims.get('ses')
    if not session_id:
        raise JWTAuthException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_jwt", "message": "Missing session ID"}
        )
    
    # Use Redis cache to get user_id from session_id (matches Perl behavior)
    redis_client = get_redis()
    cache_key = f"CaS:{session_id}"
    
    def get_user_id_from_db():
        """Callback to get user_id from database"""
        # This needs to be sync for redis callback, we'll handle it differently
        return None
    
    # Check cache first
    user_id_cached = redis_client.get(cache_key)
    
    if user_id_cached:
        user_id = int(user_id_cached) if user_id_cached else None
    else:
        # Query database for active session
        result = await db.execute(
            select(ClientesActiveSession.cliente_id)
            .where(ClientesActiveSession.id == session_id)
        )
        user_id = result.scalar_one_or_none()
        
        # Cache for 5 minutes (300 seconds) - matches Perl
        if user_id:
            redis_client.setex(cache_key, 300, str(user_id))
        else:
            # Cache empty result briefly to avoid repeated DB queries
            redis_client.setex(cache_key, 60, "")
    
    if not user_id:
        raise JWTAuthException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "jwt_logout",
                "message": "Está sessão não está mais válida (Usuário saiu)"
            }
        )
    
    # Get user from database
    result = await db.execute(
        select(Cliente)
        .where(Cliente.id == user_id)
        .where(Cliente.status == 'active')
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise JWTAuthException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "user_not_found",
                "message": "User not found or inactive"
            }
        )
    
    return {
        'user_id': user_id,
        'session_id': session_id,
        'cache_key': cache_key,
        'user': user
    }


async def get_current_user_from_token(
    db: AsyncSession,
    api_key: Optional[str] = Query(None, description="JWT token via query param"),
    x_api_key: Optional[str] = Header(None, description="JWT token via header")
) -> Cliente:
    """
    Get current user from JWT token
    Checks both query param 'api_key' and header 'x-api-key'
    Matches Perl's check_user_jwt behavior
    """
    # Get token from query param or header (matches Perl priority)
    jwt_token = api_key or x_api_key
    
    if not jwt_token:
        raise JWTAuthException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "missing_jwt", "message": "Not Authenticated"}
        )
    
    # Decode and validate
    auth_data = await decode_and_validate_jwt(jwt_token, db)
    
    return auth_data['user']


def create_user_jwt_token(session_id: int) -> str:
    """
    Create JWT token for user session
    Matches Perl's JWT format with 'typ' and 'ses' claims
    """
    payload = {
        'typ': 'usr',  # Matches Perl: typ == 'usr'
        'ses': session_id  # Session ID, matches Perl
    }
    
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token

