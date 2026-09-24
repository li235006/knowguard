"""
知识自进化与沉淀引擎实体模型 (FAQItem, FAQCandidate, KnowledgeGap)

职责:
    - 标准 FAQ 问答库模型 (FAQItem): 标准问、标准答、分类、相似问别名、Redis 缓存使能状态
    - 候选 FAQ 挖掘池模型 (FAQCandidate): 聚类簇标识、聚类频次、置信度、推荐答案、审核状态
    - 知识盲区与缺口模型 (KnowledgeGap): 检索未命中/频繁受限问题文本、累计频次、工单转建状态

架构定位:
    持久化数据模型层 (Data Models) / 模块五: 知识自进化与沉淀引擎 (MySQL 8.0+)

作者:
    System Architect (系统架构组)
"""

from typing import List, Optional
from sqlalchemy import Boolean, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class FAQItem(BaseModel):
    """官方标准 FAQ 实体存根 (MySQL 8.0+)"""
    __tablename__ = "faq_items"
    pass


class FAQCandidate(BaseModel):
    """高频挖掘候选 FAQ 实体存根 (MySQL 8.0+)"""
    __tablename__ = "faq_candidates"
    pass


class KnowledgeGap(BaseModel):
    """知识盲区与缺口工单实体存根 (MySQL 8.0+)"""
    __tablename__ = "knowledge_gaps"
    pass
