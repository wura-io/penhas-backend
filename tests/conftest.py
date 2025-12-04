"""
Pytest configuration and fixtures
"""
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base_class import Base


# Test database URL (use separate test database)
TEST_DATABASE_URL = settings.SQLALCHEMY_DATABASE_URI.replace(
    settings.POSTGRESQL_DBNAME,
    f"{settings.POSTGRESQL_DBNAME}_test"
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    """Create test database engine"""
    test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield test_engine
    
    # Drop all tables after tests
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await test_engine.dispose()


@pytest.fixture
async def db(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests"""
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture(autouse=True)
async def cleanup_db(db: AsyncSession):
    """Cleanup database after each test"""
    yield
    # Rollback any uncommitted changes
    await db.rollback()


# Add any other common fixtures here
@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "nome_completo": "Test User",
        "apelido": "testuser",
        "cpf": "12345678900",
        "dt_nasc": "1990-01-01"
    }

