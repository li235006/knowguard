"""
Pytest 全局测试固件与测试环境配置 (Test Fixtures)

职责:
    - 配置测试异步事件循环 (asyncio loop)
    - 提供测试专用内存/测试数据库会话固件
    - 提供测试用 FastAPI AsyncClient HTTP 客户端固件
    - 提供 Mock Redis 与测试用 UserContext 固件

架构定位:
    测试验证层 (Testing)

作者:
    System Architect (系统架构组)
"""

from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import AsyncClient
from main import app


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """HTTP 异步测试客户端固件存根"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
