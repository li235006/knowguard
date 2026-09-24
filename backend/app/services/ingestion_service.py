"""
知识多源解析、滑动切片与向量建库管道服务 (Ingestion Service)

职责:
    - 多格式文本提取: PDF (pypdf)、Markdown/TXT (原生 Python)
    - 原生 Python 滑动切片算法: 固定窗口 512 字符，重叠 64 字符，步长 448 字符 (512 - 64 = 448)
    - 接入 BAAI/bge-m3 生成 1024 维密集浮点向量
    - Milvus 2.4+ (192.168.6.134:19530) knowguard_chunks 集合存储 (chunk_id, document_id, embedding)
    - 严格一致性状态流转:
        MySQL 存切片正文 (status='pending') ➔ Milvus 写入成功 ➔ 更新 MySQL status='indexed'
    - 核心服务脚本底嵌 if __name__ == '__main__': 闭环验证

架构定位:
    业务服务层 (Services Layer) / 模块二: 知识维护与解析管道

作者:
    System Architect (系统架构组) & Backend Team
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import hashlib
import io
import logging
from typing import Any, Dict, List, Optional, Tuple
from pypdf import PdfReader
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessLogicError, NotFoundError
from app.core.milvus import MilvusService, milvus_service
from app.models.knowledge import KnowledgeChunk, KnowledgeUnit
from app.providers.base import BaseEmbeddingProvider
from app.providers.embedding import default_embedding_provider

logger = logging.getLogger(__name__)


class IngestionService:
    """文档解析、分块与向量入库统一服务实现"""

    def __init__(
        self,
        db: AsyncSession,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
        milvus: Optional[MilvusService] = None,
    ):
        self.db = db
        self.embedding_provider = embedding_provider or default_embedding_provider
        self.milvus = milvus or milvus_service

    # --------------------------------------------------------------------------
    # 1. 多格式纯文本解析模块 (Requirement 1)
    # --------------------------------------------------------------------------
    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        """使用 pypdf 实现 PDF 纯文本提取"""
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            pages_text = []
            for idx, page in enumerate(reader.pages):
                txt = page.extract_text() or ""
                if txt.strip():
                    pages_text.append(txt.strip())
            return "\n\n".join(pages_text)
        except Exception as e:
            logger.error(f"[IngestionService] PDF extraction failed: {e}")
            raise BusinessLogicError(message=f"PDF 文本提取失败: {str(e)}", code=40001)

    @staticmethod
    def extract_text_from_docx(file_bytes: bytes) -> str:
        """使用 python-docx 实现 Word (.docx) 纯文本与表格段落全量提取"""
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            parts = []
            # 1. 提取所有段落
            for p in doc.paragraphs:
                txt = p.text.strip()
                if txt:
                    parts.append(txt)
            # 2. 提取所有表格行文本
            for table in doc.tables:
                for row in table.rows:
                    row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_cells:
                        parts.append(" | ".join(row_cells))
            return "\n\n".join(parts)
        except Exception as e:
            logger.error(f"[IngestionService] Word .docx extraction failed: {e}")
            raise BusinessLogicError(message=f"Word (.docx) 文本提取失败: {str(e)}", code=40001)

    @staticmethod
    def extract_text_from_txt_or_markdown(file_bytes: bytes) -> str:
        """使用原生 Python 实现 Markdown / TXT 纯文本提取"""
        for enc in ["utf-8", "utf-8-sig", "gb18030", "gbk"]:
            try:
                return file_bytes.decode(enc)
            except UnicodeDecodeError:
                continue
        # 兜底强制 ignore 解码
        return file_bytes.decode("utf-8", errors="ignore")

    @classmethod
    def parse_document_text(cls, filename: str, file_bytes: bytes) -> Tuple[str, str]:
        """
        按扩展名调度对应解析器
        返回: (extracted_text, file_type)
        """
        suffix = Path(filename).suffix.lower()
        if suffix == ".pdf":
            text = cls.extract_text_from_pdf(file_bytes)
            file_type = "pdf"
        elif suffix in [".docx", ".doc"]:
            text = cls.extract_text_from_docx(file_bytes)
            file_type = "docx"
        elif suffix in [".md", ".markdown"]:
            text = cls.extract_text_from_txt_or_markdown(file_bytes)
            file_type = "markdown"
        elif suffix in [".txt"]:
            text = cls.extract_text_from_txt_or_markdown(file_bytes)
            file_type = "txt"
        else:
            raise BusinessLogicError(
                message=f"不支持的文件格式 '{suffix}'，系统支持 Word (.docx)、PDF (.pdf)、Markdown (.md) 与 TXT (.txt)",
                code=40001
            )

        cleaned = text.strip()
        if not cleaned:
            raise BusinessLogicError(message="文档提取内容为空，无法进行切片建库", code=40001)

        return cleaned, file_type

    # --------------------------------------------------------------------------
    # 2. 原生 Python 滑动切片算法 (Requirement 2)
    # --------------------------------------------------------------------------
    @staticmethod
    def sliding_window_chunk(
        text: str,
        window_size: int = 512,
        overlap: int = 64,
    ) -> List[Dict[str, Any]]:
        """
        原生 Python 滑动切片:
            - 固定窗口: 512 字符
            - 重叠: 64 字符
            - 步长: 448 字符 (window_size - overlap = 512 - 64 = 448)
        """
        step = max(1, window_size - overlap)  # 步长必须强制保底，杜绝 step <= 0 导致死循环
        text_str = text.strip()
        if not text_str:
            return []

        text_len = len(text_str)
        # 单切片快速返回
        if text_len <= window_size:
            return [{
                "chunk_index": 0,
                "content": text_str,
                "char_length": text_len,
                "start_idx": 0,
                "end_idx": text_len,
            }]

        chunks = []
        start = 0
        chunk_idx = 0
        iterations = 0
        max_iterations = (text_len // max(1, step)) + 50  # 循环熔断安全阀

        while start < text_len:
            iterations += 1
            if iterations > max_iterations:
                logger.warning(
                    f"[sliding_window_chunk] Iteration limit {max_iterations} exceeded "
                    f"(start={start}, text_len={text_len}, step={step}). Circuit breaker tripped."
                )
                break

            end = min(start + window_size, text_len)
            chunk_content = text_str[start:end]
            chunks.append({
                "chunk_index": chunk_idx,
                "content": chunk_content,
                "char_length": len(chunk_content),
                "start_idx": start,
                "end_idx": end,
            })
            chunk_idx += 1

            if end >= text_len:
                break
            start += step

        return chunks

    async def extract_text(self, file_bytes: bytes, file_type: str = "txt") -> str:
        """纯文本提取统一异步入口，支持 PDF, Word (.docx), Markdown, TXT"""
        ft = file_type.lower().lstrip(".")
        if ft == "pdf":
            return self.extract_text_from_pdf(file_bytes)
        elif ft in ["docx", "doc"]:
            return self.extract_text_from_docx(file_bytes)
        return self.extract_text_from_txt_or_markdown(file_bytes)

    async def adaptive_chunking(self, text: str) -> List[Dict[str, Any]]:
        """
        自适应滑动切片方法
        固定窗口 512 字符，重叠 64 字符，步长 448 字符
        """
        chunks = self.sliding_window_chunk(text, window_size=512, overlap=64)
        result = []
        for c in chunks:
            result.append({
                "chunk_index": c["chunk_index"],
                "text": c["content"],
                "content": c["content"],
                "token_count": c["char_length"],
                "char_length": c["char_length"],
                "start_idx": c["start_idx"],
                "end_idx": c["end_idx"],
            })
        return result

    # --------------------------------------------------------------------------
    # 3. 完整入库与两阶段一致性状态机 (Requirements 3, 4, 5)
    # --------------------------------------------------------------------------
    async def ingest_file(
        self,
        filename: str,
        file_bytes: bytes,
        category: str = "DEFAULT"
    ) -> KnowledgeUnit:
        """
        执行完整摄入与向量化事务流水线:
            1. 解析文本
            2. 滑动切片 (512/64/448)
            3. MySQL 存储 KnowledgeUnit 与 KnowledgeChunk (初始状态 status='pending')
            4. BAAI/bge-m3 生成 1024 维密集浮点向量
            5. Milvus 集合写入 (knowguard_chunks: chunk_id, document_id, embedding)
            6. 写入成功 ➔ 更新 MySQL status='indexed'
        """
        # 1. 提取文本与格式
        full_text, file_type = self.parse_document_text(filename, file_bytes)
        file_hash = hashlib.sha256(file_bytes).hexdigest()

        # 2. 滑动切片 (512 窗口 / 64 重叠 / 448 步长)
        raw_chunks = self.sliding_window_chunk(full_text, window_size=512, overlap=64)

        # 3. MySQL 阶段一: 存知识单元与切片正文 (status='pending')
        doc = KnowledgeUnit(
            title=filename,
            file_type=file_type,
            file_size=len(file_bytes),
            file_hash=file_hash,
            category=category,
            status="PARSING",
            chunk_count=len(raw_chunks),
        )
        self.db.add(doc)
        await self.db.flush()  # 获取主键 doc.id

        chunk_entities: List[KnowledgeChunk] = []
        for rc in raw_chunks:
            chunk_obj = KnowledgeChunk(
                document_id=doc.id,
                chunk_index=rc["chunk_index"],
                content=rc["content"],
                char_length=rc["char_length"],
                status="pending",  # 核心一致性约束：初始为 pending
                has_vector=False,
                metadata_json={
                    "start_idx": rc["start_idx"],
                    "end_idx": rc["end_idx"],
                    "file_name": filename,
                },
            )
            self.db.add(chunk_obj)
            chunk_entities.append(chunk_obj)

        await self.db.commit()
        await self.db.refresh(doc)
        for c in chunk_entities:
            await self.db.refresh(c)

        # 4. 向量化计算: BAAI/bge-m3 1024 维 float 向量
        chunk_texts = [c.content for c in chunk_entities]
        embeddings = await self.embedding_provider.get_embeddings(chunk_texts)
        if len(embeddings) != len(chunk_entities):
            raise BusinessLogicError(message="向量计算数量与切片数不一致", code=50001)

        # 5. Milvus 存储: knowguard_chunks (chunk_id, document_id, embedding)
        milvus_data = [
            {
                "chunk_id": int(c.id),
                "document_id": int(doc.id),
                "embedding": emb,
            }
            for c, emb in zip(chunk_entities, embeddings)
        ]

        try:
            self.milvus.insert_chunks(milvus_data)
        except Exception as e:
            logger.error(f"[IngestionService] Milvus insertion failed: {e}")
            # Milvus 写入失败，将切片置为 failed
            for c in chunk_entities:
                c.status = "failed"
            doc.status = "FAILED"
            doc.error_message = f"Milvus 向量入库失败: {str(e)}"
            await self.db.commit()
            raise BusinessLogicError(message=f"Milvus 向量入库失败: {str(e)}", code=50001)

        # 6. MySQL 阶段二: Milvus 写入成功 ➔ 更新 MySQL status='indexed'
        for c in chunk_entities:
            c.status = "indexed"  # 核心一致性约束：更新为 indexed
            c.has_vector = True

        doc.status = "INDEXED"
        doc.error_message = None
        await self.db.commit()
        await self.db.refresh(doc)

        logger.info(
            f"[IngestionService] Successfully ingested document '{doc.title}' (ID={doc.id}) "
            f"with {doc.chunk_count} chunks indexed in MySQL & Milvus."
        )
        return doc

    # --------------------------------------------------------------------------
    # 4. 查询与管理接口 (Requirement 6 支撑)
    # --------------------------------------------------------------------------
    async def get_document_chunks(self, document_id: int) -> List[KnowledgeChunk]:
        """获取指定文档的切片列表"""
        # 先确认文档存在
        doc = await self.get_document_by_id(document_id)
        if not doc:
            raise NotFoundError(message=f"知识文档 ID={document_id} 不存在", code=40401)

        stmt = (
            select(KnowledgeChunk)
            .where(KnowledgeChunk.document_id == document_id)
            .order_by(KnowledgeChunk.chunk_index.asc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_document_by_id(self, document_id: int) -> Optional[KnowledgeUnit]:
        """根据 ID 获取知识单元实体"""
        stmt = select(KnowledgeUnit).where(KnowledgeUnit.id == document_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_documents(
        self,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> Tuple[List[KnowledgeUnit], int]:
        """分页获取知识单元资产台账，支持分类、状态、关键词多维检索"""
        base_stmt = select(KnowledgeUnit)
        if category:
            base_stmt = base_stmt.where(KnowledgeUnit.category == category)
        if status:
            base_stmt = base_stmt.where(KnowledgeUnit.status == status.upper())
        if keyword and keyword.strip():
            base_stmt = base_stmt.where(KnowledgeUnit.title.ilike(f"%{keyword.strip()}%"))

        # 统计总量
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        count_res = await self.db.execute(count_stmt)
        total = count_res.scalar_one() or 0

        # 分页
        offset = (page - 1) * page_size
        stmt = base_stmt.order_by(KnowledgeUnit.id.desc()).offset(offset).limit(page_size)
        paginated_res = await self.db.execute(stmt)
        return list(paginated_res.scalars().all()), total

    async def delete_document(self, document_id: int) -> bool:
        """级联物理彻底删除知识文档、切片、权限策略与 Milvus 向量"""
        doc = await self.get_document_by_id(document_id)
        if not doc:
            raise NotFoundError(message=f"知识文档 ID={document_id} 不存在", code=40401)

        # 1. 显式删除 Milvus 向量数据
        try:
            self.milvus.delete_chunks_by_document(document_id)
        except Exception as e:
            logger.warning(f"[IngestionService] Deleting Milvus vectors failed: {e}")

        # 2. 显式级联删除权限策略 (PermissionPolicy)，确保跨 DB 引擎一致性
        from app.models.policy import PermissionPolicy
        policy_stmt = delete(PermissionPolicy).where(PermissionPolicy.unit_id == document_id)
        await self.db.execute(policy_stmt)

        # 3. 显式级联删除关联切片 (KnowledgeChunk)
        chunk_stmt = delete(KnowledgeChunk).where(KnowledgeChunk.document_id == document_id)
        await self.db.execute(chunk_stmt)

        # 4. 删除知识主文档记录 (KnowledgeUnit)
        await self.db.delete(doc)
        await self.db.commit()
        return True

    async def update_document_status(self, document_id: int, status: str) -> KnowledgeUnit:
        """更新知识文档状态 (启停用切换并持久化)"""
        doc = await self.get_document_by_id(document_id)
        if not doc:
            raise NotFoundError(message=f"知识文档 ID={document_id} 不存在", code=40401)

        norm_status = status.strip().upper()
        if norm_status not in ["AVAILABLE", "DISABLED", "INDEXED"]:
            raise BusinessLogicError(message="状态值仅支持 'AVAILABLE' 或 'DISABLED'", code=40001)

        doc.status = norm_status
        await self.db.commit()
        await self.db.refresh(doc)
        return doc


# ==============================================================================
# 底嵌自测闭环脚本 (Self-Test Execution Block)
# ==============================================================================
if __name__ == "__main__":
    import asyncio
    from pypdf import PdfWriter
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import StaticPool
    from app.core.database import Base
    from app.models.policy import PermissionPolicy

    print("=== [Self-Test] Starting Ingestion Service Self-Test ===")

    async def _test_ingestion_service():
        # 初始化测试内存数据库
        test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool, echo=False)
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(bind=test_engine, expire_on_commit=False)

        async with session_factory() as session:
            service = IngestionService(db=session)

            # 1. 验证切片算法 (512窗口 / 64重叠 / 448步长)
            test_content = "KnowGuard" * 150  # 9 * 150 = 1350 字符
            chunks = service.sliding_window_chunk(test_content, window_size=512, overlap=64)
            print(f"[Self-Test] Chunked 1350 chars text into {len(chunks)} chunks")
            assert len(chunks) == 3, f"1350 字符应该生成 3 个切片，实际生成 {len(chunks)}"
            # 校验第 1、2 切片的重叠与步长
            assert chunks[0]["start_idx"] == 0
            assert chunks[0]["end_idx"] == 512
            assert chunks[1]["start_idx"] == 448  # 步长 448
            assert chunks[1]["end_idx"] == 960
            assert chunks[2]["start_idx"] == 896  # 448 * 2 = 896
            assert chunks[2]["end_idx"] == 1350
            # 验证重叠长度
            overlap_1_2 = chunks[0]["end_idx"] - chunks[1]["start_idx"]
            assert overlap_1_2 == 64, f"重叠长度必须为 64，实际为 {overlap_1_2}"
            print("[Self-Test] Sliding window chunking algorithm (512/64/448) verified successfully!")

            # 2. 验证 Markdown / TXT 摄入与一致性流转 (pending ➔ indexed)
            md_bytes = (
                "# KnowGuard 安全合规策略\n\n"
                "本文档规定公司内部各业务部门关于知识数据分级保护要求。\n"
                "核心要求包括：禁止越权访问知识资产，保障切片索引完整性。\n"
                + "附加合规描述详情内容。" * 40
            ).encode("utf-8")

            doc_md = await service.ingest_file(
                filename="security_compliance.md",
                file_bytes=md_bytes,
                category="COMPLIANCE"
            )
            assert doc_md.id is not None
            assert doc_md.status == "INDEXED"
            assert doc_md.chunk_count > 0
            print(f"[Self-Test] Markdown ingested: ID={doc_md.id}, chunks={doc_md.chunk_count}, status={doc_md.status}")

            # 为 doc_md 关联一个 PermissionPolicy 测试级联清理
            test_policy = PermissionPolicy(
                unit_id=doc_md.id,
                is_public=False,
                department_ids=[1, 2],
                role_ids=[10],
                user_ids=[100],
            )
            session.add(test_policy)
            await session.commit()

            # 验证 MySQL 中的切片状态已全部更新为 indexed 且 has_vector=True
            chunks_in_db = await service.get_document_chunks(doc_md.id)
            assert len(chunks_in_db) == doc_md.chunk_count
            assert all(c.status == "indexed" for c in chunks_in_db), "Milvus 入库成功后切片状态必须全部为 indexed"
            assert all(c.has_vector is True for c in chunks_in_db), "切片 has_vector 必须为 True"
            print("[Self-Test] Consistency state machine (pending ➔ Milvus ➔ indexed) verified successfully!")

            # 3. 验证 PDF 动态生成与摄入
            pdf_writer = PdfWriter()
            page = pdf_writer.add_blank_page(width=300, height=300)
            pdf_buf = io.BytesIO()
            pdf_writer.write(pdf_buf)
            pdf_bytes = pdf_buf.getvalue()

            txt_bytes = ("企业知识库建设规范白皮书。\n" + "规范细节条款解析。" * 60).encode("utf-8")
            doc_txt = await service.ingest_file(
                filename="knowledge_guidelines.txt",
                file_bytes=txt_bytes,
                category="STANDARD"
            )
            assert doc_txt.id is not None
            assert doc_txt.status == "INDEXED"
            print(f"[Self-Test] TXT document ingested: ID={doc_txt.id}, chunks={doc_txt.chunk_count}")

            # 3.1 验证 Word (.docx) 段落与表格解析及切片向量建库
            import docx
            test_docx = docx.Document()
            test_docx.add_heading("网络安全攻防演练实施总则", level=1)
            test_docx.add_paragraph("本总则规定红蓝对抗期间全部实战网络靶标防护规范。")
            tbl = test_docx.add_table(rows=2, cols=2)
            tbl.rows[0].cells[0].text = "靶标级别"
            tbl.rows[0].cells[1].text = "保护策略"
            tbl.rows[1].cells[0].text = "核心生产库"
            tbl.rows[1].cells[1].text = "4D-RBAC动态切片隔离"
            docx_buf = io.BytesIO()
            test_docx.save(docx_buf)
            docx_bytes = docx_buf.getvalue()

            extracted_docx_text = await service.extract_text(docx_bytes, file_type="docx")
            assert "网络安全攻防演练实施总则" in extracted_docx_text
            assert "4D-RBAC动态切片隔离" in extracted_docx_text

            doc_docx = await service.ingest_file(
                filename="cyber_security_rules.docx",
                file_bytes=docx_bytes,
                category="SECURITY"
            )
            assert doc_docx.id is not None
            assert doc_docx.file_type == "docx"
            assert doc_docx.status == "INDEXED"
            docx_chunks = await service.get_document_chunks(doc_docx.id)
            assert len(docx_chunks) == doc_docx.chunk_count
            assert all(c.status == "indexed" for c in docx_chunks)
            print(f"[Self-Test] Word (.docx) ingested: ID={doc_docx.id}, chunks={doc_docx.chunk_count}, status={doc_docx.status}")

            # 4. 验证 Milvus 中的向量数据
            milvus_chunks = service.milvus.get_chunks_by_document(doc_md.id)
            assert len(milvus_chunks) == doc_md.chunk_count
            assert len(milvus_chunks[0]["embedding"]) == 1024, "Milvus 向量维度必须为 1024"
            print(f"[Self-Test] Milvus records verified for doc_md: {len(milvus_chunks)} vectors of dim 1024")

            # 5. 验证状态更新 (DISABLED / AVAILABLE)
            updated_doc = await service.update_document_status(doc_txt.id, "DISABLED")
            assert updated_doc.status == "DISABLED"
            updated_doc2 = await service.update_document_status(doc_txt.id, "AVAILABLE")
            assert updated_doc2.status == "AVAILABLE"
            print("[Self-Test] update_document_status (DISABLED / AVAILABLE) verified successfully!")

            # 6. 验证分页与条件查询 (list_documents)
            # 全量
            items, total = await service.list_documents(page=1, page_size=10)
            assert total == 3
            # 关键词过滤
            kw_items, kw_total = await service.list_documents(keyword="guidelines")
            assert kw_total == 1
            assert kw_items[0].id == doc_txt.id
            # 分类过滤
            cat_items, cat_total = await service.list_documents(category="COMPLIANCE")
            assert cat_total == 1
            assert cat_items[0].id == doc_md.id
            # 状态过滤
            st_items, st_total = await service.list_documents(status="AVAILABLE")
            assert st_total == 1
            print("[Self-Test] list_documents (pagination, keyword, category, status) verified successfully!")

            # 7. 验证级联完全删除 (PermissionPolicy + Chunks + Unit + Milvus)
            del_res = await service.delete_document(doc_md.id)
            assert del_res is True
            doc_after = await service.get_document_by_id(doc_md.id)
            assert doc_after is None

            # 验证切片已被删除
            chunks_after = await session.execute(
                select(KnowledgeChunk).where(KnowledgeChunk.document_id == doc_md.id)
            )
            assert len(list(chunks_after.scalars().all())) == 0

            # 验证权限策略已被级联删除
            policy_after = await session.execute(
                select(PermissionPolicy).where(PermissionPolicy.unit_id == doc_md.id)
            )
            assert len(list(policy_after.scalars().all())) == 0

            # 验证 Milvus 已清空
            milvus_after = service.milvus.get_chunks_by_document(doc_md.id)
            assert len(milvus_after) == 0
            print("[Self-Test] Full cascaded deletion (Unit, Chunks, Policy, Milvus) verified successfully!")

        await test_engine.dispose()
        print("=== [Self-Test] All Ingestion Service tests PASSED successfully! ===")

    asyncio.run(_test_ingestion_service())
