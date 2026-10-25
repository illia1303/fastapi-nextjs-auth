import uuid

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.database import Base, get_async_session
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """
    Создаёт async engine для тестовой SQLite БД.
    scope="session" — один engine на весь прогон тестов.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Создаём все таблицы (аналог alembic upgrade head, но через SQLAlchemy)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine  # отдаём engine тестам

    # После всех тестов — удаляем таблицы и закрываем engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine):
    """
    Создаёт отдельную сессию БД для каждого теста.
    scope="function" — новая сессия на каждый тест, данные изолированы.

    Использует транзакцию с ROLLBACK — после каждого теста все изменения
    откатываются, БД остаётся чистой для следующего теста.
    """
    async_session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session
        # Откатываем все изменения, сделанные в этом тесте
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def anon_client(db_session):
    """
    Создаёт тестовый HTTP-клиент AsyncClient без авторизации.

    Подменяет зависимость get_async_session на тестовую сессию —
    это называется "Dependency Override" (переопределение зависимости).
    Благодаря этому API использует нашу изолированную тестовую БД.
    """
    async def override_get_async_session():
        yield db_session

    # Переопределяем зависимость FastAPI на тестовую
    app.dependency_overrides[get_async_session] = override_get_async_session

    # ASGITransport позволяет httpx общаться напрямую с FastAPI без HTTP-сервера
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    # Очищаем переопределение после теста
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def client(anon_client):
    """
    Авторизованный клиент: регистрирует нового пользователя и логинится.
    Бекенд ставит httpOnly cookie с токеном, httpx сохраняет её и шлёт
    со всеми следующими запросами — как браузер.

    Тестовая БД общая на весь прогон (commit сохраняет данные),
    поэтому email у каждого теста уникальный.
    """
    credentials = {"email": f"user-{uuid.uuid4().hex[:8]}@example.com", "password": "secret123"}
    await anon_client.post("/auth/register", json=credentials)
    await anon_client.post("/auth/login", json=credentials)
    yield anon_client



