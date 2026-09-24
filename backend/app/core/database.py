"""
数据库异步引擎与会话生命周期管理模块

职责:
    - 创建与维护 SQLAlchemy 2.0 AsyncEngine 异步连接池 (适配 MySQL 8.0+ 及 aiomysql 驱动)
    - 提供 async_sessionmaker 异步会话生成器
    - 提供 FastAPI 依赖注入项 get_db()
    - 声明 ORM 模型统一基类 Base (DeclarativeBase)

架构定位:
    核心底层支撑层 (Core Infrastructure) / 关系数据库基础设施 (MySQL 8.0+)

输入/输出契约:
    - 输入: settings.DATABASE_URL (mysql+aiomysql)
    - 输出: AsyncEngine, AsyncSession 依赖生成器

作者:
    System Architect (系统架构组) & Backend Team
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 声明式模型统一基类"""
    pass


# 默认配置引擎 (适配 MySQL 8.0+ 异步连接池)
# 当处于 SQLite 测试环境或特殊 URI 时自动调整 pool 参数
connect_args = {}
engine_kwargs = {
    "echo": settings.DB_ECHO,
}

if "sqlite" in settings.DATABASE_URL:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
    engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
    engine_kwargs["pool_pre_ping"] = True

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖注入: 获取异步数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
