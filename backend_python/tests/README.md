# PenhaS Python Backend - Testing Guide

## 🧪 Testing Infrastructure

This directory contains the complete testing suite for the PenhaS Python backend.

## 📁 Test Structure

```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── test_auth.py            # Authentication and security tests
├── test_integration.py     # API integration tests
├── test_e2e.py            # End-to-end user flow tests
└── README.md              # This file
```

## 🚀 Running Tests

### Run all tests
```bash
poetry run pytest
```

### Run specific test file
```bash
poetry run pytest tests/test_auth.py
```

### Run with coverage
```bash
poetry run pytest --cov=app --cov-report=html
```

### Run with verbose output
```bash
poetry run pytest -v -s
```

### Run only fast tests (skip slow integration tests)
```bash
poetry run pytest -m "not slow"
```

## 📊 Test Categories

### Unit Tests (`test_auth.py`)
- ✅ Password hashing and verification
- ✅ JWT token creation and validation
- ✅ Legacy SHA256 password support
- ✅ Utility functions (PII removal, UUID validation)
- ✅ User model operations

**Coverage**: Core security and business logic

### Integration Tests (`test_integration.py`)
- ✅ API endpoint responses
- ✅ Authentication flows
- ✅ Database operations
- ✅ Error handling
- ✅ OpenAPI schema generation

**Coverage**: Full request/response cycles

### E2E Tests (`test_e2e.py`)
- ✅ Complete user registration flow
- ✅ Guardian management flow
- ✅ Timeline interaction flow
- ✅ Password reset flow
- ✅ Chat functionality
- ✅ Audio management
- ✅ Admin workflows

**Coverage**: Complete user journeys

## 🔧 Configuration

### Test Database
Tests use a separate test database: `penhas_test`

Configure in `.env`:
```bash
POSTGRESQL_DBNAME=penhas
# Test database will be penhas_test
```

### Fixtures
Common fixtures are defined in `conftest.py`:
- `db`: AsyncSession for database operations
- `event_loop`: Async event loop
- `engine`: Test database engine
- `sample_user_data`: Sample user data

## 📝 Writing New Tests

### Unit Test Example
```python
def test_something():
    """Test description"""
    result = function_to_test()
    assert result == expected_value
```

### Async Test Example
```python
@pytest.mark.asyncio
async def test_async_function(db: AsyncSession):
    """Test async function"""
    result = await async_function(db)
    assert result is not None
```

### Integration Test Example
```python
@pytest.mark.asyncio
async def test_endpoint():
    """Test API endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/endpoint")
        assert response.status_code == 200
```

## 🎯 Coverage Goals

Target coverage by module:
- **Core modules**: 80%+
- **Helpers**: 70%+
- **Endpoints**: 60%+
- **Overall**: 70%+

## 🔍 Test Organization Best Practices

1. **One test file per module** or logical grouping
2. **Use descriptive test names** that explain what's being tested
3. **Arrange-Act-Assert** pattern:
   ```python
   def test_something():
       # Arrange - Set up test data
       data = setup_data()
       
       # Act - Execute the code
       result = function_under_test(data)
       
       # Assert - Check results
       assert result == expected
   ```
4. **Use fixtures** for common setup
5. **Mock external services** (AWS, Google Maps, etc.)

## 🐛 Debugging Tests

### Run with print statements
```bash
pytest -v -s
```

### Run specific test
```bash
pytest tests/test_auth.py::TestPasswordHashing::test_password_hash
```

### Drop into debugger on failure
```bash
pytest --pdb
```

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Async Testing](https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html)

## ✅ Test Checklist

Before merging code, ensure:
- [ ] All tests pass
- [ ] New features have tests
- [ ] Coverage hasn't decreased
- [ ] Integration tests pass
- [ ] E2E flows work
- [ ] No warnings or errors

## 🎉 Testing Status

**Current Status**: Infrastructure ready, example tests implemented

**Next Steps**:
1. Run full test suite: `pytest`
2. Generate coverage report: `pytest --cov=app --cov-report=html`
3. Review coverage and add tests for uncovered code
4. Set up CI/CD to run tests automatically

---

*The testing infrastructure is production-ready and awaits comprehensive test implementation!*

