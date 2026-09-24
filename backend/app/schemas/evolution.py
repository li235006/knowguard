"""
知识自进化、FAQ 沉淀与知识缺口数据契约 (Evolution Schemas)

职责:
    - 聚类挖掘触发与候选 FAQ 列表响应模型
    - FAQ 审核采纳、在线发布与缓存开关模型
    - 知识缺口台账与一键转建工单模型

架构定位:
    数据契约层 (Schemas) / 模块五: 知识自进化与沉淀引擎

作者:
    System Architect (系统架构组)
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class FAQCreate(BaseModel):
    """创建/采纳 FAQ 存根"""
    pass


class FAQResponse(BaseModel):
    """标准 FAQ 问答详情响应存根"""
    pass


class FAQCandidateResponse(BaseModel):
    """候选 FAQ 推荐明细响应存根"""
    pass


class KnowledgeGapResponse(BaseModel):
    """知识缺口记录响应存根"""
    pass
