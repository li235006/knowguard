"""
模块 M1 部门组织架构 8 级递归树自动化测试套件 (test_m1_departments.py)

测试范围:
    - 部门 8 级树形层级依次创建与物化路径闭包生成
    - 超过 8 级最深限制时的边界拦截阻断 (40001)
    - 部门树形结构 (DepartmentTreeResponse) 完整递归组装
    - 删除非叶子节点 (包含子部门) 严格拦截
    - 删除包含在职员工的部门严格拦截
    - 叶子节点安全删除
    - 循环移动父子节点检测防御

作者:
    Backend Team & QA
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessLogicError
from app.schemas.user import DepartmentCreate, UserCreate, UserUpdate
from app.services.iam_service import IAMService


@pytest.mark.asyncio
async def test_department_8_levels_creation_and_materialized_path(db_session: AsyncSession):
    """测试完整创建 8 级部门树与物化路径编码计算"""
    service = IAMService(db_session)

    # 1. 创建根部门 (Level 1)
    root = await service.create_department(DepartmentCreate(
        name="集团总部",
        code="DEPT_ROOT",
        parent_id=None,
        leader_name="总部总经理",
    ))
    assert root.level == 1
    assert root.materialized_path == f"/{root.id}/"

    # 2. 逐级创建至第 8 级
    current_parent = root
    created_depts = [root]
    for lvl in range(2, 9):
        child = await service.create_department(DepartmentCreate(
            name=f"第{lvl}级分支部门",
            code=f"DEPT_LVL_{lvl}",
            parent_id=current_parent.id,
            leader_name=f"主管_{lvl}",
        ))
        assert child.level == lvl
        assert child.materialized_path == f"{current_parent.materialized_path}{child.id}/"
        created_depts.append(child)
        current_parent = child

    assert len(created_depts) == 8
    leaf_node = created_depts[-1]
    assert leaf_node.level == 8

    # 3. 验证向第 8 级叶子节点继续添加第 9 级节点时被严格拦截
    with pytest.raises(BusinessLogicError) as exc_info:
        await service.create_department(DepartmentCreate(
            name="第9级非法部门",
            code="DEPT_LVL_9",
            parent_id=leaf_node.id,
        ))
    assert "8 级" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_department_tree_api_serialization(client: AsyncClient, db_session: AsyncSession):
    """测试部门树 API 的层级递归嵌套序列化"""
    service = IAMService(db_session)

    # 创建一级和二级结构
    dept_a = await service.create_department(DepartmentCreate(
        name="华东大区", code="EAST_CHINA", parent_id=None, sort_order=1
    ))
    dept_b = await service.create_department(DepartmentCreate(
        name="华南大区", code="SOUTH_CHINA", parent_id=None, sort_order=2
    ))
    dept_a1 = await service.create_department(DepartmentCreate(
        name="上海分公司", code="SHANGHAI_BR", parent_id=dept_a.id, sort_order=1
    ))
    dept_a2 = await service.create_department(DepartmentCreate(
        name="杭州分公司", code="HANGZHOU_BR", parent_id=dept_a.id, sort_order=2
    ))

    # 生成管理员访问 Token
    user = await service.create_user(UserCreate(
        employee_id="ADMIN001",
        username="admin_dept",
        real_name="部门管理员",
        password="AdminPassword123",
        is_superuser=True,
    ))
    login_res = await client.post("/api/v1/auth/login", json={"username": "ADMIN001", "password": "AdminPassword123"})
    token = login_res.json()["data"]["access_token"]

    tree_res = await client.get("/api/v1/departments/tree", headers={"Authorization": f"Bearer {token}"})
    assert tree_res.status_code == 200
    res_data = tree_res.json()["data"]
    assert len(res_data) == 2  # 两个根部门

    east_node = next(d for d in res_data if d["code"] == "EAST_CHINA")
    assert len(east_node["children"]) == 2
    child_codes = [c["code"] for c in east_node["children"]]
    assert "SHANGHAI_BR" in child_codes
    assert "HANGZHOU_BR" in child_codes


@pytest.mark.asyncio
async def test_delete_department_protection_rules(client: AsyncClient, db_session: AsyncSession):
    """测试删除部门的硬性保护机制：非叶子节点与关联员工阻断"""
    service = IAMService(db_session)

    parent_dept = await service.create_department(DepartmentCreate(
        name="技术研发中心", code="R_AND_D", parent_id=None
    ))
    child_dept = await service.create_department(DepartmentCreate(
        name="AI实验室", code="AI_LAB", parent_id=parent_dept.id
    ))

    # 1. 尝试删除包含子部门的父节点 -> 阻断
    with pytest.raises(BusinessLogicError) as exc_sub:
        await service.delete_department(parent_dept.id)
    assert "包含下级子部门" in str(exc_sub.value.message)

    # 2. 在子部门关联员工
    user = await service.create_user(UserCreate(
        employee_id="99001",
        username="researcher1",
        real_name="AI科学家",
        password="Password123!",
        department_id=child_dept.id,
    ))

    # 3. 尝试删除包含在职员工的子部门 -> 阻断
    with pytest.raises(BusinessLogicError) as exc_user:
        await service.delete_department(child_dept.id)
    assert "存在关联员工" in str(exc_user.value.message)

    # 4. 将员工转移或删除后，叶子节点允许成功删除
    await service.update_user(user.id, UserUpdate(department_id=None))  # 解绑部门
    user.department_id = None
    await db_session.commit()

    delete_ok = await service.delete_department(child_dept.id)
    assert delete_ok is True

    # 5. 子部门删除后，父节点变为叶子节点，也可以成功删除
    parent_delete_ok = await service.delete_department(parent_dept.id)
    assert parent_delete_ok is True


@pytest.mark.asyncio
async def test_department_cycle_prevention(db_session: AsyncSession):
    """测试防止循环引用的安全校验 (禁止将部门移动至其子孙部门下)"""
    service = IAMService(db_session)
    d1 = await service.create_department(DepartmentCreate(name="D1", code="D1", parent_id=None))
    d2 = await service.create_department(DepartmentCreate(name="D2", code="D2", parent_id=d1.id))
    d3 = await service.create_department(DepartmentCreate(name="D3", code="D3", parent_id=d2.id))

    # 尝试将 D1 的父级改为 D3 (形成环路)
    from app.schemas.user import DepartmentUpdate
    with pytest.raises(BusinessLogicError) as exc:
        await service.update_department(d1.id, DepartmentUpdate(parent_id=d3.id))
    assert "循环引用" in str(exc.value.message)
