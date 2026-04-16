import pytest, pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.main import app
from app.db.session import get_db
from app.db.base import Base

from unittest.mock import AsyncMock, patch

@pytest_asyncio.fixture
async def db_session():
    # Use in-memory SQLite for tests (fast, no Docker needed)
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine) as session:
        yield session

@pytest_asyncio.fixture
async def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(app=app, base_url='http://test') as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def mock_redis():
    with patch('app.api.routers.auth.redis_client') as mock:
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock()
        mock.incr = AsyncMock(return_value=1)
        mock.expire = AsyncMock()
        mock.pipeline = lambda: mock
        mock.execute = AsyncMock(return_value=[1, True])
        yield mock
