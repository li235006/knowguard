"""
KnowGuard 阶段 P1-2 极简测试脚本 (test_p1_2_policy.py)
严格执行大总管瘦身铁律：单文件覆核 4D 权限策略与动态 RAG 联动 3 大核心黄金断言:
  1. 策略回显 (GET /api/v1/guard/units/{id}/policy 契约回显 4D 结构)
  2. 原子更新 (PUT /api/v1/guard/units/{id}/policy 更新并原子持久化 4D 策略)
  3. 动态 RAG 生效 (策略动态切换为仅研发部；张三放行并回显 citations，李四静默拦截触发 SilentFallback 且零泄露)
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.milvus import milvus_service
from app.core.security import create_access_token
from app.models.policy import PermissionPolicy
from app.schemas.guard import PermissionPolicyConfig
from app.services.guard_service import GuardService
from app.services.ingestion_service import IngestionService


@pytest_asyncio.fixture
async def sample_unit_with_doc(db_session: AsyncSession):
    """预置一个已建库切片且向量化的知识资产 (初始配置全局公开)"""
    # 清理历史向量切片防止干扰
    if hasattr(milvus_service, "_mock_collection") and milvus_service._mock_collection:
        milvus_service._mock_collection.records.clear()

    service = IngestionService(db=db_session)
    content = ("# 核心研发规范与系统架构\n本文档详细规定了研发部的核心规范与架构设计标准。" + "详细规则条款。" * 20).encode("utf-8")
    doc = await service.ingest_file(
        filename="rd_core_architecture.md",
        file_bytes=content,
        category="DEV",
    )
    # 初始化为全局公开策略
    guard_svc = GuardService(db=db_session)
    await guard_svc.update_unit_policy(
        doc.id,
        PermissionPolicyConfig(
            is_global=True,
            is_public=True,
            department_ids=[],
            role_ids=[],
            user_ids=[],
        ),
    )
    return doc


@pytest.mark.asyncio
async def test_01_policy_echo(client: AsyncClient, sample_unit_with_doc):
    """黄金断言 1: 策略回显 (GET /api/v1/guard/units/{id}/policy 返回 4D 结构 is_global/is_public, department_ids, role_ids, user_ids)"""
    doc_id = sample_unit_with_doc.id

    # 1. 验证 Leader 标准路由 GET /api/v1/guard/units/{id}/policy
    res = await client.get(f"/api/v1/guard/units/{doc_id}/policy")
    assert res.status_code == 200, f"策略回显接口失败: {res.text}"
    res_json = res.json()
    assert res_json["code"] == 200
    data = res_json["data"]
    assert data["unit_id"] == doc_id
    assert "is_global" in data or "is_public" in data
    assert isinstance(data.get("department_ids"), list)
    assert isinstance(data.get("role_ids"), list)
    assert isinstance(data.get("user_ids"), list)

    # 2. 验证前端兼容路由 GET /api/v1/guard/policies/{id}
    alias_res = await client.get(f"/api/v1/guard/policies/{doc_id}")
    assert alias_res.status_code == 200
    alias_data = alias_res.json()["data"]
    assert alias_data["unit_id"] == doc_id
    assert alias_data["is_global"] is True
    print(f"\n✅ [黄金断言 1 通过] 策略回显契约校验通过: unit_id={doc_id}, is_global={alias_data['is_global']}")


@pytest.mark.asyncio
async def test_02_policy_atomic_update_and_persistence(client: AsyncClient, sample_unit_with_doc, db_session: AsyncSession):
    """黄金断言 2: 原子更新与持久化 (PUT /api/v1/guard/units/{id}/policy 更新并持久化 4D 策略，严格核验响应与实体一致性)"""
    doc_id = sample_unit_with_doc.id

    update_payload = {
        "is_global": False,
        "is_public": False,
        "department_ids": [2],
        "role_ids": [10, 20],
        "user_ids": [10086],
    }

    # 1. 执行原子更新 PUT /api/v1/guard/units/{id}/policy
    put_res = await client.put(f"/api/v1/guard/units/{doc_id}/policy", json=update_payload)
    assert put_res.status_code == 200, f"策略更新失败: {put_res.text}"
    put_data = put_res.json()["data"]
    assert put_data["unit_id"] == doc_id
    assert put_data["is_global"] is False
    assert put_data["department_ids"] == [2]
    assert put_data["role_ids"] == [10, 20]
    assert put_data["user_ids"] == [10086]

    # 2. 再次调用 GET 核验持久化回显
    get_res = await client.get(f"/api/v1/guard/units/{doc_id}/policy")
    assert get_res.status_code == 200
    get_data = get_res.json()["data"]
    assert get_data["is_global"] is False
    assert get_data["department_ids"] == [2]
    assert get_data["role_ids"] == [10, 20]
    assert get_data["user_ids"] == [10086]

    # 3. 数据库物理表层面直接核验
    stmt = select(PermissionPolicy).where(PermissionPolicy.unit_id == doc_id)
    policy_db = (await db_session.execute(stmt)).scalar_one_or_none()
    assert policy_db is not None
    assert policy_db.is_public is False
    assert policy_db.department_ids == [2]
    assert policy_db.role_ids == [10, 20]
    assert policy_db.user_ids == [10086]
    print(f"\n✅ [黄金断言 2 通过] 策略原子更新与底层持久化校验通过: unit_id={doc_id}, depts={policy_db.department_ids}")


@pytest.mark.asyncio
async def test_03_dynamic_rag_enforcement(client: AsyncClient, sample_unit_with_doc):
    """黄金断言 3: 动态 RAG 生效 (策略动态切换为仅研发部 dept_id=2；张三放行并回显 citations，李四触发 SilentFallback 且零泄露)"""
    doc_id = sample_unit_with_doc.id

    # 1. 动态切换策略: 仅限研发部 (dept_id=2)
    dept_policy = {
        "is_global": False,
        "is_public": False,
        "department_ids": [2],
        "role_ids": [],
        "user_ids": [],
    }
    put_res = await client.put(f"/api/v1/guard/units/{doc_id}/policy", json=dept_policy)
    assert put_res.status_code == 200

    # 2. 构造用户凭证
    # 张三: 研发部员工 (dept_id=2)
    token_zhangsan = create_access_token({
        "sub": "10086",
        "user_id": 1,
        "employee_id": "10086",
        "username": "zhangsan",
        "real_name": "张三",
        "dept_id": 2,
        "dept_name": "研发部",
        "role_ids": [3],
        "is_superuser": False,
    })
    # 李四: 财务部经理 (dept_id=3)
    token_lisi = create_access_token({
        "sub": "10087",
        "user_id": 2,
        "employee_id": "10087",
        "username": "lisi",
        "real_name": "李四",
        "dept_id": 3,
        "dept_name": "财务部",
        "role_ids": [2],
        "is_superuser": False,
    })

    query_payload = {
        "query": "请问研发部的核心规范和系统架构是什么？",
        "conversation_id": "conv-p1-2-dyn-rag",
    }

    # 3. 张三 (研发部 dept_id=2) 发起 RAG 问答 -> 必须放行并产出 citation 卡片
    res_zs = await client.post(
        "/api/v1/chat/completions",
        json=query_payload,
        headers={"Authorization": f"Bearer {token_zhangsan}", "Accept": "text/event-stream"},
    )
    assert res_zs.status_code == 200
    assert "text/event-stream" in res_zs.headers.get("Content-Type", "")
    zs_text = res_zs.text
    assert "event: citation" in zs_text, "研发部张三必须获得知识溯源 citation 卡片"
    assert "rd_core_architecture.md" in zs_text
    assert "event: text_delta" in zs_text
    assert "event: done" in zs_text

    # 4. 李四 (财务部 dept_id=3) 发起 RAG 问答 -> 必须被 4D Guard 拦截并触发 SilentFallback
    res_ls = await client.post(
        "/api/v1/chat/completions",
        json=query_payload,
        headers={"Authorization": f"Bearer {token_lisi}", "Accept": "text/event-stream"},
    )
    assert res_ls.status_code == 200
    assert "text/event-stream" in res_ls.headers.get("Content-Type", "")
    ls_text = res_ls.text
    assert "event: citation" not in ls_text, "财务部李四越权访问绝不输出 citation 溯源"
    assert "event: warning" in ls_text, "财务部李四越权必须触发 warning 隔离事件帧"
    assert "rd_core_architecture.md" not in ls_text, "严禁向越权人员泄露文档标题"
    assert "is_silent_fallback" in ls_text, "必须触发 SilentFallback 高情商兜底"
    print("\n✅ [黄金断言 3 通过] 动态 RAG 权限生效断言通过: 张三放行回显，李四拦截静默零泄露")
