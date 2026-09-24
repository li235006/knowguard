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
    System Architect (系统架构组)
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 声明式模型基类存根"""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖注入: 获取异步数据库会话存根 (MySQL 8.0+ 连接池)"""
    pass
    yield
    pass
