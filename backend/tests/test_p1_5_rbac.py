"""
KnowGuard 阶段 P1-5 极简组织架构与 RBAC 角色权限测试套件 (test_p1_5_rbac.py)
严格执行大总管 MVP 极简铁律：单文件高密度覆核 3 大核心黄金断言:
  1. test_01_departments_tree_and_user_counts: 部门列表/树状结构生成及各部门成员人数统计 (member_count / user_count)
  2. test_02_user_lifecycle_and_freeze_toggle: 员工列表分页检索、新建、密码重置与冻结/解冻状态流转 (/api/v1/users, /status)
  3. test_03_roles_preset_and_permission_assignment: 5 大内置角色预置及其菜单/功能权限分配与更新 (/api/v1/roles, /permissions)
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import Department, Role, User
from app.services.iam_service import BUILTIN_ROLES, IAMService


def make_admin_headers() -> dict:
    """生成具备超级管理员权限的 Bearer Token 请求头"""
    token = create_access_token({
        "sub": "1",
        "user_id": 1,
        "employee_id": "ADMIN_P15",
        "username": "admin_p15",
        "real_name": "系统管理员",
        "is_superuser": True,
        "role_codes": ["ROLE_SUPER_ADMIN"],
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_01_departments_tree_and_user_counts(client: AsyncClient, db_session: AsyncSession):
    """黄金断言 1: 部门列表/树状结构生成及各部门成员人数统计 (member_count / user_count)"""
    headers = make_admin_headers()

    # 1. 递归创建 3 级部门体系 (管理层 -> 研发中心 / 财务中心 -> AI 算法组)
    # 根部门 (Level 1)
    res_root = await client.post("/api/v1/departments", json={
        "name": "集团管理层",
        "code": "DEPT_ROOT_P15",
        "parent_id": None,
        "leader_name": "王总",
    }, headers=headers)
    assert res_root.status_code == 200, f"创建根部门失败: {res_root.text}"
    root_data = res_root.json()["data"]
    root_id = root_data["id"]
    assert root_data["level"] == 1
    assert root_data["materialized_path"] == f"/{root_id}/"

    # 二级部门: 研发中心 (Level 2)
    res_tech = await client.post("/api/v1/departments", json={
        "name": "研发中心",
        "code": "DEPT_TECH_P15",
        "parent_id": root_id,
        "leader_name": "李总监",
    }, headers=headers)
    assert res_tech.status_code == 200
    tech_data = res_tech.json()["data"]
    tech_id = tech_data["id"]
    assert tech_data["level"] == 2
    assert tech_data["materialized_path"] == f"/{root_id}/{tech_id}/"

    # 二级部门: 财务中心 (Level 2)
    res_fin = await client.post("/api/v1/departments", json={
        "name": "财务中心",
        "code": "DEPT_FIN_P15",
        "parent_id": root_id,
        "leader_name": "张总监",
    }, headers=headers)
    assert res_fin.status_code == 200
    fin_id = res_fin.json()["data"]["id"]

    # 三级部门: AI 算法组 (Level 3)
    res_ai = await client.post("/api/v1/departments", json={
        "name": "AI算法组",
        "code": "DEPT_AI_P15",
        "parent_id": tech_id,
        "leader_name": "赵组长",
    }, headers=headers)
    assert res_ai.status_code == 200
    ai_data = res_ai.json()["data"]
    ai_id = ai_data["id"]
    assert ai_data["level"] == 3
    assert ai_data["materialized_path"] == f"/{root_id}/{tech_id}/{ai_id}/"

    # 2. 挂接员工至各个部门:
    # 研发中心分配 2 人，财务中心分配 1 人，AI 算法组分配 1 人，根部门 0 人
    users_to_create = [
        {"employee_id": "EMP_T01", "username": "dev01", "real_name": "研发一", "dept_id": tech_id},
        {"employee_id": "EMP_T02", "username": "dev02", "real_name": "研发二", "dept_id": tech_id},
        {"employee_id": "EMP_F01", "username": "fin01", "real_name": "财务一", "dept_id": fin_id},
        {"employee_id": "EMP_A01", "username": "ai01", "real_name": "算法一", "dept_id": ai_id},
    ]
    for u in users_to_create:
        u_res = await client.post("/api/v1/users", json={
            "employee_id": u["employee_id"],
            "username": u["username"],
            "real_name": u["real_name"],
            "password": "Password123456!",
            "department_id": u["dept_id"],
            "is_active": True,
        }, headers=headers)
        assert u_res.status_code == 200, f"创建用户 {u['username']} 失败: {u_res.text}"

    # 3. 调用 GET /api/v1/departments/tree 核验树结构完整性与各部门人数聚合统计
    tree_res = await client.get("/api/v1/departments/tree", headers=headers)
    assert tree_res.status_code == 200
    tree_json = tree_res.json()
    assert tree_json["code"] == 200
    tree_data = tree_json["data"]

    # 定位根节点
    root_node = next((d for d in tree_data if d["id"] == root_id), None)
    assert root_node is not None, "部门树中必须包含创建的根节点"
    assert root_node["level"] == 1
    # 根节点总成员数包含子部门全部成员 (2+1+1=4)，直属成员为 0
    assert root_node["member_count"] == 4
    assert root_node["user_count"] == 4
    assert root_node["direct_member_count"] == 0
    assert root_node["direct_user_count"] == 0
    assert len(root_node["children"]) == 2, "根部门下挂研发中心与财务中心两个子部门"

    # 核验研发中心及其子部门人数: 研发中心直属 2 人，AI组 1 人，总计 3 人
    tech_node = next((d for d in root_node["children"] if d["id"] == tech_id), None)
    assert tech_node is not None
    assert tech_node["level"] == 2
    assert tech_node["member_count"] == 3, "研发中心含下属AI组总人数为 3"
    assert tech_node["user_count"] == 3
    assert tech_node["direct_member_count"] == 2, "研发中心直属 2 名员工"
    assert tech_node["direct_user_count"] == 2
    assert len(tech_node["children"]) == 1

    ai_node = tech_node["children"][0]
    assert ai_node["id"] == ai_id
    assert ai_node["level"] == 3
    assert ai_node["materialized_path"] == f"/{root_id}/{tech_id}/{ai_id}/"
    assert ai_node["member_count"] == 1, "AI算法组分配了 1 名员工"
    assert ai_node["user_count"] == 1
    assert ai_node["direct_member_count"] == 1
    assert ai_node["direct_user_count"] == 1

    # 核验财务中心人数: 直属 1 人，无下级
    fin_node = next((d for d in root_node["children"] if d["id"] == fin_id), None)
    assert fin_node is not None
    assert fin_node["member_count"] == 1, "财务中心分配了 1 名员工"
    assert fin_node["user_count"] == 1
    assert fin_node["direct_member_count"] == 1
    assert fin_node["direct_user_count"] == 1
    assert len(fin_node["children"]) == 0

    print(f"\n✅ [黄金断言 1 通过] 部门 3 级递归树构建及各节点成员统计正确 (Root Total=4/Direct=0, Tech Total=3/Direct=2, Fin=1, AI=1)")


@pytest.mark.asyncio
async def test_02_user_lifecycle_and_freeze_toggle(client: AsyncClient, db_session: AsyncSession):
    """黄金断言 2: 员工列表分页检索、新建、密码重置与冻结/解冻状态流转 (/api/v1/users, /status)"""
    headers = make_admin_headers()

    # 1. 新建员工 (验证 Bcrypt 12 工作因子密码加密)
    create_payload = {
        "employee_id": "EMP_P15_001",
        "username": "tester_lifecycle",
        "real_name": "生命周期测试员",
        "password": "InitialSecretPassword123!",
        "email": "lifecycle@knowguard.com",
        "phone": "13800001501",
        "is_active": True,
    }
    create_res = await client.post("/api/v1/users", json=create_payload, headers=headers)
    assert create_res.status_code == 200, f"新建员工失败: {create_res.text}"
    user_data = create_res.json()["data"]
    user_id = user_data["id"]
    assert user_data["real_name"] == "生命周期测试员"
    assert user_data["is_active"] is True

    # 底层数据库物理校验 Bcrypt 12 工作因子
    db_stmt = select(User).where(User.id == user_id)
    user_db = (await db_session.execute(db_stmt)).scalar_one()
    assert user_db.hashed_password.startswith("$2b$12$"), "用户初始密码必须强制采用 Bcrypt 12 工作因子加盐哈希"

    # 2. 分页列表检索与关键字过滤
    list_res = await client.get("/api/v1/users?page=1&page_size=10&keyword=tester_lifecycle", headers=headers)
    assert list_res.status_code == 200
    paginated = list_res.json()["data"]
    assert paginated["total"] >= 1
    assert paginated["page"] == 1
    assert paginated["page_size"] == 10
    assert any(u["id"] == user_id and u["username"] == "tester_lifecycle" for u in paginated["items"])

    # 3. 员工信息修改与密码重置 (PUT /api/v1/users/{id})
    update_res = await client.put(f"/api/v1/users/{user_id}", json={
        "real_name": "生命周期测试员_已重命名",
        "email": "new_email@knowguard.com",
        "password": "NewUpdatedPassword456!",
    }, headers=headers)
    assert update_res.status_code == 200
    assert update_res.json()["data"]["real_name"] == "生命周期测试员_已重命名"

    # 验证旧密码失效，新密码可成功登录
    old_login = await client.post("/api/v1/auth/login", json={
        "username": "tester_lifecycle",
        "password": "InitialSecretPassword123!",
    })
    assert old_login.status_code == 400
    assert old_login.json()["code"] == 40001

    new_login = await client.post("/api/v1/auth/login", json={
        "username": "tester_lifecycle",
        "password": "NewUpdatedPassword456!",
    })
    assert new_login.status_code == 200
    assert "access_token" in new_login.json()["data"]

    # 4. 账号冻结流转 (PATCH /api/v1/users/{id}/status -> is_active=False)
    freeze_res = await client.patch(f"/api/v1/users/{user_id}/status", json={"is_active": False}, headers=headers)
    assert freeze_res.status_code == 200
    assert freeze_res.json()["data"] is True

    # 验证冻结后登录被严格阻断 (401 / code=40101)
    frozen_login = await client.post("/api/v1/auth/login", json={
        "username": "tester_lifecycle",
        "password": "NewUpdatedPassword456!",
    })
    assert frozen_login.status_code == 401
    assert frozen_login.json()["code"] == 40101
    assert "停用" in frozen_login.json()["message"]

    # 5. 账号解冻流转 (PATCH /api/v1/users/{id}/status -> is_active=True)
    unfreeze_res = await client.patch(f"/api/v1/users/{user_id}/status", json={"is_active": True}, headers=headers)
    assert unfreeze_res.status_code == 200
    assert unfreeze_res.json()["data"] is True

    # 验证解冻后重新登录正常
    unfrozen_login = await client.post("/api/v1/auth/login", json={
        "username": "tester_lifecycle",
        "password": "NewUpdatedPassword456!",
    })
    assert unfrozen_login.status_code == 200
    assert "access_token" in unfrozen_login.json()["data"]

    print(f"\n✅ [黄金断言 2 通过] 员工生命周期 CRUD、Bcrypt 12 哈希、密码重置及冻结/解冻状态流转验证通过")


@pytest.mark.asyncio
async def test_03_roles_preset_and_permission_assignment(client: AsyncClient, db_session: AsyncSession):
    """黄金断言 3: 5 大内置角色预置及其菜单/功能权限分配与更新 (/api/v1/roles, /permissions)"""
    headers = make_admin_headers()

    # 1. 验证 5 大系统内置角色全量预置 (GET /api/v1/roles)
    roles_res = await client.get("/api/v1/roles", headers=headers)
    assert roles_res.status_code == 200, f"获取角色列表失败: {roles_res.text}"
    roles_list = roles_res.json()["data"]
    assert len(roles_list) >= 5, f"系统内置角色至少应有 5 个，当前获取到: {len(roles_list)}"

    role_code_map = {r["code"]: r for r in roles_list}
    expected_builtin_roles = [
        "ROLE_SUPER_ADMIN",
        "ROLE_KNOWLEDGE_ADMIN",
        "ROLE_COMMON_USER",
        "ROLE_HRBP",
        "ROLE_DEPT_MANAGER",
    ]
    for b_code in expected_builtin_roles:
        assert b_code in role_code_map, f"预置内置角色 {b_code} 缺失"
        role_item = role_code_map[b_code]
        assert role_item["is_system"] is True, f"内置角色 {b_code} 的 is_system 属性必须为 True"
        assert role_item["status"] is True

    # 2. 创建自定义业务角色 (POST /api/v1/roles)
    custom_role_payload = {
        "name": "安全与合规审计专员",
        "code": "ROLE_SEC_AUDITOR_P15",
        "description": "专职安全合规审计与外发管控",
        "status": True,
        "permission_codes": ["chat:menu", "chat:view"],
    }
    create_role_res = await client.post("/api/v1/roles", json=custom_role_payload, headers=headers)
    assert create_role_res.status_code == 200, f"创建自定义角色失败: {create_role_res.text}"
    new_role = create_role_res.json()["data"]
    new_role_id = new_role["id"]
    assert new_role["code"] == "ROLE_SEC_AUDITOR_P15"
    assert new_role["is_system"] is False, "自定义角色 is_system 属性必须为 False"
    assert "chat:menu" in new_role["permission_codes"]

    # 3. 动态配置/更新角色细粒度 RBAC 权限 (PUT /api/v1/roles/{id}/permissions)
    target_perms = [
        "knowledge:menu",
        "knowledge:view",
        "knowledge:upload",
        "analytics:view",
        "audit:export",
    ]
    perm_res = await client.put(f"/api/v1/roles/{new_role_id}/permissions", json={
        "permission_codes": target_perms,
    }, headers=headers)
    assert perm_res.status_code == 200, f"更新角色权限失败: {perm_res.text}"
    updated_role = perm_res.json()["data"]
    assert set(updated_role["permission_codes"]) == set(target_perms)
    assert set(updated_role["permissions"]) == set(target_perms)

    # 数据库物理层与接口持久化核验
    db_session.expire_all()
    service = IAMService(db_session)
    assigned_roles = await service.list_roles()
    fresh_custom_role = next((r for r in assigned_roles if r.id == new_role_id), None)
    assert fresh_custom_role is not None
    assert set(fresh_custom_role.permission_codes) == set(target_perms)

    # 接口侧再次拉取核验
    get_roles_res = await client.get("/api/v1/roles", headers=headers)
    assert get_roles_res.status_code == 200
    fresh_role_api = next((r for r in get_roles_res.json()["data"] if r["id"] == new_role_id), None)
    assert fresh_role_api is not None
    assert set(fresh_role_api["permission_codes"]) == set(target_perms)

    # 4. 获取三级 RBAC 授权树模板 (GET /api/v1/roles/permissions/tree)
    tree_res = await client.get("/api/v1/roles/permissions/tree", headers=headers)
    assert tree_res.status_code == 200
    tree_nodes = tree_res.json()["data"]
    assert len(tree_nodes) >= 1

    # 核验三级层级结构: 菜单 (menu) -> 路由 (route) -> 按钮 (button)
    menu_types = set()
    route_types = set()
    btn_types = set()

    for menu in tree_nodes:
        assert menu["type"] == "menu", f"第一级节点必须为 menu 类型, 当前: {menu['type']}"
        menu_types.add(menu["type"])
        assert len(menu["children"]) > 0, f"菜单节点 {menu['label']} 必须包含路由下级"
        for route in menu["children"]:
            assert route["type"] == "route", f"第二级节点必须为 route 类型, 当前: {route['type']}"
            route_types.add(route["type"])
            for btn in route["children"]:
                assert btn["type"] == "button", f"第三级节点必须为 button 类型, 当前: {btn['type']}"
                btn_types.add(btn["type"])
                assert len(btn["children"]) == 0, "按钮节点为叶子节点，不得有子级"

    assert "menu" in menu_types and "route" in route_types and "button" in btn_types
    print(f"\n✅ [黄金断言 3 通过] 5 大内置角色预置、自定义角色创建、RBAC 细粒度权限动态更新与 3 级权限树拓扑验证全部通过")
