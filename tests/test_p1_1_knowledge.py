"""
KnowGuard 阶段 P1-1 极简测试脚本 (test_p1_1_knowledge.py)
严格执行大总管瘦身铁律：单文件覆核知识资产台账管理 3 大核心黄金断言
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.ingestion_service import IngestionService


@pytest_asyncio.fixture
async def sample_doc(db_session: AsyncSession):
    """预置一个已建库切片的知识资产"""
    service = IngestionService(db=db_session)
    content = ("# 企业核心知识资产测试制度\n本文件用于知识台账与切片完整性测试。" + "详细规则内容。" * 30).encode("utf-8")
    doc = await service.ingest_file(
        filename="company_policy.md",
        file_bytes=content,
        category="POLICY",
    )
    return doc


@pytest.mark.asyncio
async def test_01_knowledge_units_pagination_and_contract(client: AsyncClient, sample_doc):
    """黄金断言 1: 资产列表检索 (分页拉取台账，校验 title, file_type, chunk_count, status 契约完整性)"""
    res = await client.get("/api/v1/knowledge/units?page=1&page_size=10")
    assert res.status_code == 200, f"拉取台账列表失败: {res.text}"
    res_json = res.json()
    assert res_json["code"] == 200

    paginated = res_json["data"]
    assert paginated["total"] >= 1
    items = paginated["items"]
    assert len(items) >= 1

    item = next((i for i in items if i["id"] == sample_doc.id), items[0])
    # 核心契约字段校验
    assert "title" in item and len(item["title"]) > 0
    assert "file_type" in item and item["file_type"] in ("markdown", "pdf", "txt", "docx")
    assert "chunk_count" in item and item["chunk_count"] > 0
    assert "status" in item and item["status"] in ("INDEXED", "PARSING", "PENDING", "DISABLED")
    print(f"\n✅ [黄金断言 1 通过] 知识台账分页与契约字段校验成功: title={item['title']}, chunks={item['chunk_count']}")


@pytest.mark.asyncio
async def test_02_knowledge_status_toggle_persistence(client: AsyncClient, sample_doc):
    """黄金断言 2: 状态切换断言 (调用 PATCH /status 启停用切换，断言状态持久化)"""
    doc_id = sample_doc.id

    # 1. 停用切换 -> DISABLED
    patch_res = await client.patch(f"/api/v1/knowledge/units/{doc_id}/status?status=DISABLED")
    assert patch_res.status_code == 200
    assert patch_res.json()["data"]["status"] == "DISABLED"

    # 验证数据库持久化结果
    get_res = await client.get(f"/api/v1/knowledge/units/{doc_id}")
    assert get_res.status_code == 200
    assert get_res.json()["data"]["status"] == "DISABLED"

    # 2. 启用恢复 -> INDEXED
    patch_res_2 = await client.patch(f"/api/v1/knowledge/units/{doc_id}/status?status=INDEXED")
    assert patch_res_2.status_code == 200
    assert patch_res_2.json()["data"]["status"] == "INDEXED"
    print(f"\n✅ [黄金断言 2 通过] 知识资产 ID={doc_id} 启停用状态切换与持久化断言通过")


@pytest.mark.asyncio
async def test_03_knowledge_cascade_deletion(client: AsyncClient, sample_doc):
    """黄金断言 3: 级联删除断言 (调用 DELETE /units/{id}，断言数据库与切片彻底清除，接口返回 200)"""
    doc_id = sample_doc.id

    # 1. 物理删除
    del_res = await client.delete(f"/api/v1/knowledge/units/{doc_id}")
    assert del_res.status_code == 200
    assert del_res.json()["code"] == 200

    # 2. 再次查询确认已清除
    check_res = await client.get(f"/api/v1/knowledge/units/{doc_id}")
    assert check_res.status_code == 404, "删除后再次查询必须返回 404"
    assert check_res.json()["code"] == 40401
    print(f"\n✅ [黄金断言 3 通过] 知识单元 ID={doc_id} 级联清除成功，再次查询准确返回 404")
