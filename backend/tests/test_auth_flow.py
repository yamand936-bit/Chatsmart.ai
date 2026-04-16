import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_login_success(client, db_session):
    # Create a test user first
    from app.models.user import User
    from app.core.security import get_password_hash
    user = User(email='test@test.com', hashed_password=get_password_hash('password123'), role='merchant')
    db_session.add(user)
    await db_session.commit()

    # Attempt login
    resp = await client.post('/api/auth/login', data={'username': 'test@test.com', 'password': 'password123'})
    assert resp.status_code == 200
    assert 'access_token' in resp.json()

@pytest.mark.asyncio
async def test_login_wrong_password(client):
    resp = await client.post('/api/auth/login', data={'username': 'x@x.com', 'password': 'wrong'})
    assert resp.status_code == 401

@pytest.mark.asyncio
async def test_rate_limit_login(client, mock_redis):
    mock_redis.execute = AsyncMock(return_value=[11, True])  # Simulate 11th attempt
    resp = await client.post('/api/auth/login', data={'username': 'x@x.com', 'password': 'x'})
    assert resp.status_code == 429
