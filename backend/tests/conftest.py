"""
Pytest 全局测试固件与测试环境配置 (Test Fixtures)

职责:
    - 提供测试专用内存 SQLite 异步引擎与数据库会话固件
    - 提供 FastAPI AsyncClient HTTP 客户端固件 (自动注入 dependency_overrides)
    - 自动初始化 5 大内置角色与测试用户数据

架构定位:
    测试验证层 (Testing)

作者:
    System Architect (系统架构组) & Backend Team
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.services.iam_service import IAMService
from main import app

# 测试专用内存 SQLite 异步引擎
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """会话级测试数据库引擎"""
    engine = create_async_engine(TEST_DB_URL, poolclass=StaticPool, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """每个用例独享的数据库会话 (测试前后建表与删表保证隔离)"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=test_engine, expire_on_commit=False, autoflush=False)
    async with session_maker() as session:
        # 初始化 5 大内置角色
        service = IAMService(session)
        await service.init_builtin_roles_and_permissions()
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """测试用 HTTP 异步客户端，自动重载 get_db 依赖"""
    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
