"""
知识自进化、FAQ 审核与知识缺口控制器 (Evolution Router)

接口清单:
    - POST /api/v1/evolution/cluster-mining: 触发提问语义聚类挖掘
    - GET  /api/v1/evolution/candidates: 获取高频候选 FAQ 列表
    - POST /api/v1/evolution/faqs/publish: 采纳发布 FAQ 并注入 Redis 高速缓存
    - GET  /api/v1/evolution/knowledge-gaps: 查询知识盲区缺口池
    - POST /api/v1/evolution/knowledge-gaps/{id}/convert: 知识缺口一键转建为补充工单

架构定位:
    API 控制器层 / 模块五: 知识自进化与沉淀引擎

作者:
    System Architect (系统架构组)
"""

from fastapi import APIRouter
from app.schemas.common import PaginatedResponse, StandardResponse
from app.schemas.evolution import FAQCandidateResponse, FAQCreate, FAQResponse, KnowledgeGapResponse

router = APIRouter()


@router.get("/candidates", response_model=StandardResponse[PaginatedResponse[FAQCandidateResponse]])
async def list_faq_candidates():
    """查询聚类推荐候选 FAQ 列表存根"""
    pass


@router.post("/faqs/publish", response_model=StandardResponse[FAQResponse])
async def publish_faq(payload: FAQCreate):
    """发布 FAQ 并预热缓存存根"""
    pass


@router.get("/knowledge-gaps", response_model=StandardResponse[PaginatedResponse[KnowledgeGapResponse]])
async def list_knowledge_gaps():
    """查询知识缺口清单存根"""
    pass
