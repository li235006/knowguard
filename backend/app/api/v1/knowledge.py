"""
知识资产维护与导入控制器 (Knowledge Router)

接口清单:
    - POST /api/v1/knowledge/upload: 单文件上传、滑动分块与向量建库入库
    - GET  /api/v1/knowledge/documents/{id}/chunks: 查看指定文档切片明细与向量状态
    - GET  /api/v1/knowledge/units/{id}/chunks: 兼容前端路径查看切片
    - GET  /api/v1/knowledge/units: 分页查询知识资产台账
    - GET  /api/v1/knowledge/documents/{id}: 获取知识单元详情
    - DELETE /api/v1/knowledge/documents/{id}: 物理删除知识文档、切片及向量

架构定位:
    API 控制器层 / 模块二: 知识维护与解析管道

作者:
    System Architect (系统架构组) & Backend Team
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from typing import List, Optional
from fastapi import APIRouter, Body, Depends, File, Form, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import BusinessLogicError, NotFoundError
from app.schemas.common import PaginatedResponse, StandardResponse
from app.schemas.knowledge import (
    KnowledgeChunkResponse,
    KnowledgeUnitResponse,
    KnowledgeUnitStatusUpdate,
)
from app.services.ingestion_service import IngestionService

router = APIRouter()


@router.post("/upload", response_model=StandardResponse[KnowledgeUnitResponse])
async def upload_document(
    file: UploadFile = File(..., description="待解析入库文件 (支持 PDF, Markdown, TXT)"),
    category: str = Form("DEFAULT", description="知识所属业务分类"),
    db: AsyncSession = Depends(get_db),
):
    """
    单文档上传、滑动切片与向量建库:
    - 支持 PDF(pypdf)、Markdown/TXT(原生Python)
    - 512 字符窗口，64 字符重叠，448 字符步长
    - BAAI/bge-m3 1024 维密集浮点向量
    - Milvus 集合写入 + MySQL pending->indexed 一致性保障
    """
    if not file.filename:
        raise BusinessLogicError(message="上传文件名称不能为空", code=40001)

    file_bytes = await file.read()
    if not file_bytes:
        raise BusinessLogicError(message="上传文件内容为空", code=40001)

    service = IngestionService(db=db)
    doc = await service.ingest_file(
        filename=file.filename,
        file_bytes=file_bytes,
        category=category,
    )

    data = KnowledgeUnitResponse.model_validate(doc)
    return StandardResponse(
        code=200,
        message="文档上传、滑动分块与向量入库成功",
        data=data,
    )


@router.get("/documents/{doc_id}/chunks", response_model=StandardResponse[List[KnowledgeChunkResponse]])
async def get_document_chunks(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    获取指定知识主文档下的全部切片列表 (按切片序号有序排列)
    包含正文、字符数、Milvus 向量化状态与元数据
    """
    service = IngestionService(db=db)
    chunks = await service.get_document_chunks(document_id=doc_id)
    chunk_list = [KnowledgeChunkResponse.model_validate(c) for c in chunks]
    return StandardResponse(
        code=200,
        message="获取切片列表成功",
        data=chunk_list,
    )


@router.get("/units/{unit_id}/chunks", response_model=StandardResponse[List[KnowledgeChunkResponse]])
async def get_unit_chunks(
    unit_id: int,
    db: AsyncSession = Depends(get_db),
):
    """前端兼容别名接口: 根据 unit_id 获取切片列表"""
    return await get_document_chunks(doc_id=unit_id, db=db)


@router.get("/units", response_model=StandardResponse[PaginatedResponse[KnowledgeUnitResponse]])
async def list_knowledge_units(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    category: Optional[str] = Query(None, description="分类过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    keyword: Optional[str] = Query(None, description="关键词检索 (模糊匹配文档标题)"),
    db: AsyncSession = Depends(get_db),
):
    """分页获取知识资产台账，支持分类、状态、关键词检索"""
    service = IngestionService(db=db)
    items, total = await service.list_documents(
        page=page,
        page_size=page_size,
        category=category,
        status=status,
        keyword=keyword,
    )
    res_items = [KnowledgeUnitResponse.model_validate(item) for item in items]
    paginated_data = PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=res_items,
    )
    return StandardResponse(
        code=200,
        message="获取知识资产列表成功",
        data=paginated_data,
    )


