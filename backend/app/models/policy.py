"""
四维细粒度数据权限策略实体模型 (PermissionPolicy)

职责:
    - 知识单元与数据访问权限的映射策略配置
    - 支撑四维实体映射: 全局公开 (is_public/is_global)、部门列表 (department_ids)、角色列表 (role_ids)、个人列表 (user_ids)
    - 遵循 OR 充分条件裁决语义与写时展开机制

架构定位:
    持久化数据模型层 (Data Models) / 模块三: 4D 权限与安全护栏 (MySQL 8.0+)

作者:
    System Architect (系统架构组) & Backend Team
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, ForeignKey, Integer, JSON, select
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class PermissionPolicy(BaseModel):
    """
    四维细粒度权限策略实体 (MySQL 8.0+)
    映射维度:
        1. 全局公开: is_public (兼容 is_global)
        2. 部门授权: department_ids (JSON 数组)
        3. 角色授权: role_ids (JSON 数组)
        4. 个人授权: user_ids (JSON 数组)
    """
    __tablename__ = "permission_policies"

    unit_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("knowledge_units.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="关联知识单元主表 ID"
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否全员公开 (True 则跳过部门/角色/个人检查)"
    )
    department_ids: Mapped[List[int]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="授权部门 ID 列表 (JSON Array)"
    )
    role_ids: Mapped[List[int]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="授权角色 ID 列表 (JSON Array)"
    )
    user_ids: Mapped[List[int]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="授权特定员工用户 ID 列表 (JSON Array)"
    )

    @property
    def is_global(self) -> bool:
        """前端与全局策略兼容别名"""
        return self.is_public

    @is_global.setter
    def is_global(self, val: bool) -> None:
        self.is_public = val

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "unit_id": self.unit_id,
            "is_public": self.is_public,
            "is_global": self.is_public,
            "department_ids": self.department_ids or [],
            "role_ids": self.role_ids or [],
            "user_ids": self.user_ids or [],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def __repr__(self) -> str:
        return f"<PermissionPolicy unit_id={self.unit_id} public={self.is_public} depts={len(self.department_ids)}>"


# ==============================================================================
# 底嵌自测闭环脚本 (Self-Test Execution Block)
# ==============================================================================
if __name__ == "__main__":
    import asyncio
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import StaticPool
    from app.core.database import Base
    from app.models.knowledge import KnowledgeUnit

    print("=== [Self-Test] Starting PermissionPolicy Model Self-Test ===")

    async def _test_policy_model():
        test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool, echo=False)
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(bind=test_engine, expire_on_commit=False)

        async with session_factory() as session:
            # 1. 创建前置知识单元
            doc = KnowledgeUnit(
                title="战略规划2026.pdf",
                file_type="pdf",
                file_size=5000,
                status="INDEXED"
            )
            session.add(doc)
            await session.commit()
            await session.refresh(doc)

            # 2. 创建四维权限策略
            policy = PermissionPolicy(
                unit_id=doc.id,
                is_public=False,
                department_ids=[1, 2],
                role_ids=[10, 20],
                user_ids=[10086, 10087]
            )
            session.add(policy)
            await session.commit()
            await session.refresh(policy)

            assert policy.id is not None
            assert policy.unit_id == doc.id
            assert policy.is_public is False
            assert policy.is_global is False
            assert len(policy.department_ids) == 2
            assert len(policy.role_ids) == 2
            assert len(policy.user_ids) == 2
            print(f"[Self-Test] Created PermissionPolicy for Unit ID={doc.id}: {policy}")

            # 3. 验证更新 is_global 别名同步
            policy.is_global = True
            await session.commit()
            await session.refresh(policy)
            assert policy.is_public is True
            print("[Self-Test] is_global property setter synchronization verified")

            # 4. 验证级联查询
            stmt = select(PermissionPolicy).where(PermissionPolicy.unit_id == doc.id)
            res = await session.execute(stmt)
            queried = res.scalar_one_or_none()
            assert queried is not None
            assert queried.unit_id == doc.id
            print("[Self-Test] PermissionPolicy query by unit_id verified successfully")

        await test_engine.dispose()
        print("=== [Self-Test] All PermissionPolicy Model tests PASSED successfully! ===")

    asyncio.run(_test_policy_model())
