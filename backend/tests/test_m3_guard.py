"""
模块 M3 4D-RBAC 细粒度数据鉴权与安全护栏自动化测试套件 (test_m3_guard.py)

测试范围:
    1. 策略持久化: GET 与 PUT /api/v1/guard/units/{unit_id}/policy
    2. 前端兼容路径: GET 与 PUT /api/v1/guard/policies/{unit_id}
    3. 四维 OR 判定引擎:
        - 维度 1: 全局公开 (is_public / is_global) 全员放行
        - 维度 2: 部门定向授权 (department_ids)
        - 维度 3: 角色定向授权 (role_ids)
        - 维度 4: 个人定向授权 (user_ids)
        - 超级管理员豁免全量放行
        - 四维均不命中坚决拦截阻断
    4. 批量切片级鉴权过滤: GuardService.filter_allowed_chunks(user_ctx, chunk_ids)
    5. API 决策接口: POST /api/v1/guard/check-access 与 POST /api/v1/guard/check-chunks

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

from app.core.security import create_access_token
from app.models.knowledge import KnowledgeChunk, KnowledgeUnit
from app.schemas.auth import UserContext
from app.schemas.guard import PermissionPolicyConfig
from app.services.guard_service import GuardService


@pytest.mark.asyncio
async def test_4d_policy_crud_and_frontend_alias_api(client: AsyncClient, db_session: AsyncSession):
    """测试 4D 策略查询与更新 API (包括 /units/{id}/policy 和 /policies/{id})"""
    doc = KnowledgeUnit(title="薪酬福利手册.pdf", file_type="pdf", status="INDEXED")
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    # 1. 查询默认未配置策略 (默认非公开)
    get_res = await client.get(f"/api/v1/guard/units/{doc.id}/policy")
    assert get_res.status_code == 200
    p_data = get_res.json()["data"]
    assert p_data["unit_id"] == doc.id
    assert p_data["is_public"] is False
    assert p_data["is_global"] is False
    assert p_data["department_ids"] == []

    # 2. 更新策略 (PUT /guard/units/{id}/policy)
    put_res = await client.put(
        f"/api/v1/guard/units/{doc.id}/policy",
        json={
            "is_public": False,
            "department_ids": [2],
            "role_ids": [10, 20],
            "user_ids": [10086],
        },
    )
    assert put_res.status_code == 200
    updated_data = put_res.json()["data"]
    assert updated_data["department_ids"] == [2]
    assert updated_data["role_ids"] == [10, 20]
    assert updated_data["user_ids"] == [10086]

    # 3. 前端兼容路径测试 (GET & PUT /guard/policies/{id})
    alias_get = await client.get(f"/api/v1/guard/policies/{doc.id}")
    assert alias_get.status_code == 200
    assert alias_get.json()["data"]["user_ids"] == [10086]

    alias_put = await client.put(
        f"/api/v1/guard/policies/{doc.id}",
        json={"is_global": True, "department_ids": []},
    )
    assert alias_put.status_code == 200
    assert alias_put.json()["data"]["is_global"] is True
    assert alias_put.json()["data"]["is_public"] is True


@pytest.mark.asyncio
async def test_guard_service_or_condition_all_dimensions(db_session: AsyncSession):
    """测试 GuardService 四维 OR 判定充分条件（命中任一维即放行，全不满足则拦截）"""
    service = GuardService(db=db_session)

    # 创建 4 个不同授权策略的文档
    doc_global = KnowledgeUnit(title="文档-全局公开.pdf", file_type="pdf", status="INDEXED")
    doc_dept = KnowledgeUnit(title="文档-研发部专享.pdf", file_type="pdf", status="INDEXED")
    doc_role = KnowledgeUnit(title="文档-经理角色专享.pdf", file_type="pdf", status="INDEXED")
    doc_user = KnowledgeUnit(title="文档-李四个人白名单.pdf", file_type="pdf", status="INDEXED")
    doc_private = KnowledgeUnit(title="文档-未授权私有.pdf", file_type="pdf", status="INDEXED")

    db_session.add_all([doc_global, doc_dept, doc_role, doc_user, doc_private])
    await db_session.commit()

    # 策略 1: 全局公开
    await service.update_unit_policy(doc_global.id, PermissionPolicyConfig(is_public=True))
    # 策略 2: 仅部门 2 (研发部)
    await service.update_unit_policy(doc_dept.id, PermissionPolicyConfig(department_ids=[2]))
    # 策略 3: 仅角色 10 (经理角色)
    await service.update_unit_policy(doc_role.id, PermissionPolicyConfig(role_ids=[10]))
    # 策略 4: 仅个人 user_id=10087 (李四)
    await service.update_unit_policy(doc_user.id, PermissionPolicyConfig(user_ids=[10087]))
    # 策略 5: 未设置任何白名单 (默认私有)
    await service.update_unit_policy(doc_private.id, PermissionPolicyConfig(is_public=False))

    all_doc_ids = [doc_global.id, doc_dept.id, doc_role.id, doc_user.id, doc_private.id]

    # 1. 验证张三 (普通员工: user_id=10086, dept_id=2, role_ids=[30])
    # 应命中: doc_global (全局), doc_dept (部门2); 拦截: doc_role, doc_user, doc_private
    ctx_zhangsan = UserContext(
        user_id=10086,
        employee_id="10086",
        username="zhangsan",
        real_name="张三",
        dept_id=2,
        role_ids=[30],
        is_superuser=False,
    )
    zs_allowed, zs_restr = await service.evaluate_access(ctx_zhangsan, all_doc_ids)
    assert set(zs_allowed) == {doc_global.id, doc_dept.id}
    assert set(zs_restr) == {doc_role.id, doc_user.id, doc_private.id}

    # 2. 验证李四 (财务部门经理: user_id=10087, dept_id=3, role_ids=[10])
    # 应命中: doc_global (全局), doc_role (角色10), doc_user (个人10087); 拦截: doc_dept, doc_private
    ctx_lisi = UserContext(
        user_id=10087,
        employee_id="10087",
        username="lisi",
        real_name="李四",
        dept_id=3,
        role_ids=[10],
        is_superuser=False,
    )
    ls_allowed, ls_restr = await service.evaluate_access(ctx_lisi, all_doc_ids)
    assert set(ls_allowed) == {doc_global.id, doc_role.id, doc_user.id}
    assert set(ls_restr) == {doc_dept.id, doc_private.id}

    # 3. 验证王五 (超级管理员: is_superuser=True)
    # 必须全量放行全部 5 个文档
    ctx_wangwu = UserContext(
        user_id=10088,
        employee_id="10088",
        username="wangwu",
        real_name="王五",
        is_superuser=True,
    )
    ww_allowed, ww_restr = await service.evaluate_access(ctx_wangwu, all_doc_ids)
    assert set(ww_allowed) == set(all_doc_ids)
    assert len(ww_restr) == 0


@pytest.mark.asyncio
async def test_filter_allowed_chunks_batch(db_session: AsyncSession):
    """测试批量切片鉴权过滤: GuardService.filter_allowed_chunks(user_ctx, chunk_ids)"""
    service = GuardService(db=db_session)

    # 构造文档与切片
    doc1 = KnowledgeUnit(title="公开文档.md", file_type="markdown", status="INDEXED")
    doc2 = KnowledgeUnit(title="秘密文档.md", file_type="markdown", status="INDEXED")
    db_session.add_all([doc1, doc2])
    await db_session.commit()

    chunk1_1 = KnowledgeChunk(document_id=doc1.id, chunk_index=0, content="公开切片1", status="indexed")
    chunk1_2 = KnowledgeChunk(document_id=doc1.id, chunk_index=1, content="公开切片2", status="indexed")
    chunk2_1 = KnowledgeChunk(document_id=doc2.id, chunk_index=0, content="秘密切片1", status="indexed")
    db_session.add_all([chunk1_1, chunk1_2, chunk2_1])
    await db_session.commit()

    # doc1 公开，doc2 仅限用户 999
    await service.update_unit_policy(doc1.id, PermissionPolicyConfig(is_public=True))
    await service.update_unit_policy(doc2.id, PermissionPolicyConfig(is_public=False, user_ids=[999]))

    candidate_chunks = [chunk1_1.id, chunk1_2.id, chunk2_1.id, 99999]  # 99999 为不存在的切片

    # 1. 普通用户 10086 访问
    user_common = UserContext(
        user_id=10086,
        employee_id="10086",
        username="zhangsan",
        real_name="张三",
        is_superuser=False,
    )
    allowed_c, restr_c = await service.filter_allowed_chunks(user_common, candidate_chunks)
    assert set(allowed_c) == {chunk1_1.id, chunk1_2.id}
    assert set(restr_c) == {chunk2_1.id, 99999}

    # 2. 白名单用户 999 访问
    user_vip = UserContext(
        user_id=999,
        employee_id="999",
        username="vip_user",
        real_name="VIP",
        is_superuser=False,
    )
    allowed_vip, restr_vip = await service.filter_allowed_chunks(user_vip, candidate_chunks)
    assert set(allowed_vip) == {chunk1_1.id, chunk1_2.id, chunk2_1.id}
    assert set(restr_vip) == {99999}


@pytest.mark.asyncio
async def test_api_check_access_and_check_chunks(client: AsyncClient, db_session: AsyncSession):
    """测试 POST /api/v1/guard/check-access 与 POST /api/v1/guard/check-chunks HTTP 接口"""
    doc = KnowledgeUnit(title="研发规范.md", file_type="markdown", status="INDEXED")
    db_session.add(doc)
    await db_session.commit()

    chunk = KnowledgeChunk(document_id=doc.id, chunk_index=0, content="研发规范切片", status="indexed")
    db_session.add(chunk)
    await db_session.commit()

    # 仅授权研发部 (dept_id=2)
    service = GuardService(db=db_session)
    await service.update_unit_policy(doc.id, PermissionPolicyConfig(department_ids=[2]))

    # 构造研发员工 Token
    rd_token = create_access_token({
        "sub": "10086",
        "user_id": 10086,
        "employee_id": "10086",
        "username": "zhangsan",
        "dept_id": 2,
        "role_ids": [],
        "is_superuser": False,
    })

    # 1. 验证 POST /check-access
    access_res = await client.post(
        "/api/v1/guard/check-access",
        json={"candidate_unit_ids": [doc.id, 99999]},
        headers={"Authorization": f"Bearer {rd_token}"},
    )
    assert access_res.status_code == 200
    res_data = access_res.json()["data"]
    assert res_data["allowed_unit_ids"] == [doc.id]
    assert res_data["restricted_unit_ids"] == [99999]

    # 2. 验证 POST /check-chunks
    chunks_res = await client.post(
        "/api/v1/guard/check-chunks",
        json={"candidate_chunk_ids": [chunk.id, 99999]},
        headers={"Authorization": f"Bearer {rd_token}"},
    )
    assert chunks_res.status_code == 200
    c_data = chunks_res.json()["data"]
    assert c_data["allowed_chunk_ids"] == [chunk.id]
    assert c_data["restricted_chunk_ids"] == [99999]

