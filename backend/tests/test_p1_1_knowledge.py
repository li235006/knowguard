"""
KnowGuard 阶段 P1-1 测试套件 (test_p1_1_knowledge.py)
覆盖知识资产台账管理核心要求:
  1. 资产台账分页检索与分类/状态/关键词过滤 (GET /api/v1/knowledge/units)
  2. 知识状态启停用切换 (PATCH /api/v1/knowledge/units/{id}/status) 与 Guard 引擎联动阻断
  3. 知识单元全级联物理删除 (DELETE /api/v1/knowledge/units/{id} 清理 Unit, Chunk, Policy, Milvus)
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeChunk, KnowledgeUnit
from app.models.policy import PermissionPolicy
from app.schemas.auth import UserContext
from app.services.guard_service import GuardService
from app.services.ingestion_service import IngestionService


@pytest_asyncio.fixture
async def sample_doc(db_session: AsyncSession):
    """预置一个已建库切片的知识资产，并关联权限策略"""
    service = IngestionService(db=db_session)
    content = ("# 企业核心知识资产测试制度\n本文件用于知识台账与切片完整性测试。" + "详细规则内容。" * 30).encode("utf-8")
    doc = await service.ingest_file(
        filename="company_policy.md",
        file_bytes=content,
        category="POLICY",
    )
    # 附加权限策略用于验证级联删除
    policy = PermissionPolicy(
        unit_id=doc.id,
        is_public=True,
        department_ids=[],
        role_ids=[],
        user_ids=[],
    )
    db_session.add(policy)
    await db_session.commit()
    await db_session.refresh(doc)
    return doc


@pytest.mark.asyncio
async def test_01_knowledge_units_pagination_and_contract(client: AsyncClient, sample_doc):
    """断言 1: 资产列表检索 (分页拉取台账，支持 category / status / keyword 过滤，校验契约完整性)"""
    # 1. 基础分页
    res = await client.get("/api/v1/knowledge/units?page=1&page_size=10")
    assert res.status_code == 200, f"拉取台账列表失败: {res.text}"
    res_json = res.json()
    assert res_json["code"] == 200

    paginated = res_json["data"]
    assert paginated["total"] >= 1
    items = paginated["items"]
    assert len(items) >= 1

    item = next((i for i in items if i["id"] == sample_doc.id), items[0])
    assert item["title"] == "company_policy.md"
    assert item["file_type"] in ("markdown", "pdf", "txt")
    assert item["chunk_count"] > 0
    assert item["status"] in ("INDEXED", "AVAILABLE", "DISABLED")

    # 2. 分类与关键词检索过滤
    kw_res = await client.get("/api/v1/knowledge/units?keyword=company_policy&category=POLICY")
    assert kw_res.status_code == 200
    kw_data = kw_res.json()["data"]
    assert kw_data["total"] >= 1
    assert any(i["id"] == sample_doc.id for i in kw_data["items"])

    # 3. 未命中关键词检索
    none_res = await client.get("/api/v1/knowledge/units?keyword=non_existent_key_xyz_123")
    assert none_res.status_code == 200
    assert none_res.json()["data"]["total"] == 0


@pytest.mark.asyncio
async def test_02_knowledge_status_toggle_and_guard_veto(client: AsyncClient, db_session: AsyncSession, sample_doc):
    """断言 2: 状态切换与 Guard 引擎核心联动 (PATCH 切换 DISABLED / AVAILABLE，断言 Guard 引擎对 DISABLED 状态一票否决)"""
    doc_id = sample_doc.id
    guard_svc = GuardService(db=db_session)

    # 构造超级管理员用户身份
    admin_user = UserContext(
        user_id=1,
        employee_id="ADMIN001",
        username="admin",
        real_name="超级管理员",
        role_codes=["ROLE_SUPER_ADMIN"],
        is_superuser=True,
    )

    # 初始状态 INDEXED: 超管正常放行
    allowed_init, restr_init = await guard_svc.evaluate_access(admin_user, [doc_id])
    assert doc_id in allowed_init
    assert doc_id not in restr_init

    # 1. 停用切换 -> DISABLED (通过 JSON 请求体)
    patch_res = await client.patch(
        f"/api/v1/knowledge/units/{doc_id}/status",
        json={"status": "DISABLED"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["data"]["status"] == "DISABLED"

    # 验证数据库持久化结果
    get_res = await client.get(f"/api/v1/knowledge/units/{doc_id}")
    assert get_res.status_code == 200
    assert get_res.json()["data"]["status"] == "DISABLED"

    # 核心联动断言: 停用后 GuardService.evaluate_access 必须一票否决 (即使是超管也立即阻断)
    allowed_dis, restr_dis = await guard_svc.evaluate_access(admin_user, [doc_id])
    assert doc_id in restr_dis, "DISABLED 状态文档必须被 Guard 引擎无条件拦截"
    assert doc_id not in allowed_dis

    # 2. 启用恢复 -> AVAILABLE (通过 JSON 请求体)
    patch_res_2 = await client.patch(
        f"/api/v1/knowledge/units/{doc_id}/status",
        json={"status": "AVAILABLE"},
    )
    assert patch_res_2.status_code == 200
    assert patch_res_2.json()["data"]["status"] == "AVAILABLE"

    # 核心联动断言: 恢复启用后，超管及公开策略可正常访问
    allowed_en, restr_en = await guard_svc.evaluate_access(admin_user, [doc_id])
    assert doc_id in allowed_en
    assert doc_id not in restr_en


@pytest.mark.asyncio
async def test_03_knowledge_full_cascade_deletion(client: AsyncClient, db_session: AsyncSession, sample_doc):
    """断言 3: 级联删除断言 (调用 DELETE /units/{id}，断言 Unit, Chunks, Policy, Milvus 均彻底清空)"""
    doc_id = sample_doc.id
    service = IngestionService(db=db_session)

    # 确认删除前切片与策略均存在
    chunks_before = await db_session.execute(
        select(KnowledgeChunk).where(KnowledgeChunk.document_id == doc_id)
    )
    assert len(list(chunks_before.scalars().all())) > 0

    policy_before = await db_session.execute(
        select(PermissionPolicy).where(PermissionPolicy.unit_id == doc_id)
    )
    assert len(list(policy_before.scalars().all())) == 1

    # 1. 物理删除
    del_res = await client.delete(f"/api/v1/knowledge/units/{doc_id}")
    assert del_res.status_code == 200
    assert del_res.json()["code"] == 200
    assert del_res.json()["data"]["deleted_id"] == doc_id

    # 2. 接口查询确认返回 404
    check_res = await client.get(f"/api/v1/knowledge/units/{doc_id}")
    assert check_res.status_code == 404
    assert check_res.json()["code"] == 40401

    # 3. 数据库显式验证 KnowledgeUnit 已被清除
    unit_check = await db_session.execute(
        select(KnowledgeUnit).where(KnowledgeUnit.id == doc_id)
    )
    assert unit_check.scalar_one_or_none() is None

    # 4. 数据库显式验证 KnowledgeChunk 已被清除
    chunks_check = await db_session.execute(
        select(KnowledgeChunk).where(KnowledgeChunk.document_id == doc_id)
    )
    assert len(list(chunks_check.scalars().all())) == 0

    # 5. 数据库显式验证 PermissionPolicy 已被清除
    policy_check = await db_session.execute(
        select(PermissionPolicy).where(PermissionPolicy.unit_id == doc_id)
    )
    assert len(list(policy_check.scalars().all())) == 0

    # 6. Milvus 集合验证切片向量已清空
    milvus_chunks = service.milvus.get_chunks_by_document(doc_id)
    assert len(milvus_chunks) == 0
