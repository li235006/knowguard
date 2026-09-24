"""
KnowGuard 阶段 P1-4 测试套件 (test_p1_4_batch_docx.py)
严格执行大总管瘦身铁律：单文件覆核 Word(.docx)解析与批量并发上传 3 大核心黄金断言:
  1. test_01_docx_extraction_and_indexing: 验证 .docx 文档段落与表格提取、分块与向量化入库
  2. test_02_batch_upload_concurrency: 验证 POST /api/v1/knowledge/batch-upload 多文件并发上传与批量资产生成
  3. test_03_status_lifecycle_and_guard: 验证批量上传资产状态流转 (PENDING/INDEXING -> INDEXED/AVAILABLE) 并受 Guard 引擎有效管控
"""

import io
import docx
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.milvus import milvus_service
from app.core.security import create_access_token
from app.models.knowledge import KnowledgeChunk, KnowledgeUnit
from app.schemas.auth import UserContext
from app.schemas.guard import PermissionPolicyConfig
from app.services.guard_service import GuardService
from app.services.ingestion_service import IngestionService


def create_sample_docx_bytes() -> bytes:
    """生成包含标题、段落及多行表格的保真 Word (.docx) 字节流"""
    doc = docx.Document()
    doc.add_heading("企业年度信息安全与合规管理规范2026", level=1)
    doc.add_paragraph("本规范详细说明了企业内部数据防泄露与四维权限管控核心细则。所有研发与技术人员必须严格执行。")

    # 添加表格测试结构化数据提取
    table = doc.add_table(rows=3, cols=3)
    # 表头
    table.rows[0].cells[0].text = "条款编号"
    table.rows[0].cells[1].text = "安全控制要求"
    table.rows[0].cells[2].text = "密级定义"
    # 数据行 1
    table.rows[1].cells[0].text = "SEC-01"
    table.rows[1].cells[1].text = "4D-RBAC切片级动态剥离与高情商兜底"
    table.rows[1].cells[2].text = "绝密"
    # 数据行 2
    table.rows[2].cells[0].text = "SEC-02"
    table.rows[2].cells[1].text = "多源解析支持PDF与Word原生文档表格提取"
    table.rows[2].cells[2].text = "机密"

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_01_docx_extraction_and_indexing(db_session: AsyncSession):
    """黄金断言 1: 验证 .docx 文档段落与表格提取、分块与向量化入库"""
    if hasattr(milvus_service, "_mock_collection") and milvus_service._mock_collection:
        milvus_service._mock_collection.records.clear()

    service = IngestionService(db=db_session)
    docx_bytes = create_sample_docx_bytes()

    # 1. 执行 Word .docx 解析与入库流水线
    unit = await service.ingest_file(
        filename="security_compliance_spec.docx",
        file_bytes=docx_bytes,
        category="SPEC",
    )

    # 2. 校验资产元数据与状态机
    assert unit.id is not None
    assert unit.title == "security_compliance_spec.docx"
    assert unit.file_type == "docx"
    assert unit.status == "INDEXED"
    assert unit.chunk_count >= 1

    # 3. 校验切片提取完整性 (段落文本与表格单元格数据均被成功抽取)
    chunks = await service.get_document_chunks(document_id=unit.id)
    assert len(chunks) == unit.chunk_count

    all_content = "\n".join(c.content for c in chunks)
    assert "企业年度信息安全与合规管理规范2026" in all_content, "必须提取正文标题"
    assert "4D-RBAC切片级动态剥离" in all_content, "必须提取表格单元格关键内容"
    assert "SEC-01" in all_content, "必须包含表格编码字段"

    # 4. 校验切片状态与向量一致性
    for c in chunks:
        assert c.status == "indexed", "入库成功后切片状态必须为 indexed"
        assert c.has_vector is True, "入库切片必须标记拥有向量"

    # 5. 校验 Milvus 向量集合中已写入切片记录
    milvus_chunks = service.milvus.get_chunks_by_document(unit.id)
    assert len(milvus_chunks) == len(chunks), "Milvus 中切片数必须与 MySQL 完全一致"
    print(f"\n✅ [黄金断言 1 通过] Word(.docx) 正文与表格结构化文本解析、滑动切片与向量入库全部校验通过")


