"""
知识单元与解析切片数据契约 (Knowledge Schemas)

职责:
    - 知识文件上传与批量上传请求模型
    - 知识单元详情、台账分页查询与启停用模型
    - 知识切片检索明细与元数据响应模型

架构定位:
    数据契约层 (Schemas) / 模块二: 知识维护与解析管道

作者:
    System Architect (系统架构组)
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class KnowledgeUnitCreate(BaseModel):
    """创建知识单元存根"""
    pass


class KnowledgeUnitResponse(BaseModel):
    """知识单元详情响应存根"""
    pass


class KnowledgeChunkResponse(BaseModel):
    """切片明细与向量状态响应存根"""
    pass


class BatchUploadResponse(BaseModel):
    """批量上传与异步任务分发响应存根"""
    pass
