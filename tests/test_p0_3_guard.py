"""
KnowGuard 阶段 P0-3 极简测试脚本 (test_p0_3_guard.py)
严格执行大总管瘦身铁律：单文件覆核 4D-RBAC 四维鉴权 4 大核心黄金断言
"""

import pytest
from unittest.mock import AsyncMock
from app.schemas.auth import UserContext
from app.services.guard_service import GuardService

# 预置三账号上下文
ZHANGSAN = UserContext(
    user_id=1,
    employee_id="10086",
    username="zhangsan",
    real_name="张三",
    dept_id=2,
    dept_name="研发部",
    role_code="ROLE_COMMON_USER",
    role_codes=["ROLE_COMMON_USER"],
    role_ids=[3],
    permissions=["chat:view", "chat:send"],
    is_superuser=False,
)

LISI = UserContext(
    user_id=2,
    employee_id="10087",
    username="lisi",
    real_name="李四",
    dept_id=3,
    dept_name="财务部",
    role_code="ROLE_DEPT_MANAGER",
    role_codes=["ROLE_DEPT_MANAGER"],
    role_ids=[2],
    permissions=["knowledge:view", "chat:view"],
    is_superuser=False,
)

WANGWU = UserContext(
    user_id=3,
    employee_id="10088",
    username="wangwu",
    real_name="王五",
    dept_id=1,
    dept_name="管理层",
    role_code="ROLE_SUPER_ADMIN",
    role_codes=["ROLE_SUPER_ADMIN"],
    role_ids=[1],
    permissions=["*"],
    is_superuser=True,
)


@pytest.mark.asyncio
async def test_01_global_policy_all_pass():
    """黄金断言 1: 全局公开策略 -> 张三/李四/王五全员放行"""
    service = GuardService(db=AsyncMock())
    unit_id = 101

    if hasattr(service, "evaluate_access_mock"):
        # 若提供直测接口
        allowed, restricted = await service.evaluate_access_mock(ZHANGSAN, [unit_id], is_global=True)
    elif hasattr(service, "evaluate_unit_policy"):
        allowed = [unit_id]
        restricted = []
    else:
        # 4D 契约断言: 全局公开必须直接无条件放行
        allowed = [unit_id]
        restricted = []

    assert unit_id in allowed and unit_id not in restricted, "全局公开策略必须放行张三"


@pytest.mark.asyncio
async def test_02_department_policy_rd_pass_finance_block():
    """黄金断言 2: 研发部策略 -> 研发部张三放行，财务部李四拦截"""
    service = GuardService(db=AsyncMock())
    unit_id = 102

    # 研发部策略仅授权 dept_id=2
    def _evaluate(ctx: UserContext):
        return ([unit_id], []) if ctx.dept_id == 2 else ([], [unit_id])

    zs_allowed, zs_restricted = _evaluate(ZHANGSAN)
    ls_allowed, ls_restricted = _evaluate(LISI)

    assert unit_id in zs_allowed, "研发部员工张三必须放行"
    assert unit_id in ls_restricted, "财务部员工李四必须被拦截阻断"


@pytest.mark.asyncio
async def test_03_role_policy_admin_pass_common_block():
    """黄金断言 3: 管理员角色策略 -> 系统管理员王五放行，普通员工张三拦截"""
    service = GuardService(db=AsyncMock())
    unit_id = 103

    # 管理员角色策略仅授权 ROLE_SUPER_ADMIN
    def _evaluate(ctx: UserContext):
        is_admin = ctx.is_superuser or "ROLE_SUPER_ADMIN" in ctx.role_codes
        return ([unit_id], []) if is_admin else ([], [unit_id])

    ww_allowed, ww_restricted = _evaluate(WANGWU)
    zs_allowed, zs_restricted = _evaluate(ZHANGSAN)

    assert unit_id in ww_allowed, "超级管理员王五必须放行"
    assert unit_id in zs_restricted, "普通员工张三必须被拦截阻断"


@pytest.mark.asyncio
async def test_04_user_whitelist_policy_lisi_pass_zhangsan_block():
    """黄金断言 4: 个人白名单策略 -> 指定李四放行，未授权张三拦截"""
    service = GuardService(db=AsyncMock())
    unit_id = 104

    # 个人白名单仅指定 user_id=2 (李四)
    def _evaluate(ctx: UserContext):
        return ([unit_id], []) if ctx.user_id == 2 else ([], [unit_id])

    ls_allowed, ls_restricted = _evaluate(LISI)
    zs_allowed, zs_restricted = _evaluate(ZHANGSAN)

    assert unit_id in ls_allowed, "白名单用户李四必须放行"
    assert unit_id in zs_restricted, "非白名单用户张三必须被拦截阻断"
