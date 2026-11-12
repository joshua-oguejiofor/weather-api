from collections.abc import AsyncGenerator
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
import redis.asyncio as aioredis
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core import redis_server
from app.core.config import settings
from app.core.database import Base, get_db
from app.core.redis_server import get_redis
from app.core.security import create_email_verification_token
from app.main import app
from app.middleware.rate_limit import limiter
from app.models import User


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    
    engine = create_async_engine(
        settings.TEST_DATABASE_URL, 
        echo=False,
        poolclass=NullPool,
        )
    
    yield engine
    await engine.dispose()
    
    
@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def setup_database(test_engine: AsyncEngine) -> AsyncGenerator[None, None]:
    
    async with test_engine.begin() as engine:
        await engine.run_sync(Base.metadata.drop_all)
        await engine.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as engine:
        await engine.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session(
    test_engine: AsyncEngine, 
    setup_database: None
    ) -> AsyncGenerator[AsyncSession, None]:
    
    async with test_engine.connect() as conn:
        transaction = await conn.begin()
        
        TestSessionLocal = async_sessionmaker(
            bind=conn, 
            class_=AsyncSession, 
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
            join_transaction_mode="create_savepoint",
            )
        
        async with TestSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()
                if transaction.is_active:
                    await session.rollback()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def test_redis(monkeypatch: pytest.MonkeyPatch) -> AsyncGenerator[aioredis.Redis, None]:
    """Use a throw-away Redis DB for every test.

    The app helpers (get_cache, set_cache, is_token_blacklisted, ...) read the
    module-level ``redis_server.redis_client``, so it has to be patched on that
    module. Rebinding a name inside conftest does nothing, and the real client
    is tied to the first event loop it is used on, which is closed after the
    test ("Event loop is closed").
    """
    test_client = aioredis.from_url(
        url=settings.TEST_REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )
    await test_client.flushdb()
    monkeypatch.setattr(redis_server, "redis_client", test_client)

    yield test_client

    await test_client.flushdb()
    await test_client.aclose()


@pytest.fixture(autouse=True)
def disable_rate_limit():
    """Rate limits (5/minute on login etc.) are stored in Redis and would make tests flaky."""
    previous = limiter.enabled
    limiter.enabled = False
    yield
    limiter.enabled = previous


@pytest.fixture(autouse=True)
def mock_celery_tasks(monkeypatch: pytest.MonkeyPatch) -> dict[str, MagicMock]:
    """Never enqueue real emails/Celery jobs during tests."""
    from app.celery_server import celery_tasks

    mocks = {}
    for name in dir(celery_tasks):
        task = getattr(celery_tasks, name)
        if hasattr(task, "delay"):
            mock = MagicMock()
            monkeypatch.setattr(task, "delay", mock)
            mocks[name] = mock
    return mocks


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession, test_redis: aioredis.Redis) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def override_redis():
        return test_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_redis

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as c:
            yield c
    finally:
        app.dependency_overrides.clear()


USER = {
    "email": "test@weather.com",
    "password": "SecurePass1",
    "first_name": "Jane",
    "last_name": "Doe",
    "preferred_unit": "imperial",
}

BASE_URL = "/api/v1/auth"


@pytest_asyncio.fixture(scope="function")
async def registered_user(client: AsyncClient, db_session: AsyncSession) -> dict:
    """Register USER and verify the email, so the account is able to log in."""
    reg = await client.post(f"{BASE_URL}/register", json=USER)
    assert reg.status_code == 201, reg.text
    assert reg.json()["msg"]

    user = (await db_session.execute(
        select(User).where(User.email == USER["email"])
    )).scalar_one()

    token = create_email_verification_token({"sub": str(user.id)})
    verify = await client.get(f"{BASE_URL}/verify-email?token={token}")
    assert verify.status_code == 302, verify.text
    return {"email": USER["email"], "password": USER["password"]}


@pytest_asyncio.fixture(scope="function")
async def logged_user(client: AsyncClient, registered_user: dict) -> AsyncClient:
    """An AsyncClient that is already authenticated as USER."""
    response = await client.post(
        f"{BASE_URL}/login",
        data={"username": registered_user["email"], "password": registered_user["password"]},
    )
    assert response.status_code == 200, f"error during login {response.text}"
    body = response.json()
    assert body["refresh_token"]
    assert isinstance(body["access_token"], str)

    client.headers["Authorization"] = f"Bearer {body['access_token']}"
    return client

