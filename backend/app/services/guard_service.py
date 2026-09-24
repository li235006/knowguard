"""
四维细粒度数据权限与安全鉴权引擎 (4D Security Guard Service)

职责:
    - 核心铁律实现: 默认非公开 (Private-by-default)，四维实体 (全局/部门/角色/个人) 命中任意一维即放行 (OR 充分条件裁决，全不满足则拦截)
    - 知识单元 4D 权限策略持久化与读取 (PUT / GET policy)
    - 知识单元级鉴权裁决: evaluate_access(user_context, candidate_unit_ids) -> (allowed, restricted)
    - 批量切片级鉴权过滤: filter_allowed_chunks(user_ctx, chunk_ids) -> (allowed_chunks, restricted_chunks)
    - 超级管理员 (is_superuser / ROLE_SUPER_ADMIN) 具备系统级豁免直接放行
    - 核心脚本底嵌 if __name__ == '__main__': 闭环自测

架构定位:
    业务服务层 (Services Layer) / 模块三: 4D 权限与安全护栏 (核心基底)

作者:
    System Architect (系统架构组) & Backend Team
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundError
from app.models.knowledge import KnowledgeChunk, KnowledgeUnit
from app.models.policy import PermissionPolicy
from app.schemas.auth import UserContext
from app.schemas.guard import PermissionPolicyConfig

logger = logging.getLogger(__name__)


class GuardService:
    """4D 数据权限鉴权决策引擎"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # --------------------------------------------------------------------------
    # 1. 策略持久化与查询接口
    # --------------------------------------------------------------------------
    async def get_unit_policy(self, unit_id: int) -> Optional[PermissionPolicy]:
        """获取指定知识单元的四维权限策略 (若未配置返回 None)"""
        stmt = select(PermissionPolicy).where(PermissionPolicy.unit_id == unit_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def update_unit_policy(
        self, unit_id: int, policy_config: Union[PermissionPolicyConfig, Dict[str, Any]]
    ) -> PermissionPolicy:
        """
        创建或更新知识单元的四维权限配置
        支持 is_public 与 is_global 双向对齐
        """
        # 1. 验证目标知识单元必须存在
        doc_stmt = select(KnowledgeUnit).where(KnowledgeUnit.id == unit_id)
        doc_res = await self.db.execute(doc_stmt)
        doc = doc_res.scalar_one_or_none()
        if not doc:
            raise EntityNotFoundError(message=f"知识单元 ID={unit_id} 不存在", code=40401)

        # 2. 规范化配置入参
        if isinstance(policy_config, PermissionPolicyConfig):
            is_pub = policy_config.is_public
            dept_ids = list(policy_config.department_ids or [])
            r_ids = list(policy_config.role_ids or [])
            u_ids = list(policy_config.user_ids or [])
        else:
            is_pub = bool(policy_config.get("is_public", policy_config.get("is_global", False)))
            dept_ids = list(policy_config.get("department_ids", []))
            r_ids = list(policy_config.get("role_ids", []))
            u_ids = list(policy_config.get("user_ids", []))

        # 3. 查重或新增
        policy = await self.get_unit_policy(unit_id)
        if policy is None:
            policy = PermissionPolicy(
                unit_id=unit_id,
                is_public=is_pub,
                department_ids=dept_ids,
                role_ids=r_ids,
                user_ids=u_ids,
            )
            self.db.add(policy)
        else:
            policy.is_public = is_pub
            policy.department_ids = dept_ids
            policy.role_ids = r_ids
            policy.user_ids = u_ids

        await self.db.commit()
        await self.db.refresh(policy)
        logger.info(
            f"[GuardService] Updated 4D policy for unit_id={unit_id}: "
            f"public={policy.is_public}, depts={policy.department_ids}, roles={policy.role_ids}, users={policy.user_ids}"
        )
        return policy

    # --------------------------------------------------------------------------
    # 2. OR 充分条件单文档裁决引擎
    # --------------------------------------------------------------------------
    @staticmethod
    def evaluate_policy_rule(user_context: UserContext, policy: Optional[PermissionPolicy]) -> bool:
        """
        4D-RBAC 核心裁决语义 (OR 充分条件规则):
            1. 超管豁免: user.is_superuser 或具有 ROLE_SUPER_ADMIN 立即放行
            2. 默认非公开: 若未配置策略，默认拒绝
            3. 四维 OR 判定:
                - 维度 1: 全局公开 (is_public / is_global 为 True) -> 放行
                - 维度 2: 个人授权 (user_id 命中 policy.user_ids) -> 放行
                - 维度 3: 角色授权 (user.role_ids 与 policy.role_ids 有交集) -> 放行
                - 维度 4: 部门授权 (user.dept_id 命中 policy.department_ids) -> 放行
            4. 全不满足: 拦截拒绝
        """
        # 1. 超管豁免
        if user_context.is_superuser or "ROLE_SUPER_ADMIN" in (user_context.role_codes or []):
            return True

        # 2. 默认非公开安全屏障
        if policy is None:
            return False

        # 维度 1: 全局公开判定
        if policy.is_public or getattr(policy, "is_global", False):
            return True

        # 维度 2: 个人定向授权
        u_id = user_context.user_id
        if u_id is not None and u_id in (policy.user_ids or []):
            return True

        # 维度 3: 角色维度授权 (交集检查)
        user_role_ids: Set[int] = set(user_context.role_ids or [])
        policy_role_ids: Set[int] = set(policy.role_ids or [])
        if bool(user_role_ids & policy_role_ids):
            return True

        # 维度 4: 部门维度授权
        user_dept_id = user_context.dept_id
        if user_dept_id is not None and user_dept_id in (policy.department_ids or []):
            return True

        # 四维全未命中，坚决拦截
        return False

    # --------------------------------------------------------------------------
    # 3. 批量知识单元访问鉴权 (evaluate_access)
    # --------------------------------------------------------------------------
    async def evaluate_access(
        self, user_context: UserContext, candidate_unit_ids: List[int]
    ) -> Tuple[List[int], List[int]]:
        """
        批量计算知识单元放行集合与拦截集合
        联动规则: 停用状态 (DISABLED) 一票否决阻断放行
        返回: (allowed_unit_ids, restricted_unit_ids)
        """
        if not candidate_unit_ids:
            return [], []

        # 批量获取知识单元状态
        doc_stmt = select(KnowledgeUnit.id, KnowledgeUnit.status).where(KnowledgeUnit.id.in_(candidate_unit_ids))
        doc_res = await self.db.execute(doc_stmt)
        doc_status_map: Dict[int, str] = {row[0]: row[1] for row in doc_res.all()}

        # 批量获取全部策略
        stmt = select(PermissionPolicy).where(PermissionPolicy.unit_id.in_(candidate_unit_ids))
        res = await self.db.execute(stmt)
        policies = list(res.scalars().all())
        policy_map: Dict[int, PermissionPolicy] = {p.unit_id: p for p in policies}

        allowed: List[int] = []
        restricted: List[int] = []

        for u_id in candidate_unit_ids:
            # 1. 核心联动: 停用状态 (DISABLED) 一票否决，无论身份直接阻断
            status_val = doc_status_map.get(u_id, "").upper()
            if status_val == "DISABLED":
                restricted.append(u_id)
                continue

            # 2. 超管快速放行通道 (仅限非停用文档)
            if user_context.is_superuser or "ROLE_SUPER_ADMIN" in (user_context.role_codes or []):
                allowed.append(u_id)
                continue

            # 3. 四维 OR 判定规则
            pol = policy_map.get(u_id)
            if self.evaluate_policy_rule(user_context, pol):
                allowed.append(u_id)
            else:
                restricted.append(u_id)

        return allowed, restricted

    # --------------------------------------------------------------------------
    # 4. 批量切片级访问鉴权过滤 (filter_allowed_chunks)
    # --------------------------------------------------------------------------
    async def filter_allowed_chunks(
        self, user_ctx: UserContext, chunk_ids: List[int]
    ) -> Tuple[List[int], List[int]]:
        """
        批量切片访问鉴权过滤 (Requirement 4):
            输入: 用户上下文 user_ctx, 候选切片 ID 列表 chunk_ids
            返回: (allowed_chunks, restricted_chunks)
        """
        if not chunk_ids:
            return [], []

        # 批量查询切片获取所属 document_id
        chunk_stmt = select(KnowledgeChunk).where(KnowledgeChunk.id.in_(chunk_ids))
        chunk_res = await self.db.execute(chunk_stmt)
        chunks = list(chunk_res.scalars().all())
        chunk_map: Dict[int, KnowledgeChunk] = {c.id: c for c in chunks}

        # 收集切片涉及的全部文档 ID，统一调用 evaluate_access 进行 4D 与停用状态联合裁决
        doc_ids = list({c.document_id for c in chunks})
        allowed_doc_ids, _ = await self.evaluate_access(user_ctx, doc_ids)
        allowed_doc_set = set(allowed_doc_ids)

        allowed_chunks: List[int] = []
        restricted_chunks: List[int] = []

        for c_id in chunk_ids:
            chunk_obj = chunk_map.get(c_id)
            if chunk_obj and chunk_obj.document_id in allowed_doc_set:
                allowed_chunks.append(c_id)
            else:
                restricted_chunks.append(c_id)

        return allowed_chunks, restricted_chunks


# ==============================================================================
# 底嵌自测闭环脚本 (Self-Test Execution Block)
# ==============================================================================
if __name__ == "__main__":
    import asyncio
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import StaticPool
    from app.core.database import Base

    print("=== [Self-Test] Starting Guard Service Self-Test ===")

    async def _test_guard_service():
        test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool, echo=False)
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(bind=test_engine, expire_on_commit=False)

        async with session_factory() as session:
            service = GuardService(db=session)

            # 1. 创建基础数据：3 个文档及其切片
            doc_pub = KnowledgeUnit(title="公共规章.pdf", file_type="pdf", status="INDEXED")
            doc_dept = KnowledgeUnit(title="研发部规范.md", file_type="markdown", status="INDEXED")
            doc_secret = KnowledgeUnit(title="机密财报.pdf", file_type="pdf", status="INDEXED")
            session.add_all([doc_pub, doc_dept, doc_secret])
            await session.commit()
            await session.refresh(doc_pub)
            await session.refresh(doc_dept)
            await session.refresh(doc_secret)

            chunk1 = KnowledgeChunk(document_id=doc_pub.id, chunk_index=0, content="公共内容切片", status="indexed")
            chunk2 = KnowledgeChunk(document_id=doc_dept.id, chunk_index=0, content="研发部切片", status="indexed")
            chunk3 = KnowledgeChunk(document_id=doc_secret.id, chunk_index=0, content="机密财务切片", status="indexed")
            session.add_all([chunk1, chunk2, chunk3])
            await session.commit()
            await session.refresh(chunk1)
            await session.refresh(chunk2)
            await session.refresh(chunk3)

            # 2. 配置 4D 权限策略
            # 文档 1: 全局公开 (is_public=True)
            await service.update_unit_policy(doc_pub.id, PermissionPolicyConfig(is_public=True))
            # 文档 2: 授权给 研发部 (dept_id=2) 或 角色开发工程师 (role_id=20)
            await service.update_unit_policy(
                doc_dept.id,
                PermissionPolicyConfig(is_public=False, department_ids=[2], role_ids=[20])
            )
            # 文档 3: 仅授权特定个人 (user_id=888)
            await service.update_unit_policy(
                doc_secret.id,
                PermissionPolicyConfig(is_public=False, user_ids=[888])
            )
            print("[Self-Test] 3 documents and policies configured.")

            # 3. 构造 3 类不同上下文测试身份
            # 用户 A: 普通研发员工 (user_id=101, dept_id=2, role_ids=[20])
            user_rd = UserContext(
                user_id=101,
                employee_id="10101",
                username="rd_user",
                real_name="研发员工",
                dept_id=2,
                role_ids=[20],
                is_superuser=False,
            )

            # 用户 B: 财务部普通员工 (user_id=102, dept_id=3, role_ids=[30])
            user_finance = UserContext(
                user_id=102,
                employee_id="10102",
                username="fin_user",
                real_name="财务员工",
                dept_id=3,
                role_ids=[30],
                is_superuser=False,
            )

            # 用户 C: 超级管理员
            user_admin = UserContext(
                user_id=1,
                employee_id="10001",
                username="admin",
                real_name="超管",
                role_codes=["ROLE_SUPER_ADMIN"],
                is_superuser=True,
            )

            candidate_units = [doc_pub.id, doc_dept.id, doc_secret.id]
            candidate_chunks = [chunk1.id, chunk2.id, chunk3.id]

            # 4. 测试研发员工鉴权 (命中公共 + 研发部，拦截机密)
            allowed_u, restr_u = await service.evaluate_access(user_rd, candidate_units)
            assert doc_pub.id in allowed_u, "公开文档必须放行"
            assert doc_dept.id in allowed_u, "研发部门文档必须放行"
            assert doc_secret.id in restr_u, "机密文档必须拦截"
            print(f"[Self-Test] RD user evaluate_access verified: allowed={allowed_u}, restricted={restr_u}")

            # 5. 测试切片级过滤 (filter_allowed_chunks)
            allowed_c, restr_c = await service.filter_allowed_chunks(user_rd, candidate_chunks)
            assert chunk1.id in allowed_c
            assert chunk2.id in allowed_c
            assert chunk3.id in restr_c
            print(f"[Self-Test] RD user filter_allowed_chunks verified: allowed={allowed_c}, restricted={restr_c}")

            # 6. 测试财务员工鉴权 (仅命中公共文档，拦截研发和机密)
            allowed_fin, restr_fin = await service.evaluate_access(user_finance, candidate_units)
            assert allowed_fin == [doc_pub.id]
            assert set(restr_fin) == {doc_dept.id, doc_secret.id}
            print(f"[Self-Test] Finance user evaluate_access verified: allowed={allowed_fin}")

            # 7. 测试超管鉴权 (全量放行)
            allowed_adm, restr_adm = await service.evaluate_access(user_admin, candidate_units)
            assert len(allowed_adm) == 3
            assert len(restr_adm) == 0
            allowed_adm_c, restr_adm_c = await service.filter_allowed_chunks(user_admin, candidate_chunks)
            assert len(allowed_adm_c) == 3
            print(f"[Self-Test] Super admin evaluate_access verified: all 3 units allowed")

            # 8. 测试个人授权维度 (单独赋权给财务员工 user_id=102)
            await service.update_unit_policy(
                doc_secret.id,
                PermissionPolicyConfig(is_public=False, user_ids=[102])
            )
            allowed_fin_after, _ = await service.evaluate_access(user_finance, [doc_secret.id])
            assert doc_secret.id in allowed_fin_after, "个人定向授权命中必须放行"
            print("[Self-Test] Personal user_id authorization verified successfully")

            # 9. 测试停用状态 (DISABLED) 核心一票否决联动 (即便是超管也必须阻断)
            doc_pub.status = "DISABLED"
            await session.commit()
            allowed_dis_adm, restr_dis_adm = await service.evaluate_access(user_admin, [doc_pub.id])
            assert doc_pub.id in restr_dis_adm, "停用文档超管亦必须被拦截"
            assert doc_pub.id not in allowed_dis_adm
            allowed_dis_chunk, restr_dis_chunk = await service.filter_allowed_chunks(user_admin, [chunk1.id])
            assert chunk1.id in restr_dis_chunk, "停用文档切片必须被拦截"
            print("[Self-Test] DISABLED document status veto rule verified successfully for admin & chunks")

        await test_engine.dispose()
        print("=== [Self-Test] All Guard Service tests PASSED successfully! ===")

    asyncio.run(_test_guard_service())
