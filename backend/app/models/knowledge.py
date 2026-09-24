"""
知识单元与切片持久化模型 (KnowledgeUnit, KnowledgeChunk)

职责:
    - 知识单元主表 (KnowledgeUnit): 资产编号、标题、分类、原始文件路径、解析状态、哈希特征 (存储于 MySQL 8.0+)
    - 知识切片元数据表 (KnowledgeChunk): 切片序号、文本内容、元数据 (页码/标题/Chunk ID) 存储于 MySQL 8.0+，
      与 Milvus 2.4+ 向量集合 (knowguard_chunks, 1024 维 BGE-M3, HNSW 索引) 关联对齐

架构定位:
    持久化数据模型层 (Data Models) / 模块二: 知识维护与解析管道

作者:
    System Architect (系统架构组) & Backend Team
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text, select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class KnowledgeUnit(BaseModel):
    """知识单元资产主表实体 (MySQL 8.0+)"""
    __tablename__ = "knowledge_units"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="知识文件标题/文档名")
    file_type: Mapped[str] = mapped_column(String(64), nullable=False, comment="文件类型 (pdf, markdown, txt)")
    file_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="物理文件存储路径或对象存储 URI")
    file_size: Mapped[int] = mapped_column(Integer, default=0, comment="原始文件大小 (字节)")
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True, comment="文件 SHA-256 哈希防重指纹")
    category: Mapped[str] = mapped_column(String(128), default="DEFAULT", index=True, comment="知识分类")
    status: Mapped[str] = mapped_column(
        String(32),
        default="PENDING",
        nullable=False,
        index=True,
        comment="资产解析状态 (PENDING / PARSING / CHUNKING / INDEXED / FAILED)"
    )
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, comment="切片总分块数")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="解析或向量化异常错误日志")

    # 级联切片关联
    chunks: Mapped[List["KnowledgeChunk"]] = relationship(
        "KnowledgeChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="KnowledgeChunk.chunk_index"
    )

    def __repr__(self) -> str:
        return f"<KnowledgeUnit id={self.id} title={self.title} status={self.status} chunks={self.chunk_count}>"


class KnowledgeChunk(BaseModel):
    """
    知识切片元数据实体 (MySQL 8.0+ 存储切片元数据，向量特征索引于 Milvus 2.4+)
    一致性状态机: status 初始为 pending，Milvus 向量写入成功后置为 indexed，失败置为 failed
    """
    __tablename__ = "knowledge_chunks"

    document_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("knowledge_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="关联知识单元主表 ID"
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="切片序号 (0-based)")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="切片纯文本正文内容")
    char_length: Mapped[int] = mapped_column(Integer, default=0, comment="切片正文字符长度")
    status: Mapped[str] = mapped_column(
        String(32),
        default="pending",
        nullable=False,
        index=True,
        comment="切片向量化状态 (pending: 待入库 / indexed: 已同步 Milvus / failed: 失败)"
    )
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
        comment="切片元数据 (如 start_pos, end_pos, page_no, chunk_id)"
    )
    has_vector: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否已成功生成并在 Milvus 建库向量")

    # 反向关联主文档
    document: Mapped["KnowledgeUnit"] = relationship("KnowledgeUnit", back_populates="chunks")

    @property
    def unit_id(self) -> int:
        """兼容前端 unit_id 契约字段"""
        return self.document_id

    @unit_id.setter
    def unit_id(self, val: int) -> None:
        self.document_id = val

    def __repr__(self) -> str:
        return f"<KnowledgeChunk id={self.id} doc_id={self.document_id} idx={self.chunk_index} status={self.status}>"


# ==============================================================================
# 底嵌自测闭环脚本 (Self-Test Execution Block)
# ==============================================================================
if __name__ == "__main__":
    import asyncio
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import StaticPool
    from app.core.database import Base

    print("=== [Self-Test] Starting Knowledge Models Self-Test ===")

    async def _test_knowledge_models():
        test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool, echo=False)
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(bind=test_engine, expire_on_commit=False)

        async with session_factory() as session:
            # 1. 创建知识文档
            doc = KnowledgeUnit(
                title="员工安全合规手册2026.pdf",
                file_type="pdf",
                file_size=10240,
                file_hash="mock-sha256-hash-001",
                category="COMPLIANCE",
                status="PARSING",
                chunk_count=2,
            )
            session.add(doc)
            await session.commit()
            await session.refresh(doc)
            assert doc.id is not None
            assert doc.status == "PARSING"
            print(f"[Self-Test] Created KnowledgeUnit ID={doc.id}, title='{doc.title}'")

            # 2. 插入初始状态为 pending 的切片
            chunk1 = KnowledgeChunk(
                document_id=doc.id,
                chunk_index=0,
                content="这是第一段测试切片内容，长度未满512字符。",
                char_length=23,
                status="pending",
                has_vector=False,
                metadata_json={"page": 1, "start_pos": 0, "end_pos": 23}
            )
            chunk2 = KnowledgeChunk(
                document_id=doc.id,
                chunk_index=1,
                content="这是第二段测试切片内容，承接上下文滑动重叠。",
                char_length=23,
                status="pending",
                has_vector=False,
                metadata_json={"page": 1, "start_pos": 20, "end_pos": 43}
            )
            session.add_all([chunk1, chunk2])
            await session.commit()

            # 3. 验证 pending 状态
            stmt = select(KnowledgeChunk).where(KnowledgeChunk.document_id == doc.id)
            res = await session.execute(stmt)
            saved_chunks = list(res.scalars().all())
            assert len(saved_chunks) == 2
            assert all(c.status == "pending" for c in saved_chunks)
            assert saved_chunks[0].unit_id == doc.id
            print(f"[Self-Test] Saved 2 chunks with initial status='pending'")

            # 4. 模拟向量写入成功后状态转换为 indexed
            for c in saved_chunks:
                c.status = "indexed"
                c.has_vector = True
            doc.status = "INDEXED"
            await session.commit()

            # 5. 重新查询验证一致性变更
            res_after = await session.execute(stmt)
            updated_chunks = list(res_after.scalars().all())
            assert all(c.status == "indexed" for c in updated_chunks)
            assert all(c.has_vector is True for c in updated_chunks)
            print(f"[Self-Test] Updated chunks status to 'indexed' and has_vector=True successfully")

        await test_engine.dispose()
        print("=== [Self-Test] All Knowledge Models tests PASSED successfully! ===")

    asyncio.run(_test_knowledge_models())
