"""
知识单元与解析切片数据契约 (Knowledge Schemas)

职责:
    - 知识文件上传与批量上传请求模型
    - 知识单元详情、台账分页查询与启停用模型
    - 知识切片检索明细与元数据响应模型 (对齐前端与 Milvus 字段)

架构定位:
    数据契约层 (Schemas) / 模块二: 知识维护与解析管道

作者:
    System Architect (系统架构组) & Backend Team
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class KnowledgeUnitBase(BaseModel):
    """知识单元基础属性"""
    title: str = Field(..., description="知识文档标题")
    file_type: str = Field(..., description="文档格式 (pdf, markdown, txt)")
    category: str = Field(default="DEFAULT", description="知识分类")


class KnowledgeUnitCreate(KnowledgeUnitBase):
    """创建知识单元请求模型"""
    file_size: int = Field(default=0, description="文件大小 (字节)")
    file_hash: Optional[str] = Field(None, description="文件哈希")


class KnowledgeUnitStatusUpdate(BaseModel):
    """知识单元启停用状态更新请求模型"""
    status: str = Field(..., description="目标状态: AVAILABLE (启用) / DISABLED (停用)")

    @model_validator(mode="before")
    @classmethod
    def validate_and_normalize_status(cls, data: Any) -> Any:
        if isinstance(data, dict):
            raw_s = data.get("status", "")
            if isinstance(raw_s, str):
                norm = raw_s.strip().upper()
                if norm not in ["AVAILABLE", "DISABLED", "INDEXED"]:
                    raise ValueError("状态值仅支持 'AVAILABLE' 或 'DISABLED'")
                data["status"] = norm
        return data


class KnowledgeUnitResponse(BaseModel):
    """知识单元详情响应模型 (对齐前端 KnowledgeUnit 接口)"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="知识单元主键 ID / document_id")
    title: str = Field(..., description="文档标题")
    file_type: str = Field(..., description="文件格式")
    file_size: int = Field(default=0, description="文件大小")
    category: str = Field(default="DEFAULT", description="知识分类")
    status: str = Field(..., description="状态: PENDING / PARSING / CHUNKING / INDEXED / FAILED")
    chunk_count: int = Field(default=0, description="切片总数")
    error_message: Optional[str] = Field(None, description="异常报错信息")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class KnowledgeChunkResponse(BaseModel):
    """切片明细与向量状态响应模型 (兼容前端 ChunkItem 及 Milvus 结构)"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int = Field(..., description="切片主键 ID / chunk_id")
    chunk_id: Optional[int] = Field(None, description="切片编号 (等同于 id)")
    document_id: int = Field(..., description="所属知识文档 ID")
    unit_id: int = Field(..., description="所属知识文档 ID (前端别名)")
    chunk_index: int = Field(..., description="切片索引序号 (0-based)")
    content: str = Field(..., description="切片正文纯文本")
    char_length: int = Field(default=0, description="字符长度")
    status: str = Field(..., description="切片状态: pending / indexed / failed")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="切片元数据")
    has_vector: bool = Field(default=False, description="是否已写入向量库")
    created_at: Optional[datetime] = Field(None, description="创建时间")

    @model_validator(mode="before")
    @classmethod
    def populate_aliases_and_metadata(cls, data: Any) -> Any:
        if hasattr(data, "__dict__"):
            # ORM 实体转换
            obj_id = getattr(data, "id", None)
            doc_id = getattr(data, "document_id", getattr(data, "unit_id", None))
            meta = getattr(data, "metadata_json", {}) or {}
            status_val = getattr(data, "status", "pending")
            has_vec = getattr(data, "has_vector", False)
            return {
                "id": obj_id,
                "chunk_id": obj_id,
                "document_id": doc_id,
                "unit_id": doc_id,
                "chunk_index": getattr(data, "chunk_index", 0),
                "content": getattr(data, "content", ""),
                "char_length": getattr(data, "char_length", 0),
                "status": status_val,
                "metadata": meta,
                "has_vector": has_vec,
                "created_at": getattr(data, "created_at", None),
            }
        elif isinstance(data, dict):
            obj_id = data.get("id") or data.get("chunk_id")
            doc_id = data.get("document_id") or data.get("unit_id")
            if "chunk_id" not in data or data["chunk_id"] is None:
                data["chunk_id"] = obj_id
            if "unit_id" not in data or data["unit_id"] is None:
                data["unit_id"] = doc_id
            if "document_id" not in data or data["document_id"] is None:
                data["document_id"] = doc_id
            if "metadata" not in data:
                data["metadata"] = data.get("metadata_json", {})
        return data


class BatchUploadResponse(BaseModel):
    """批量上传与异步任务分发响应"""
    total: int = Field(..., description="处理总数")
    success_count: int = Field(..., description="成功导入文档数")
    failed_count: int = Field(0, description="失败数")
    items: List[KnowledgeUnitResponse] = Field(default_factory=list, description="知识文档列表")


# ==============================================================================
# 底嵌自测闭环脚本 (Self-Test Execution Block)
# ==============================================================================
if __name__ == "__main__":
    print("=== [Self-Test] Starting Knowledge Schemas Self-Test ===")
    now = datetime.now()

    # 1. 验证 KnowledgeUnitResponse
    unit_res = KnowledgeUnitResponse(
        id=101,
        title="测试技术白皮书.pdf",
        file_type="pdf",
        file_size=20480,
        category="TECH",
        status="INDEXED",
        chunk_count=10,
        created_at=now,
    )
    assert unit_res.id == 101
    assert unit_res.status == "INDEXED"
    print(f"[Self-Test] KnowledgeUnitResponse verified: {unit_res.title}")

    # 2. 验证 KnowledgeChunkResponse 字典转化与别名自动填充
    chunk_raw = {
        "id": 501,
        "document_id": 101,
        "chunk_index": 0,
        "content": "KnowGuard 架构安全防护规范切片测试",
        "char_length": 22,
        "status": "indexed",
        "has_vector": True,
        "metadata": {"start_pos": 0, "end_pos": 22}
    }
    chunk_res = KnowledgeChunkResponse.model_validate(chunk_raw)
    assert chunk_res.chunk_id == 501
    assert chunk_res.unit_id == 101
    assert chunk_res.has_vector is True
    assert chunk_res.status == "indexed"
    print(f"[Self-Test] KnowledgeChunkResponse verified: chunk_id={chunk_res.chunk_id}, unit_id={chunk_res.unit_id}")

    print("=== [Self-Test] All Knowledge Schemas tests PASSED successfully! ===")
