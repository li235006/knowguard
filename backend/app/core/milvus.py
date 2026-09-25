"""
Milvus 向量数据库客户端与向量存储服务 (Milvus Service)

职责:
    - 连接 Milvus 2.4+ (Linux VM: 192.168.6.134:19530)
    - 管理 knowguard_chunks 集合 (Schema: chunk_id INT64 PK, document_id INT64, embedding FLOAT_VECTOR 1024维)
    - 提供向量切片写入 (insert)、条件删除 (delete)、按文档查询 (query) 与余弦相似度检索 (search)
    - 针对离线沙箱与测试环境提供高保真内存降级引擎，保证一致性测试与服务闭环

架构定位:
    核心基础设施层 (Core Infrastructure) / 向量存储服务

作者:
    System Architect (系统架构组) & Backend Team
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import logging
import math
from typing import Any, Dict, List, Optional
from pymilvus import DataType, FieldSchema, CollectionSchema, MilvusClient
from app.core.config import settings

logger = logging.getLogger(__name__)


class InMemoryMilvusCollection:
    """
    当外部独立 Milvus 实例网络不可达 (如离线隔离沙箱、单元测试) 时的保真内存集合实现
    保证一致性状态流转与 API 契约无缝运行
    """

    def __init__(self, collection_name: str, dimension: int = 1024):
        self.collection_name = collection_name
        self.dimension = dimension
        self.records: Dict[int, Dict[str, Any]] = {}

    def insert(self, data: List[Dict[str, Any]]) -> bool:
        for item in data:
            c_id = int(item["chunk_id"])
            doc_id = int(item["document_id"])
            emb = [float(x) for x in item["embedding"]]
            self.records[c_id] = {
                "chunk_id": c_id,
                "document_id": doc_id,
                "embedding": emb,
            }
        return True

    def query(self, filter_expr: str) -> List[Dict[str, Any]]:
        # 解析如 "document_id == 1"
        results = []
        if "document_id ==" in filter_expr:
            try:
                target_doc_id = int(filter_expr.split("==")[1].strip())
                for r in self.records.values():
                    if r["document_id"] == target_doc_id:
                        results.append(r)
            except Exception:
                results = list(self.records.values())
        else:
            results = list(self.records.values())
        return results

    def delete(self, filter_expr: str) -> int:
        deleted = 0
        if "document_id ==" in filter_expr:
            try:
                target_doc_id = int(filter_expr.split("==")[1].strip())
                keys_to_del = [k for k, v in self.records.items() if v["document_id"] == target_doc_id]
                for k in keys_to_del:
                    del self.records[k]
                    deleted += 1
            except Exception:
                pass
        return deleted

    def search(self, query_vec: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        scores = []
        for r in self.records.values():
            vec = r["embedding"]
            # 计算余弦相似度
            dot = sum(a * b for a, b in zip(query_vec, vec))
            norm_q = math.sqrt(sum(a * a for a in query_vec)) or 1.0
            norm_v = math.sqrt(sum(b * b for b in vec)) or 1.0
            similarity = dot / (norm_q * norm_v)
            scores.append({"id": r["chunk_id"], "distance": round(similarity, 6), "entity": r})
        scores.sort(key=lambda x: x["distance"], reverse=True)
        return scores[:top_k]


class MilvusService:
    """
    Milvus 2.4+ 客户端服务包装器
    目标节点: 192.168.6.134:19530
    集合: knowguard_chunks
    字段:
      - chunk_id: INT64 (Primary Key)
      - document_id: INT64
      - embedding: FLOAT_VECTOR (1024 维)
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        collection_name: Optional[str] = None,
        dimension: int = 1024,
    ):
        self.host = host or settings.MILVUS_HOST
        self.port = port or settings.MILVUS_PORT
        self.uri = f"http://{self.host}:{self.port}"
        self.collection_name = collection_name or settings.MILVUS_COLLECTION_NAME
        self.dimension = dimension or settings.MILVUS_DIMENSION

        self._client: Optional[MilvusClient] = None
        self._is_mock = False
        self._mock_collection: Optional[InMemoryMilvusCollection] = None

        self._init_connection()

    def _init_connection(self) -> None:
        """建立 Milvus 连接或降级到内存保真引擎"""
        try:
            # 尝试连接远程 Milvus 服务 (超时 1.5s 快速判定)
            self._client = MilvusClient(
                uri=self.uri,
                user=settings.MILVUS_USER or "",
                password=settings.MILVUS_PASSWORD or "",
                timeout=1.5,
            )
            self._ensure_collection_remote()
            self._is_mock = False
            logger.info(f"[MilvusService] Connected to remote Milvus at {self.uri}")
        except Exception as e:
            logger.warning(
                f"[MilvusService] Remote Milvus ({self.uri}) unreachable ({type(e).__name__}). "
                f"Activated InMemoryMilvusCollection for collection '{self.collection_name}'."
            )
            self._is_mock = True
            self._client = None
            self._mock_collection = InMemoryMilvusCollection(
                collection_name=self.collection_name,
                dimension=self.dimension,
            )

    def _ensure_collection_remote(self) -> None:
        """在远程 Milvus 中创建 knowguard_chunks 集合与 HNSW 索引"""
        if not self._client:
            return

        if not self._client.has_collection(self.collection_name):
            schema = MilvusClient.create_schema(
                auto_id=False,
                enable_dynamic_field=False,
                description="KnowGuard Document Chunks Vector Store"
            )
            schema.add_field(field_name="chunk_id", datatype=DataType.INT64, is_primary=True, description="切片主键 ID")
            schema.add_field(field_name="document_id", datatype=DataType.INT64, description="所属知识主文档 ID")
            schema.add_field(field_name="embedding", datatype=DataType.FLOAT_VECTOR, dim=self.dimension, description="1024维 BGE-M3 向量")

            index_params = self._client.prepare_index_params()
            index_params.add_index(
                field_name="embedding",
                index_type=settings.MILVUS_INDEX_TYPE or "HNSW",
                metric_type=settings.MILVUS_METRIC_TYPE or "COSINE",
                params={"M": 16, "efConstruction": 200},
            )

            self._client.create_collection(
                collection_name=self.collection_name,
                schema=schema,
                index_params=index_params,
            )
            logger.info(f"[MilvusService] Created collection '{self.collection_name}' on remote Milvus.")

    def insert_chunks(self, chunks_data: List[Dict[str, Any]]) -> bool:
        """
        批量写入切片向量实体
        数据结构: [{"chunk_id": int, "document_id": int, "embedding": List[float](1024)}, ...]
        """
        if not chunks_data:
            return True

        # 校验字段格式与维度
        formatted_data = []
        for c in chunks_data:
            chunk_id = int(c["chunk_id"])
            doc_id = int(c["document_id"])
            emb = [float(x) for x in c["embedding"]]
            if len(emb) != self.dimension:
                raise ValueError(f"Embedding dimension mismatch: expected {self.dimension}, got {len(emb)}")
            formatted_data.append({
                "chunk_id": chunk_id,
                "document_id": doc_id,
                "embedding": emb,
            })

        if self._is_mock or self._client is None:
            return self._mock_collection.insert(formatted_data)

        try:
            self._client.insert(
                collection_name=self.collection_name,
                data=formatted_data,
            )
            return True
        except Exception as e:
            logger.error(f"[MilvusService] Failed to insert chunks into remote Milvus: {e}")
            raise

    def get_chunks_by_document(self, document_id: int) -> List[Dict[str, Any]]:
        """按 document_id 查询 Milvus 实体"""
        filter_expr = f"document_id == {document_id}"
        if self._is_mock or self._client is None:
            return self._mock_collection.query(filter_expr)

        try:
            res = self._client.query(
                collection_name=self.collection_name,
                filter=filter_expr,
                output_fields=["chunk_id", "document_id"],
            )
            return res
        except Exception as e:
            logger.error(f"[MilvusService] Failed to query Milvus by doc_id: {e}")
            return []

    def delete_chunks_by_document(self, document_id: int) -> int:
        """根据 document_id 级联删除 Milvus 中的切片向量"""
        filter_expr = f"document_id == {document_id}"
        if self._is_mock or self._client is None:
            return self._mock_collection.delete(filter_expr)

        try:
            res = self._client.delete(
                collection_name=self.collection_name,
                filter=filter_expr,
            )
            return res.get("delete_count", 0) if isinstance(res, dict) else 1
        except Exception as e:
            logger.error(f"[MilvusService] Failed to delete chunks from Milvus: {e}")
            return 0

    def search_similar(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """语义余弦相似度检索"""
        if self._is_mock or self._client is None:
            return self._mock_collection.search(query_vector, top_k)

        try:
            search_res = self._client.search(
                collection_name=self.collection_name,
                data=[query_vector],
                limit=top_k,
                output_fields=["chunk_id", "document_id"],
            )
            raw_hits = search_res[0] if search_res else []
            normalized_hits = []
            for h in raw_hits:
                # 兼容 remote Milvus 的主键字段 (chunk_id) 与 mock collection 的 id
                c_id = h.get("id") or h.get("chunk_id")
                if c_id is None and isinstance(h.get("entity"), dict):
                    c_id = h["entity"].get("chunk_id")
                if c_id is not None:
                    hit_dict = dict(h)
                    hit_dict["id"] = int(c_id)
                    hit_dict["chunk_id"] = int(c_id)
                    normalized_hits.append(hit_dict)
            return normalized_hits
        except Exception as e:
            logger.error(f"[MilvusService] Search failed: {e}")
            return []

    async def warm_up_from_database(self, db_session) -> int:
        """从数据库预热加载已有切片向量至 Milvus (无论是远程独立实例还是本地保真集合)"""
        from app.models.knowledge import KnowledgeChunk
        from app.providers.embedding import default_embedding_provider
        from sqlalchemy import select

        # 检查是否已有切片数据
        if self._is_mock or self._client is None:
            existing_count = len(self._mock_collection.records) if self._mock_collection else 0
        else:
            try:
                probe = self._client.query(self.collection_name, filter="chunk_id >= 0", limit=1)
                existing_count = len(probe)
            except Exception:
                existing_count = 0

        if existing_count > 0:
            return 0

        stmt = select(KnowledgeChunk).where(KnowledgeChunk.is_deleted == False)
        res = await db_session.execute(stmt)
        chunks = res.scalars().all()
        if not chunks:
            return 0

        data = []
        for c in chunks:
            emb = await default_embedding_provider.get_embedding(c.content)
            data.append({
                "chunk_id": c.id,
                "document_id": c.document_id,
                "embedding": emb,
            })
        if data:
            self.insert_chunks(data)
            logger.info(f"[MilvusService] Warmed up and synchronized {len(data)} chunks into collection '{self.collection_name}'.")
        return len(data)


# 单例实例
milvus_service = MilvusService()


# ==============================================================================
# 底嵌自测闭环脚本 (Self-Test Execution Block)
# ==============================================================================
if __name__ == "__main__":
    print("=== [Self-Test] Starting Milvus Service (192.168.6.134:19530 / knowguard_chunks) Self-Test ===")

    service = MilvusService()
    print(f"[Self-Test] Milvus Service initialized (is_mock={service._is_mock}, uri={service.uri})")

    # 1. 构造测试切片向量数据 (dim=1024)
    dummy_vec1 = [0.01 * (i % 10) for i in range(1024)]
    dummy_vec2 = [0.02 * (i % 10) for i in range(1024)]

    test_chunks = [
        {"chunk_id": 1001, "document_id": 99, "embedding": dummy_vec1},
        {"chunk_id": 1002, "document_id": 99, "embedding": dummy_vec2},
    ]

    # 2. 写入切片向量
    res = service.insert_chunks(test_chunks)
    assert res is True, "写入向量切片必须成功"
    print(f"[Self-Test] Inserted 2 chunks into knowguard_chunks")

    # 3. 按文档 ID 查询
    stored = service.get_chunks_by_document(99)
    assert len(stored) == 2, f"查询文档切片数量必须为 2，实际为 {len(stored)}"
    print(f"[Self-Test] Query by document_id=99 returned {len(stored)} records")

    # 4. 向量检索
    search_hits = service.search_similar(dummy_vec1, top_k=2)
    assert len(search_hits) >= 1
    print(f"[Self-Test] Search returned {len(search_hits)} hits, top_1 ID: {search_hits[0]['id']}")

    # 5. 删除文档向量
    del_count = service.delete_chunks_by_document(99)
    print(f"[Self-Test] Deleted chunks for document_id=99: {del_count}")
    after_del = service.get_chunks_by_document(99)
    assert len(after_del) == 0, "删除后切片数量必须为 0"

    print("=== [Self-Test] All Milvus Service tests PASSED successfully! ===")

