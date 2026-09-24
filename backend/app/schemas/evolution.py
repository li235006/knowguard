"""
知识自进化、FAQ 沉淀与知识缺口数据契约 (Evolution Schemas)

职责:
    - 聚类挖掘触发与候选 FAQ 列表响应模型
    - FAQ 审核采纳、在线发布与缓存开关模型
    - 知识缺口台账与一键转建工单模型

架构定位:
    数据契约层 (Schemas) / 模块五: 知识自进化与沉淀引擎

作者:
    System Architect (系统架构组) & Backend Team
"""

from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class FAQCandidateResponse(BaseModel):
    """候选 FAQ 推荐明细响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="候选记录主键ID")
    cluster_id: str = Field(..., description="聚类簇标识")
    cluster_count: int = Field(..., description="簇内提问频次")
    suggested_question: str = Field(..., description="归纳的标准问题建议")
    suggested_answer: Optional[str] = Field(default=None, description="推荐答复草稿")
    confidence_score: float = Field(..., description="聚类置信度分值 (0.0~1.0)")
    sample_queries: List[str] = Field(default_factory=list, description="簇内聚合的用户真实提问样本")
    status: str = Field(default="PENDING", description="审核状态: PENDING/ACCEPTED/REJECTED")
    created_at: Optional[datetime] = Field(default=None, description="创建时间")
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")

    # 别名字段兼容
    @property
    def representative_question(self) -> str:
        return self.suggested_question

    @property
    def cluster_size(self) -> int:
        return self.cluster_count


class FAQCreate(BaseModel):
    """创建/采纳发布 FAQ 入参"""
    standard_question: Optional[str] = Field(default=None, min_length=1, max_length=512, description="标准问")
    standard_answer: Optional[str] = Field(default=None, min_length=1, description="标准答")
    question: Optional[str] = Field(default=None, description="标准问 (别名)")
    answer: Optional[str] = Field(default=None, description="标准答 (别名)")
    category: str = Field(default="DEFAULT", max_length=64, description="业务知识分类")
    similar_questions: List[str] = Field(default_factory=list, description="相似问/别名列表")
    similar_queries: Optional[List[str]] = Field(default=None, description="相似问列表 (别名)")
    is_cached: bool = Field(default=True, description="是否注入 Redis 极速直出缓存")
    is_enabled: bool = Field(default=True, description="是否启用生效")
    candidate_id: Optional[int] = Field(default=None, description="来源候选池记录 ID")

    @model_validator(mode="after")
    def sync_names(self) -> "FAQCreate":
        if not self.standard_question and self.question:
            self.standard_question = self.question
        elif not self.question and self.standard_question:
            self.question = self.standard_question

        if not self.standard_answer and self.answer:
            self.standard_answer = self.answer
        elif not self.answer and self.standard_answer:
            self.answer = self.standard_answer

        if not self.similar_questions and self.similar_queries:
            self.similar_questions = list(self.similar_queries)
        elif not self.similar_queries and self.similar_questions:
            self.similar_queries = list(self.similar_questions)

        return self


class FAQResponse(BaseModel):
    """标准 FAQ 问答详情响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="FAQ主键ID")
    standard_question: str = Field(..., description="标准问题")
    standard_answer: str = Field(..., description="标准回答")
    category: str = Field(default="DEFAULT", description="业务分类")
    similar_questions: List[str] = Field(default_factory=list, description="相似问别名列表")
    is_cached: bool = Field(default=True, description="是否启用缓存")
    is_enabled: bool = Field(default=True, description="启用/停用状态")
    hit_count: int = Field(default=0, description="缓存直出累计命中次数")
    candidate_id: Optional[int] = Field(default=None, description="关联候选记录ID")
    created_at: Optional[datetime] = Field(default=None, description="创建时间")
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")


class FAQStatusUpdate(BaseModel):
    """启用/停用 FAQ 入参"""
    is_enabled: Optional[bool] = Field(default=None, description="是否启用 (True启用, False停用)")
    status: Optional[Any] = Field(default=None, description="兼容状态字段")

    def get_is_enabled(self) -> bool:
        if self.is_enabled is not None:
            return bool(self.is_enabled)
        if self.status is not None:
            if isinstance(self.status, bool):
                return self.status
            if isinstance(self.status, (int, float)):
                return bool(self.status)
            if isinstance(self.status, str):
                return self.status.lower() in ("true", "1", "active", "enable", "enabled")
        return True


class KnowledgeGapResponse(BaseModel):
    """知识缺口记录响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="主键ID")
    query_text: str = Field(..., description="未命中或受限问题文本")
    hit_count: int = Field(default=1, description="累计受限/未命中频次")
    status: str = Field(default="OPEN", description="处理状态: OPEN/CONVERTED/DISMISSED")
    first_seen_at: Optional[datetime] = Field(default=None, description="首次出现时间")
    last_seen_at: Optional[datetime] = Field(default=None, description="最后出现时间")


class ClusterMiningRequest(BaseModel):
    """聚类挖掘请求入参"""
    similarity_threshold: float = Field(default=0.88, ge=0.5, le=1.0, description="余弦相似度聚类阈值")
    min_cluster_size: int = Field(default=2, ge=1, le=100, description="最小成簇提问频次")
    queries: Optional[List[str]] = Field(default=None, description="指定执行聚类的提问列表 (为空时从 Message 提取)")


class FAQMatchResponse(BaseModel):
    """FAQ 缓存匹配结果"""
    hit: bool = Field(..., description="是否命中缓存")
    faq_id: Optional[int] = Field(default=None, description="命中的 FAQ ID")
    standard_question: Optional[str] = Field(default=None, description="标准问")
    standard_answer: Optional[str] = Field(default=None, description="标准答")
    similarity: Optional[float] = Field(default=None, description="匹配相似度分值")
    hit_count: Optional[int] = Field(default=None, description="累计直出命中频次")