@pytest.mark.asyncio
async def test_02_batch_upload_concurrency(client: AsyncClient, db_session: AsyncSession):
    """黄金断言 2: 验证 POST /api/v1/knowledge/batch-upload 多文件并发批量上传与批量资产生成"""
    if hasattr(milvus_service, "_mock_collection") and milvus_service._mock_collection:
        milvus_service._mock_collection.records.clear()

    # 准备三种不同格式的文件
    docx_bytes = create_sample_docx_bytes()
    md_bytes = ("# 研发中心 Git 分支合并规范\n主干分支保护，所有 PR 必须经过两票审核与 CI 通过。" * 10).encode("utf-8")
    txt_bytes = ("企业员工日常行为守则与信息保密须知：请勿将密码记录在公共设备上。" * 10).encode("utf-8")

    files_payload = [
        ("files", ("security_spec.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
        ("files", ("git_workflow.md", md_bytes, "text/markdown")),
        ("files", ("code_of_conduct.txt", txt_bytes, "text/plain")),
    ]

    # 发起批量上传请求
    res = await client.post(
        "/api/v1/knowledge/batch-upload",
        files=files_payload,
        data={"category": "STANDARD"},
    )
    assert res.status_code == 200, f"批量上传接口调用失败: {res.text}"
    res_json = res.json()
    assert res_json["code"] == 200
    batch_units = res_json["data"]
    assert len(batch_units) == 3, "批量上传必须成功生成 3 个知识资产"

    # 校验生成资产的格式与状态
    filenames = [u["title"] for u in batch_units]
    filetypes = [u["file_type"] for u in batch_units]
    assert "security_spec.docx" in filenames
    assert "git_workflow.md" in filenames
    assert "code_of_conduct.txt" in filenames
    assert "docx" in filetypes
    assert "markdown" in filetypes
    assert "txt" in filetypes

    for u in batch_units:
        assert u["status"] in ("INDEXED", "AVAILABLE")
        assert u["chunk_count"] > 0

    # 数据库原生验证 3 个资产均已持久化
    stmt = select(KnowledgeUnit).where(KnowledgeUnit.title.in_(filenames))
    db_units = list((await db_session.execute(stmt)).scalars().all())
    assert len(db_units) == 3
    print(f"\n✅ [黄金断言 2 通过] 多文件批量上传接口 POST /batch-upload 并发建库与响应契约校验通过")


@pytest.mark.asyncio
async def test_03_status_lifecycle_and_guard(client: AsyncClient, db_session: AsyncSession):
    """黄金断言 3: 验证批量上传资产状态流转 (INDEXED -> DISABLED -> AVAILABLE) 并受 Guard 引擎有效管控"""
    service = IngestionService(db=db_session)
    docx_bytes = create_sample_docx_bytes()
    doc = await service.ingest_file(
        filename="guard_controlled_doc.docx",
        file_bytes=docx_bytes,
        category="CONFIDENTIAL",
    )
    doc_id = doc.id
    assert doc.status == "INDEXED"

    # 构造超级管理员与研发部员工上下文
    admin_ctx = UserContext(
        user_id=10088,
        employee_id="10088",
        username="admin",
        real_name="王五",
        is_superuser=True,
    )
    rd_zhangsan_ctx = UserContext(
        user_id=10086,
        employee_id="10086",
        username="zhangsan",
        real_name="张三",
        dept_id=2,
        is_superuser=False,
    )
    finance_lisi_ctx = UserContext(
        user_id=10087,
        employee_id="10087",
        username="lisi",
        real_name="李四",
        dept_id=3,
        is_superuser=False,
    )

    guard = GuardService(db=db_session)

    # 1. 状态切换 -> DISABLED (停用资产)
    patch_res = await client.patch(
        f"/api/v1/knowledge/units/{doc_id}/status",
        json={"status": "DISABLED"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["data"]["status"] == "DISABLED"

    # 核心安全管控断言: DISABLED 状态下一票否决，即使是超管也绝不可放行！
    allowed_dis, restr_dis = await guard.evaluate_access(admin_ctx, [doc_id])
    assert doc_id in restr_dis, "DISABLED 状态资产必须被 Guard 引擎无条件拦截"
    assert doc_id not in allowed_dis

    # 2. 状态恢复 -> AVAILABLE (启用资产)
    patch_res_2 = await client.patch(
        f"/api/v1/knowledge/units/{doc_id}/status",
        json={"status": "AVAILABLE"},
    )
    assert patch_res_2.status_code == 200
    assert patch_res_2.json()["data"]["status"] == "AVAILABLE"

    # 3. 联动 4D 权限策略: 仅授权研发部 (dept_id=2)
    await guard.update_unit_policy(doc_id, PermissionPolicyConfig(is_public=False, department_ids=[2]))

    # 校验 4D 动态鉴权: 张三 (研发部) 放行，李四 (财务部) 拦截
    allowed_zs, restr_zs = await guard.evaluate_access(rd_zhangsan_ctx, [doc_id])
    assert doc_id in allowed_zs, "启用且授权研发部的资产必须放行研发部员工张三"
    assert doc_id not in restr_zs

    allowed_ls, restr_ls = await guard.evaluate_access(finance_lisi_ctx, [doc_id])
    assert doc_id in restr_ls, "未获部门授权的资产必须被 Guard 引擎拦截阻断"
    assert doc_id not in allowed_ls
    print(f"\n✅ [黄金断言 3 通过] 资产状态生命周期流转与 4D Guard 动态管控联动校验通过")
