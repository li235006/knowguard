"""
ORM 基础审计模型与通用字段混入 (Base Audit Model)

职责:
    - 提供通用主键 (id: UUID / BigInteger)
    - 提供自动创建时间 (created_at) 与更新时间 (updated_at)
    - 提供软删除标记 (is_deleted) 及审计属性

架构定位:
    持久化数据模型层 (Data Models)

作者:
    System Architect (系统架构组)
"""

from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class BaseModel(Base):
    """抽象持久化实体基类"""

    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
