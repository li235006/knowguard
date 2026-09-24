"""
知识单元与切片持久化模型 (KnowledgeUnit, KnowledgeChunk)

职责:
    - 知识单元主表 (KnowledgeUnit): 资产编号、标题、分类、原始文件路径、解析状态、哈希特征 (存储于 MySQL 8.0+)
    - 知识切片元数据表 (KnowledgeChunk): 切片序号、文本内容、元数据 (页码/标题/Chunk ID) 存储于 MySQL 8.0+，与 Milvus 2.4+ 向量集合 (knowguard_chunks, 1024 维 BGE-M3, HNSW 索引) 关联对齐

架构定位:
    持久化数据模型层 (Data Models) / 模块二: 知识维护与解析管道

作者:
    System Architect (系统架构组)
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class KnowledgeUnit(BaseModel):
    """知识单元资产主表实体存根 (MySQL 8.0+)"""
    __tablename__ = "knowledge_units"
    pass


class KnowledgeChunk(BaseModel):
    """知识切片元数据实体存根 (MySQL 8.0+ 存储切片元数据，向量特征索引于 Milvus 2.4+)"""
    __tablename__ = "knowledge_chunks"
    pass