@router.get("/documents/{doc_id}", response_model=StandardResponse[KnowledgeUnitResponse])
@router.get("/units/{doc_id}", response_model=StandardResponse[KnowledgeUnitResponse])
async def get_knowledge_unit_detail(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取单个知识单元资产详情"""
    service = IngestionService(db=db)
    doc = await service.get_document_by_id(doc_id)
    if not doc:
        raise NotFoundError(message=f"知识文档 ID={doc_id} 不存在", code=40401)
    return StandardResponse(
        code=200,
        message="获取文档详情成功",
        data=KnowledgeUnitResponse.model_validate(doc),
    )


@router.delete("/documents/{doc_id}", response_model=StandardResponse[dict])
@router.delete("/units/{doc_id}", response_model=StandardResponse[dict])
async def delete_knowledge_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
):
    """物理彻底删除知识文档及其切片、权限策略与 Milvus 向量"""
    service = IngestionService(db=db)
    await service.delete_document(doc_id)
    return StandardResponse(
        code=200,
        message="知识文档、切片及向量已完全销毁",
        data={"deleted_id": doc_id},
    )


@router.patch("/documents/{doc_id}/status", response_model=StandardResponse[KnowledgeUnitResponse])
@router.patch("/units/{doc_id}/status", response_model=StandardResponse[KnowledgeUnitResponse])
async def update_knowledge_unit_status(
    doc_id: int,
    payload: Optional[KnowledgeUnitStatusUpdate] = Body(None, description="状态更新请求体"),
    status: Optional[str] = Query(None, description="目标状态 (Query 参数兼容)"),
    db: AsyncSession = Depends(get_db),
):
    """更新知识文档状态 (启停用切换并持久化)"""
    target_status = None
    if payload and payload.status:
        target_status = payload.status
    elif status:
        target_status = status

    if not target_status:
        raise BusinessLogicError(message="必须提供目标状态 status ('AVAILABLE' 或 'DISABLED')", code=40001)

    service = IngestionService(db=db)
    doc = await service.update_document_status(doc_id, target_status)
    return StandardResponse(
        code=200,
        message="知识状态更新成功",
        data=KnowledgeUnitResponse.model_validate(doc),
    )


@router.patch("/status", response_model=StandardResponse[KnowledgeUnitResponse])
async def update_knowledge_status_legacy(
    unit_id: int = Query(..., description="单元 ID"),
    status: str = Query("DISABLED", description="目标状态"),
    db: AsyncSession = Depends(get_db),
):
    """旧版兼容接口: 根据 unit_id 更新知识状态"""
    service = IngestionService(db=db)
    doc = await service.update_document_status(unit_id, status)
    return StandardResponse(
        code=200,
        message="知识状态更新成功",
        data=KnowledgeUnitResponse.model_validate(doc),
    )


# ==============================================================================
# 底嵌自测闭环脚本 (Self-Test Execution Block)
# ==============================================================================
if __name__ == "__main__":
    import asyncio
    from httpx import ASGITransport, AsyncClient
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import StaticPool
    from app.core.database import Base
    from main import create_app

    print("=== [Self-Test] Starting Knowledge Router Self-Test ===")

    async def _test_knowledge_router():
        test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool, echo=False)
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(bind=test_engine, expire_on_commit=False)

        async def _override_get_db():
            async with session_factory() as session:
                yield session

        test_app = create_app()
        test_app.dependency_overrides[get_db] = _override_get_db

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. 测试上传 Markdown 文件并切片向量化 (POST /api/v1/knowledge/upload)
            md_file_content = (
                "# KnowGuard 知识资产管理系统\n\n"
                "本系统提供企业级非结构化文档知识库维护与检索能力。\n"
                + "这是长文本测试内容，用于验证滑动窗口切片。" * 40
            ).encode("utf-8")

            upload_res = await client.post(
                "/api/v1/knowledge/upload",
                files={"file": ("architecture_doc.md", md_file_content, "text/markdown")},
                data={"category": "TECH"},
            )
            assert upload_res.status_code == 200, f"Upload failed: {upload_res.text}"
            upload_data = upload_res.json()["data"]
            doc_id = upload_data["id"]
            assert upload_data["title"] == "architecture_doc.md"
            assert upload_data["status"] == "INDEXED"
            assert upload_data["chunk_count"] > 0
            print(f"[Self-Test] Upload succeeded: Doc ID={doc_id}, Chunks={upload_data['chunk_count']}")

            # 2. 测试获取切片列表 (GET /api/v1/knowledge/documents/{id}/chunks)
            chunks_res = await client.get(f"/api/v1/knowledge/documents/{doc_id}/chunks")
            assert chunks_res.status_code == 200
            chunks_data = chunks_res.json()["data"]
            assert len(chunks_data) == upload_data["chunk_count"]
            assert all(c["status"] == "indexed" for c in chunks_data)
            assert all(c["has_vector"] is True for c in chunks_data)
            assert chunks_data[0]["document_id"] == doc_id
            assert chunks_data[0]["unit_id"] == doc_id
            print(f"[Self-Test] GET /documents/{doc_id}/chunks verified: {len(chunks_data)} chunks returned")

            # 3. 测试前端兼容别名接口 (GET /api/v1/knowledge/units/{id}/chunks)
            alias_res = await client.get(f"/api/v1/knowledge/units/{doc_id}/chunks")
            assert alias_res.status_code == 200
            assert len(alias_res.json()["data"]) == len(chunks_data)
            print("[Self-Test] GET /units/{id}/chunks alias verified")

            # 4. 测试资产台账分页与检索查询 (GET /api/v1/knowledge/units)
            list_res = await client.get("/api/v1/knowledge/units?page=1&page_size=10&keyword=architecture")
            assert list_res.status_code == 200
            list_data = list_res.json()["data"]
            assert list_data["total"] >= 1
            assert list_data["items"][0]["id"] == doc_id
            print(f"[Self-Test] GET /units with keyword filter verified: total={list_data['total']}")

            # 5. 测试状态启停用切换 (PATCH /api/v1/knowledge/units/{id}/status)
            patch_dis_res = await client.patch(
                f"/api/v1/knowledge/units/{doc_id}/status",
                json={"status": "DISABLED"},
            )
            assert patch_dis_res.status_code == 200
            assert patch_dis_res.json()["data"]["status"] == "DISABLED"
            print(f"[Self-Test] PATCH /units/{doc_id}/status -> DISABLED verified")

            # 验证按状态过滤
            filter_st_res = await client.get("/api/v1/knowledge/units?status=DISABLED")
            assert filter_st_res.status_code == 200
            assert filter_st_res.json()["data"]["total"] >= 1

            # 切回 AVAILABLE
            patch_avail_res = await client.patch(
                f"/api/v1/knowledge/units/{doc_id}/status",
                json={"status": "AVAILABLE"},
            )
            assert patch_avail_res.status_code == 200
            assert patch_avail_res.json()["data"]["status"] == "AVAILABLE"
            print(f"[Self-Test] PATCH /units/{doc_id}/status -> AVAILABLE verified")

            # 6. 测试非法格式文件上传拦截 (POST /api/v1/knowledge/upload)
            invalid_res = await client.post(
                "/api/v1/knowledge/upload",
                files={"file": ("virus_script.exe", b"binary content", "application/octet-stream")},
            )
            assert invalid_res.status_code == 400
            assert invalid_res.json()["code"] == 40001
            print("[Self-Test] Invalid file format blocked with code 40001")

            # 7. 测试删除与级联清理 (DELETE /api/v1/knowledge/units/{id})
            del_res = await client.delete(f"/api/v1/knowledge/units/{doc_id}")
            assert del_res.status_code == 200
            assert del_res.json()["data"]["deleted_id"] == doc_id

            get_del_res = await client.get(f"/api/v1/knowledge/units/{doc_id}")
            assert get_del_res.status_code == 404
            print(f"[Self-Test] DELETE /units/{doc_id} verified, subsequent GET returns 404")

        test_app.dependency_overrides.clear()
        await test_engine.dispose()
        print("=== [Self-Test] All Knowledge Router tests PASSED successfully! ===")

    asyncio.run(_test_knowledge_router())
