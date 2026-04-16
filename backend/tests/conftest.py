"""
Shared fixtures for backend tests.

Strategy:
- Set DATABASE_URL to a test SQLite file BEFORE importing any app modules,
  so the global engine in app.database points to the test DB.
- Session-scoped engine creates tables once per pytest run.
- autouse fixture truncates all tables between tests for isolation.
- `client` fixture overrides get_db so API calls hit the same test DB.
"""
import os

# Must be set before any app import so pydantic-settings picks them up
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_workmate.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models import user, conversation, message, skill, datasource  # noqa: ensure models are registered
from app.models.user import User
from app.core.security import hash_password, create_access_token

TEST_DB_URL = "sqlite+aiosqlite:///./test_workmate.db"


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()
    if os.path.exists("./test_workmate.db"):
        os.remove("./test_workmate.db")


@pytest_asyncio.fixture(autouse=True)
async def clear_tables(test_engine):
    """Delete all rows from every table after each test."""
    yield
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest_asyncio.fixture
async def db_session(test_engine):
    session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(test_engine):
    session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    user_obj = User(
        employee_id="testuser",
        password_hash=hash_password("testpass123"),
        display_name="Test User",
        is_active=True,
        is_admin=False,
    )
    db_session.add(user_obj)
    await db_session.commit()
    await db_session.refresh(user_obj)
    return user_obj


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession):
    user_obj = User(
        employee_id="adminuser",
        password_hash=hash_password("adminpass123"),
        display_name="Admin User",
        is_active=True,
        is_admin=True,
    )
    db_session.add(user_obj)
    await db_session.commit()
    await db_session.refresh(user_obj)
    return user_obj


@pytest_asyncio.fixture
async def auth_headers(test_user: User):
    token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_headers(admin_user: User):
    token = create_access_token(admin_user.id)
    return {"Authorization": f"Bearer {token}"}
