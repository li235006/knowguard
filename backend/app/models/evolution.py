"""
知识自进化与沉淀引擎实体模型 (FAQ, FAQCandidate, KnowledgeGap)

职责:
    - 标准 FAQ 问答库模型 (FAQ / FAQItem): 表名 faqs, 标准问、标准答、分类、相似问别名、命中频次、状态
    - 候选 FAQ 挖掘池模型 (FAQCandidate): 表名 faq_candidates, 聚类簇标识、聚类频次、置信度、推荐答案、审核状态
    - 知识盲区与缺口模型 (KnowledgeGap): 表名 knowledge_gaps, 检索未命中/频繁受限问题文本、累计频次、工单转建状态

架构定位:
    持久化数据模型层 (Data Models) / 模块五: 知识自进化与沉淀引擎 (MySQL 8.0+)

作者:
    System Architect (系统架构组) & Backend Team
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class FAQ(BaseModel):
    """官方标准 FAQ 实体 (表名: faqs, 严格对齐 MVP 8.4 节)"""
    __tablename__ = "faqs"
    __table_args__ = {"extend_existing": True}

    standard_question: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    standard_answer: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(64), default="DEFAULT")
    similar_questions: Mapped[List[str]] = mapped_column(JSON, default=list)
    is_cached: Mapped[bool] = mapped_column(Boolean, default=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    hit_count: Mapped[int] = mapped_column(Integer, default=0)
    candidate_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


# 兼容别名
FAQItem = FAQ


class FAQCandidate(BaseModel):
    """高频挖掘候选 FAQ 实体 (表名: faq_candidates, 严格对齐 MVP 8.4 节)"""
    __tablename__ = "faq_candidates"
    __table_args__ = {"extend_existing": True}

    cluster_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    cluster_count: Mapped[int] = mapped_column(Integer, default=1)
    suggested_question: Mapped[str] = mapped_column(String(512), nullable=False)
    suggested_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    sample_queries: Mapped[List[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", index=True)  # PENDING, ACCEPTED, REJECTED

    @property
    def similar_queries(self) -> List[str]:
        return self.sample_queries

    @similar_queries.setter
    def similar_queries(self, val: List[str]):
        self.sample_queries = val


class KnowledgeGap(BaseModel):
    """知识盲区与缺口工单实体 (表名: knowledge_gaps)"""
    __tablename__ = "knowledge_gaps"
    __table_args__ = {"extend_existing": True}

    query_text: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    hit_count: Mapped[int] = mapped_column(Integer, default=1)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reason: Mapped[str] = mapped_column(String(64), default="MISSING_KNOWLEDGE")
    status: Mapped[str] = mapped_column(String(32), default="OPEN")  # OPEN, CONVERTED, DISMISSED
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


if __name__ == "__main__":
    print("=== [Self-Test] Starting Evolution Models Self-Test ===")
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session
    from app.core.database import Base

    test_engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        cand = FAQCandidate(
            cluster_id="cluster-fa9102",
            cluster_count=5,
            suggested_question="如何申请报销年终差旅补贴？",
            suggested_answer="请登录 OA 流程中心进入财务报销审批流。",
            confidence_score=0.9625,
            status="PENDING",
            sample_queries=["差旅补贴怎么报销", "年终差旅报销流程"],
        )
        session.add(cand)
        session.flush()
        assert cand.id is not None
        assert cand.__tablename__ == "faq_candidates"
        assert cand.similar_queries == ["差旅补贴怎么报销", "年终差旅报销流程"]

        faq = FAQ(
            standard_question="如何申请报销年终差旅补贴？",
            standard_answer="请登录 OA 流程中心进入财务报销审批流。",
            category="财务制度",
            similar_questions=["差旅补贴怎么报销"],
            hit_count=0,
            is_cached=True,
            is_enabled=True,
            candidate_id=cand.id,
        )
        session.add(faq)
        session.flush()
        assert faq.id is not None
        assert faq.__tablename__ == "faqs"
        assert FAQItem is FAQ

        gap = KnowledgeGap(
            query_text="2026年境外股票投资合规政策",
            hit_count=3,
            status="OPEN",
        )
        session.add(gap)
        session.flush()
        assert gap.id is not None
        assert gap.__tablename__ == "knowledge_gaps"

        session.commit()
        print(f"[Self-Test] FAQ created: ID={faq.id}, table={faq.__tablename__}")
        print(f"[Self-Test] FAQCandidate created: ID={cand.id}, table={cand.__tablename__}")
        print(f"[Self-Test] KnowledgeGap created: ID={gap.id}, table={gap.__tablename__}")

    print("=== [Self-Test] All Evolution Models tests PASSED successfully! ===")
