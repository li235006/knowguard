"""
模块 M2 知识解析、分块、向量化与建库自动化测试套件 (test_m2_ingestion.py)

测试范围:
    1. 解析：PDF (pypdf)、Markdown/TXT (原生 Python) 纯文本提取验证
    2. 分块：原生 Python 滑动切片，固定窗口 512 字符，重叠 64 字符，步长 448 字符算法边界校验
    3. 向量：BAAI/bge-m3 1024 维 float 向量计算与归一化校验
    4. 存储：Milvus knowguard_chunks 集合 (chunk_id, document_id, embedding) 写入与检索
    5. 一致性状态流转：MySQL 存切片正文 (status='pending') ➔ Milvus 写入成功 ➔ 更新 MySQL status='indexed'
    6. 接口：POST /api/v1/knowledge/upload 与 GET /api/v1/knowledge/documents/{id}/chunks 闭环
    7. 异常控制：非法格式拦截 (40001)、空文件拦截 (40001)、不存在文档 404 (40401)

作者:
    Backend Team & QA
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import io
import math
import pytest
from httpx import AsyncClient
from pypdf import PdfWriter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.milvus import milvus_service
from app.models.knowledge import KnowledgeChunk, KnowledgeUnit
from app.providers.embedding import default_embedding_provider
from app.services.ingestion_service import IngestionService


# ==============================================================================
# 1. 纯文本提取测试 (PDF & Markdown/TXT)
# ==============================================================================
def test_pdf_text_extraction_pypdf():
    """测试基于 pypdf 的 PDF 文本提取能力"""
    writer = PdfWriter()
    # 添加含有文本注释或页面对象的 PDF
    writer.add_blank_page(width=400, height=400)
    buf = io.BytesIO()
    writer.write(buf)
    pdf_bytes = buf.getvalue()

    # 验证提取流程不抛出异常
    text = IngestionService.extract_text_from_pdf(pdf_bytes)
    assert isinstance(text, str)


def test_markdown_and_txt_extraction_native():
    """测试基于原生 Python 的 Markdown 与 TXT 纯文本提取"""
    md_str = "# 企业核心知识文档\n\n- 条款 1: 严格执行安全合规\n- 条款 2: 数据脱敏保护"
    txt_str = "这是一份普通的纯文本配置文档内容，包含关键说明。"

    md_extracted = IngestionService.extract_text_from_txt_or_markdown(md_str.encode("utf-8"))
    txt_extracted = IngestionService.extract_text_from_txt_or_markdown(txt_str.encode("gbk"))

    assert md_extracted == md_str
    assert txt_extracted == txt_str


# ==============================================================================
# 2. 原生 Python 滑动切片算法测试 (512 窗口 / 64 重叠 / 448 步长)
# ==============================================================================
def test_sliding_window_chunking_algorithm():
    """严格校验滑动切片：固定窗口 512 字符，重叠 64 字符，步长 448 字符"""
    # 构造 1350 字符的长文本
    sample_text = "KnowGuard" * 150  # 9 * 150 = 1350
    chunks = IngestionService.sliding_window_chunk(sample_text, window_size=512, overlap=64)

    # 1350 字符按 512 窗口和 448 步长切片：
    # 切片 0: [0, 512]
    # 切片 1: [448, 960]
    # 切片 2: [896, 1350]
    assert len(chunks) == 3, f"1350 字符应该生成 3 个分块，实际生成 {len(chunks)}"

    assert chunks[0]["start_idx"] == 0
    assert chunks[0]["end_idx"] == 512
    assert chunks[0]["char_length"] == 512

    assert chunks[1]["start_idx"] == 448
    assert chunks[1]["end_idx"] == 960
    assert chunks[1]["char_length"] == 512

    assert chunks[2]["start_idx"] == 896
    assert chunks[2]["end_idx"] == 1350
    assert chunks[2]["char_length"] == 1350 - 896

    # 校验切片 0 与切片 1 的重叠长度 = 512 - 448 = 64 字符
    overlap_0_1 = chunks[0]["end_idx"] - chunks[1]["start_idx"]
    assert overlap_0_1 == 64, f"第 0、1 切片重叠长度必须为 64，实际为 {overlap_0_1}"

    # 校验切片 1 与切片 2 的重叠长度 = 960 - 896 = 64 字符
    overlap_1_2 = chunks[1]["end_idx"] - chunks[2]["start_idx"]
    assert overlap_1_2 == 64, f"第 1、2 切片重叠长度必须为 64，实际为 {overlap_1_2}"


def test_sliding_window_chunking_short_text():
    """测试短文本 (<512字符) 切片仅返回 1 个分块"""
    short_text = "这是一段未超过 512 字符的知识文本，应当直接作为单个切片返回。"
    chunks = IngestionService.sliding_window_chunk(short_text, window_size=512, overlap=64)
    assert len(chunks) == 1
    assert chunks[0]["chunk_index"] == 0
    assert chunks[0]["content"] == short_text
    assert chunks[0]["char_length"] == len(short_text)


def test_sliding_window_chunking_abnormal_window_size_no_infinite_loop():
    """测试当 window_size <= overlap 时 step 强制保底为 1 且熔断机制生效，坚决杜绝死循环"""
    text = "KnowGuardSecurityTest" * 20  # 420 chars
    # 当 window_size=50, overlap=60 时，原本 step = -10，必然导致无限死循环！
    # 现经 step = max(1, window_size - overlap) 保底，step 成为 1，并受 max_iterations 熔断保护
    chunks = IngestionService.sliding_window_chunk(text, window_size=50, overlap=60)
    assert len(chunks) > 0, "即使入参异常也必须安全退出，严禁死循环"



# ==============================================================================
# 3. BAAI/bge-m3 1024 维 float 向量计算测试
# ==============================================================================
@pytest.mark.asyncio
async def test_bge_m3_embedding_dimension_and_normalization():
    """测试生成 1024 维 float 向量并验证 L2 归一化模长"""
    provider = default_embedding_provider
    text = "KnowGuard 架构安全防护规范切片向量测试。"

    vec = await provider.get_embedding(text)
    assert len(vec) == 1024, f"向量维度必须严格为 1024，实际为 {len(vec)}"
    assert all(isinstance(x, float) for x in vec), "向量内部元素必须全为 float"

    # 校验模长归一化
    norm = math.sqrt(sum(x * x for x in vec))
    assert abs(norm - 1.0) < 1e-4, f"向量 L2 模长必须归一化为 1.0，实际为 {norm}"

    # 校验批量接口
    batch = await provider.get_embeddings([text, "第二段测试切片"])
    assert len(batch) == 2
    assert len(batch[0]) == 1024
    assert len(batch[1]) == 1024


# ==============================================================================
# 4. 一致性状态机测试 (MySQL pending ➔ Milvus 写入 ➔ MySQL indexed)
# ==============================================================================
@pytest.mark.asyncio
async def test_ingestion_consistency_lifecycle(db_session: AsyncSession):
    """测试 MySQL 存切片正文 (status='pending') ➔ Milvus 写入成功 ➔ 更新 MySQL status='indexed'"""
    service = IngestionService(db=db_session)

    md_content = (
        "# 知识数据保护守则\n\n"
        "第一章：数据所有权划分与流转控制。\n"
        "第二章：知识切片嵌入与向量检索安全。\n"
        + "这是用于验证两阶段一致性流转的测试段落。" * 30
    ).encode("utf-8")

    doc = await service.ingest_file(
        filename="data_security_rules.md",
        file_bytes=md_content,
        category="SECURITY"
    )

    assert doc.id is not None
    assert doc.status == "INDEXED"
    assert doc.chunk_count > 0

    # 查询数据库中的切片记录
    stmt = select(KnowledgeChunk).where(KnowledgeChunk.document_id == doc.id).order_by(KnowledgeChunk.chunk_index)
    res = await db_session.execute(stmt)
    chunks = list(res.scalars().all())

    assert len(chunks) == doc.chunk_count
    # 验证最终全部更新为 indexed 状态
    assert all(c.status == "indexed" for c in chunks), "入库成功后全部切片 status 必须为 indexed"
    assert all(c.has_vector is True for c in chunks), "入库成功后全部切片 has_vector 必须为 True"

    # 验证 Milvus 中存入对应数量的向量实体
    milvus_records = milvus_service.get_chunks_by_document(doc.id)
    assert len(milvus_records) == doc.chunk_count
    assert len(milvus_records[0]["embedding"]) == 1024


# ==============================================================================
# 5. API 接口测试 (POST /upload 与 GET /documents/{id}/chunks)
# ==============================================================================
@pytest.mark.asyncio
async def test_api_upload_and_get_chunks_lifecycle(client: AsyncClient):
    """测试 POST /api/v1/knowledge/upload 与 GET /api/v1/knowledge/documents/{id}/chunks 完整生命周期"""
    file_content = (
        "# KnowGuard 研发体系知识手册\n\n"
        "本手册指导团队开发高内聚低耦合的代码模块。\n"
        + "切片长文本补充内容，保证产生多个切片。" * 40
    ).encode("utf-8")

    # 1. 上传文件
    upload_res = await client.post(
        "/api/v1/knowledge/upload",
        files={"file": ("rd_handbook.md", file_content, "text/markdown")},
        data={"category": "RD"},
    )
    assert upload_res.status_code == 200
    upload_json = upload_res.json()
    assert upload_json["code"] == 200
    assert "成功" in upload_json["message"]
    data = upload_json["data"]
    doc_id = data["id"]
    assert data["title"] == "rd_handbook.md"
    assert data["status"] == "INDEXED"
    assert data["chunk_count"] > 0

    # 2. 查询切片列表 (GET /api/v1/knowledge/documents/{id}/chunks)
    chunks_res = await client.get(f"/api/v1/knowledge/documents/{doc_id}/chunks")
    assert chunks_res.status_code == 200
    chunks_json = chunks_res.json()
    assert chunks_json["code"] == 200
    chunks_list = chunks_json["data"]
    assert len(chunks_list) == data["chunk_count"]
    assert chunks_list[0]["document_id"] == doc_id
    assert chunks_list[0]["unit_id"] == doc_id
    assert chunks_list[0]["status"] == "indexed"
    assert chunks_list[0]["has_vector"] is True
    assert "start_idx" in chunks_list[0]["metadata"]

    # 3. 前端兼容别名接口 (GET /api/v1/knowledge/units/{id}/chunks)
    alias_res = await client.get(f"/api/v1/knowledge/units/{doc_id}/chunks")
    assert alias_res.status_code == 200
    assert len(alias_res.json()["data"]) == len(chunks_list)

    # 4. 知识单元台账分页 (GET /api/v1/knowledge/units)
    units_res = await client.get("/api/v1/knowledge/units?page=1&page_size=10")
    assert units_res.status_code == 200
    units_data = units_res.json()["data"]
    assert units_data["total"] >= 1


@pytest.mark.asyncio
async def test_api_upload_unsupported_file_format_rejected(client: AsyncClient):
    """测试上传不支持格式的文件时被拦截并返回业务错误码 40001"""
    response = await client.post(
        "/api/v1/knowledge/upload",
        files={"file": ("malicious_executable.bin", b"mock binary", "application/octet-stream")},
    )
    assert response.status_code == 400
    res_json = response.json()
    assert res_json["code"] == 40001
    assert "不支持的文件格式" in res_json["message"]


@pytest.mark.asyncio
async def test_api_upload_empty_file_rejected(client: AsyncClient):
    """测试上传空文件时被拦截并返回业务错误码 40001"""
    response = await client.post(
        "/api/v1/knowledge/upload",
        files={"file": ("empty_notes.txt", b"", "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["code"] == 40001


@pytest.mark.asyncio
async def test_api_get_chunks_non_existent_document(client: AsyncClient):
    """测试查询不存在的文档切片返回 404 (40401)"""
    response = await client.get("/api/v1/knowledge/documents/999999/chunks")
    assert response.status_code == 404
    assert response.json()["code"] == 40401
