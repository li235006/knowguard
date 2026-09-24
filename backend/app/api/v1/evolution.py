"""
知识自进化、FAQ 审核与知识缺口控制器 (Evolution Router)

接口清单:
    - POST /api/v1/evolution/cluster-mining: 触发提问语义聚类挖掘 (>=0.88)
    - GET  /api/v1/evolution/candidates: 获取高频候选 FAQ 列表
    - POST /api/v1/evolution/candidates/{id}/approve: 审核采纳候选 FAQ 并沉淀发布
    - POST /api/v1/evolution/candidates/{id}/reject: 驳回候选 FAQ
    - POST /api/v1/evolution/faqs/publish: 采纳发布 FAQ 并注入 Redis 高速缓存
    - GET  /api/v1/evolution/faqs: 查询标准 FAQ 列表
    - GET  /api/v1/evolution/faqs/{id}: 获取标准 FAQ 详情
    - PATCH /api/v1/evolution/faqs/{id}/status: 启用/停用指定 FAQ
    - POST /api/v1/evolution/faqs/match: 前置极速 FAQ 匹配测试接口 (>=0.92)
    - GET  /api/v1/evolution/knowledge-gaps: 查询知识盲区缺口池

架构定位:
    API 控制器层 / 模块五: 知识自进化与沉淀引擎

作者:
    System Architect (系统架构组) & Backend Team
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.evolution import KnowledgeGap
from app.schemas.common import PaginatedResponse, StandardResponse
from app.schemas.evolution import (
    ClusterMiningRequest,
    FAQCandidateResponse,
    FAQCreate,
    FAQMatchResponse,
    FAQResponse,
    FAQStatusUpdate,
    KnowledgeGapResponse,
)
from app.services.evolution_service import EvolutionService

router = APIRouter()


@router.post("/cluster-mining", response_model=StandardResponse[List[FAQCandidateResponse]])
async def trigger_cluster_mining(
    request: Request,
    payload: Optional[ClusterMiningRequest] = None,
    db: AsyncSession = Depends(get_db),
):
    """手动或定时触发历史提问语义聚类挖掘 (默认余弦相似度 >= 0.88)"""
    trace_id = getattr(request.state, "trace_id", None)
    service = EvolutionService(db)
    sim_th = payload.similarity_threshold if payload else 0.88
    min_sz = payload.min_cluster_size if payload else 2
    queries = payload.queries if payload else None

    candidates = await service.run_query_clustering(
        similarity_threshold=sim_th,
        min_cluster_size=min_sz,
        queries=queries,
    )
    data = [FAQCandidateResponse.model_validate(c) for c in candidates]
    return StandardResponse(
        code=200,
        message="聚类挖掘分析完成",
        data=data,
        trace_id=trace_id,
    )


@router.get("/candidates", response_model=StandardResponse[PaginatedResponse[FAQCandidateResponse]])
async def list_faq_candidates(
    request: Request,
    page: int = Query(1, ge=1, description="当前页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页记录数"),
    status: Optional[str] = Query(None, description="状态筛选: PENDING/ACCEPTED/REJECTED"),
    db: AsyncSession = Depends(get_db),
):
    """查询聚类推荐候选 FAQ 列表"""
    trace_id = getattr(request.state, "trace_id", None)
    service = EvolutionService(db)
    items, total = await service.list_candidates(page=page, page_size=page_size, status=status)
    resp_items = [FAQCandidateResponse.model_validate(i) for i in items]
    return StandardResponse(
        code=200,
        message="查询候选 FAQ 列表成功",
        data=PaginatedResponse(
            items=resp_items,
            total=total,
            page=page,
            page_size=page_size,
        ),
        trace_id=trace_id,
    )


@router.post("/candidates/{candidate_id}/approve", response_model=StandardResponse[FAQResponse])
async def approve_candidate(
    candidate_id: int,
    request: Request,
    answer: Optional[str] = Query(None, description="自定义补充标准回答"),
    category: str = Query("DEFAULT", description="业务知识分类"),
    db: AsyncSession = Depends(get_db),
):
    """采纳候选 FAQ 并沉淀发布至标准库"""
    trace_id = getattr(request.state, "trace_id", None)
    service = EvolutionService(db)
    faq = await service.approve_candidate(candidate_id=candidate_id, answer=answer, category=category)
    return StandardResponse(
        code=200,
        message="候选 FAQ 采纳发布成功",
        data=FAQResponse.model_validate(faq),
        trace_id=trace_id,
    )


@router.post("/candidates/{candidate_id}/reject", response_model=StandardResponse[FAQCandidateResponse])
async def reject_candidate(
    candidate_id: int,
    request: Request,
    reason: Optional[str] = Query(None, description="驳回原因说明"),
    db: AsyncSession = Depends(get_db),
):
    """驳回候选 FAQ"""
    trace_id = getattr(request.state, "trace_id", None)
    service = EvolutionService(db)
    cand = await service.reject_candidate(candidate_id=candidate_id, reason=reason)
    return StandardResponse(
        code=200,
        message="候选 FAQ 已驳回",
        data=FAQCandidateResponse.model_validate(cand),
        trace_id=trace_id,
    )


@router.post("/faqs/publish", response_model=StandardResponse[FAQResponse])
async def publish_faq(
    payload: FAQCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """直接发布 FAQ 并注入 Redis 极速直出缓存"""
    trace_id = getattr(request.state, "trace_id", None)
    service = EvolutionService(db)
    faq = await service.publish_faq(payload)
    return StandardResponse(
        code=200,
        message="FAQ 发布成功",
        data=FAQResponse.model_validate(faq),
        trace_id=trace_id,
    )


@router.get("/faqs", response_model=StandardResponse[PaginatedResponse[FAQResponse]])
async def list_faqs(
    request: Request,
    page: int = Query(1, ge=1, description="当前页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页记录数"),
    category: Optional[str] = Query(None, description="业务知识分类筛选"),
    is_enabled: Optional[bool] = Query(None, description="启停用状态筛选"),
    db: AsyncSession = Depends(get_db),
):
    """查询标准 FAQ 列表"""
    trace_id = getattr(request.state, "trace_id", None)
    service = EvolutionService(db)
    items, total = await service.list_faqs(page=page, page_size=page_size, category=category, is_enabled=is_enabled)
    return StandardResponse(
        code=200,
        message="查询 FAQ 列表成功",
        data=PaginatedResponse(
            items=[FAQResponse.model_validate(f) for f in items],
            total=total,
            page=page,
            page_size=page_size,
        ),
        trace_id=trace_id,
    )


@router.get("/faqs/{faq_id}", response_model=StandardResponse[FAQResponse])
async def get_faq_detail(
    faq_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """获取指定 FAQ 详情"""
    trace_id = getattr(request.state, "trace_id", None)
    service = EvolutionService(db)
    faq = await service.get_faq_by_id(faq_id)
    return StandardResponse(
        code=200,
        message="获取 FAQ 详情成功",
        data=FAQResponse.model_validate(faq),
        trace_id=trace_id,
    )


@router.patch("/faqs/{faq_id}/status", response_model=StandardResponse[FAQResponse])
async def update_faq_status(
    faq_id: int,
    payload: FAQStatusUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """启用或停用指定 FAQ"""
    trace_id = getattr(request.state, "trace_id", None)
    service = EvolutionService(db)
    faq = await service.toggle_faq_status(faq_id, payload.get_is_enabled())
    return StandardResponse(
        code=200,
        message="FAQ 状态更新成功",
        data=FAQResponse.model_validate(faq),
        trace_id=trace_id,
    )


@router.post("/faqs/match", response_model=StandardResponse[FAQMatchResponse])
async def match_faq(
    query: str = Query(..., description="测试匹配提问文本"),
    threshold: float = Query(0.92, ge=0.5, le=1.0, description="相似度阈值"),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """前置极速 FAQ 直出匹配诊断接口 (余弦相似度 >= threshold)"""
    trace_id = getattr(request.state, "trace_id", None) if request else None
    service = EvolutionService(db)
    match_result = await service.match_faq_cache(query=query, threshold=threshold)
    if match_result:
        resp = FAQMatchResponse(
            hit=True,
            faq_id=match_result["faq_id"],
            standard_question=match_result["standard_question"],
            standard_answer=match_result["standard_answer"],
            similarity=match_result["similarity"],
            hit_count=match_result["hit_count"],
        )
    else:
        resp = FAQMatchResponse(hit=False)

    return StandardResponse(
        code=200,
        message="FAQ 缓存检索完成",
        data=resp,
        trace_id=trace_id,
    )


@router.get("/knowledge-gaps", response_model=StandardResponse[PaginatedResponse[KnowledgeGapResponse]])
async def list_knowledge_gaps(
    request: Request,
    page: int = Query(1, ge=1, description="当前页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页记录数"),
    db: AsyncSession = Depends(get_db),
):
    """查询知识盲区与缺口清单"""
    trace_id = getattr(request.state, "trace_id", None)
    count_stmt = select(func.count(KnowledgeGap.id)).where(KnowledgeGap.is_deleted == False)
    total_res = await db.execute(count_stmt)
    total = total_res.scalar() or 0

    stmt = (
        select(KnowledgeGap)
        .where(KnowledgeGap.is_deleted == False)
        .order_by(KnowledgeGap.hit_count.desc(), KnowledgeGap.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    res = await db.execute(stmt)
    items = res.scalars().all()

    return StandardResponse(
        code=200,
        message="查询知识缺口成功",
        data=PaginatedResponse(
            items=[KnowledgeGapResponse.model_validate(g) for g in items],
            total=total,
            page=page,
            page_size=page_size,
        ),
        trace_id=trace_id,
    )


if __name__ == "__main__":
    import asyncio
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from app.core.database import Base
    from app.middlewares.trace_middleware import TraceMiddleware
    from app.providers.embedding import default_embedding_provider

    async def _test_evolution_router():
        print("=== [Self-Test] Starting Evolution Router Self-Test ===")
        test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_maker = async_sessionmaker(bind=test_engine, expire_on_commit=False, autoflush=False)
        async with session_maker() as session:
            test_app = FastAPI()
            test_app.add_middleware(TraceMiddleware)

            async def _override_db():
                yield session

            test_app.dependency_overrides[get_db] = _override_db
            test_app.include_router(router, prefix="/api/v1/evolution")

            # 注册语义相似向量组
            queries = [
                "员工年假如何申请？",
                "年假申请审批流程说明",
                "请问带薪年休假怎么休",
            ]
            default_embedding_provider.register_semantic_group(queries, base_similarity=0.92)

            transport = ASGITransport(app=test_app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                # 1. POST /cluster-mining
                mine_res = await ac.post("/api/v1/evolution/cluster-mining", json={
                    "similarity_threshold": 0.88,
                    "min_cluster_size": 2,
                    "queries": queries,
                })
                assert mine_res.status_code == 200
                mine_data = mine_res.json()["data"]
                assert len(mine_data) >= 1
                cand_id = mine_data[0]["id"]
                print(f"[Self-Test] POST /cluster-mining succeeded: generated candidate ID={cand_id}")

                # 2. GET /candidates
                cands_res = await ac.get("/api/v1/evolution/candidates?page=1&page_size=10&status=PENDING")
                assert cands_res.status_code == 200
                assert cands_res.json()["data"]["total"] >= 1
                print("[Self-Test] GET /candidates verified.")

                # 3. POST /candidates/{id}/approve
                approve_res = await ac.post(f"/api/v1/evolution/candidates/{cand_id}/approve?answer=OA审批通过后生效&category=HR")
                assert approve_res.status_code == 200
                faq_id = approve_res.json()["data"]["id"]
                assert approve_res.json()["data"]["category"] == "HR"
                print(f"[Self-Test] POST /candidates/{cand_id}/approve succeeded: created FAQ ID={faq_id}")

                # 4. POST /faqs/publish
                pub_res = await ac.post("/api/v1/evolution/faqs/publish", json={
                    "standard_question": "加班费如何折算调休？",
                    "standard_answer": "工作日加班按1.5倍折算调休额度。",
                    "category": "HR",
                })
                assert pub_res.status_code == 200
                pub_faq_id = pub_res.json()["data"]["id"]
                print(f"[Self-Test] POST /faqs/publish succeeded: FAQ ID={pub_faq_id}")

                # 5. GET /faqs
                list_res = await ac.get("/api/v1/evolution/faqs?page=1&page_size=10")
                assert list_res.status_code == 200
                assert list_res.json()["data"]["total"] >= 2
                print("[Self-Test] GET /faqs verified.")

                # 6. PATCH /faqs/{id}/status
                status_res = await ac.patch(f"/api/v1/evolution/faqs/{faq_id}/status", json={"is_enabled": False})
                assert status_res.status_code == 200
                assert status_res.json()["data"]["is_enabled"] is False
                print("[Self-Test] PATCH /faqs/{id}/status verified.")

                # 7. POST /faqs/match
                match_res = await ac.post("/api/v1/evolution/faqs/match?query=加班费如何折算调休？&threshold=0.92")
                assert match_res.status_code == 200
                assert match_res.json()["data"]["hit"] is True
                print("[Self-Test] POST /faqs/match verified.")

                # 8. GET /knowledge-gaps
                gap_res = await ac.get("/api/v1/evolution/knowledge-gaps?page=1&page_size=10")
                assert gap_res.status_code == 200
                print("[Self-Test] GET /knowledge-gaps verified.")

        await test_engine.dispose()
        print("=== [Self-Test] All Evolution Router tests PASSED successfully! ===")

    asyncio.run(_test_evolution_router())

