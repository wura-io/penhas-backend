"""
Unit tests for authentication and JWT
Demonstrates testing infrastructure is ready
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.jwt_auth import decode_jwt_token
from app.models.cliente import Cliente


class TestPasswordHashing:
    """Test password hashing and verification"""
    
    def test_password_hash(self):
        """Test password hashing"""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert verify_password(password, hashed)
    
    def test_password_verify_wrong_password(self):
        """Test password verification fails with wrong password"""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        assert not verify_password("WrongPassword", hashed)
    
    def test_legacy_sha256_support(self):
        """Test legacy SHA256 password support"""
        # Legacy SHA256 hash of "password"
        legacy_hash = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"
        
        # Should verify with legacy password
        assert verify_password("password", legacy_hash)


class TestJWTTokens:
    """Test JWT token creation and verification"""
    
    def test_create_access_token(self):
        """Test JWT token creation"""
        user_id = 123
        session_id = "test-session-123"
        
        token = create_access_token(user_id=user_id, session_id=session_id)
        
        assert token is not None
        assert len(token) > 0
        assert isinstance(token, str)
    
    def test_decode_valid_token(self):
        """Test decoding valid JWT token"""
        user_id = 123
        session_id = "test-session-123"
        
        token = create_access_token(user_id=user_id, session_id=session_id)
        payload = decode_jwt_token(token)
        
        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["ses"] == session_id
        assert payload["typ"] == "access_token"
    
    def test_decode_invalid_token(self):
        """Test decoding invalid JWT token"""
        invalid_token = "invalid.token.here"
        
        payload = decode_jwt_token(invalid_token)
        assert payload is None
    
    def test_decode_expired_token(self):
        """Test decoding expired JWT token"""
        from app.core.jwt_auth import jwt
        from app.core.config import settings
        
        # Create expired token
        expires_delta = timedelta(seconds=-1)  # Already expired
        expire = datetime.utcnow() + expires_delta
        
        to_encode = {
            "sub": "123",
            "ses": "test-session",
            "typ": "access_token",
            "exp": expire
        }
        
        token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
        payload = decode_jwt_token(token)
        
        assert payload is None


@pytest.mark.asyncio
async def test_user_creation(db: AsyncSession):
    """Test user model creation"""
    user = Cliente(
        email="test@example.com",
        senha=get_password_hash("password123"),
        nome_completo="Test User",
        apelido="testuser",
        active=True,
        created_at=datetime.utcnow()
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.apelido == "testuser"
    assert user.active is True


@pytest.mark.asyncio
async def test_user_query(db: AsyncSession):
    """Test querying users"""
    from sqlalchemy import select
    
    # Create test user
    user = Cliente(
        email="query@example.com",
        senha=get_password_hash("password123"),
        apelido="queryuser",
        active=True
    )
    
    db.add(user)
    await db.commit()
    
    # Query user
    result = await db.execute(
        select(Cliente).where(Cliente.email == "query@example.com")
    )
    found_user = result.scalar_one_or_none()
    
    assert found_user is not None
    assert found_user.email == "query@example.com"
    assert found_user.apelido == "queryuser"


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_remove_pii_cpf(self):
        """Test PII removal for CPF"""
        from app.utils import remove_pii
        
        text = "My CPF is 123.456.789-00"
        cleaned = remove_pii(text)
        
        assert "123.456.789-00" not in cleaned
        assert "[CPF_OCULTO]" in cleaned
    
    def test_remove_pii_email(self):
        """Test PII removal for email"""
        from app.utils import remove_pii
        
        text = "Contact me at test@example.com"
        cleaned = remove_pii(text)
        
        assert "test@example.com" not in cleaned
        assert "[EMAIL_OCULTO]" in cleaned
    
    def test_random_string_generation(self):
        """Test random string generation"""
        from app.utils import random_string
        
        s1 = random_string(16)
        s2 = random_string(16)
        
        assert len(s1) == 16
        assert len(s2) == 16
        assert s1 != s2  # Should be different
    
    def test_validate_uuid(self):
        """Test UUID validation"""
        from app.utils import is_uuid_valid
        import uuid
        
        valid_uuid = str(uuid.uuid4())
        invalid_uuid = "not-a-uuid"
        
        assert is_uuid_valid(valid_uuid) is True
        assert is_uuid_valid(invalid_uuid) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

