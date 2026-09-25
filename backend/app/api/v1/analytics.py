"""
运营监控、ECharts 图表大盘与审计流水控制器 (Analytics Router)

接口清单:
    - GET /api/v1/analytics/dashboard-summary: 核心 5 大 KPI 卡片汇总 (PV/UV/切片总量/已发布FAQ/待处理缺口)
    - GET /api/v1/analytics/trends: 近 7 天 Token 消耗与响应延时趋势数据 (适配 ECharts)
    - GET /api/v1/analytics/top-rankings: 高频提问 TOP 5 与知识引用热度 TOP 5 榜单
    - GET /api/v1/analytics/audit-logs: 问答全链路安全审计日志分页查询
    - GET /api/v1/analytics/audit-logs/{id}: 审计流水详情
    - GET /api/v1/analytics/audit-logs/{id}/evidence-chain: 拦截证据链穿透下钻分析
    - POST /api/v1/analytics/audit-logs: 安全审计流水手工/系统打点写入

架构定位:
    API 控制器层 / 模块六: 运营监控与审计大盘

作者:
    System Architect (系统架构组) & Backend Team
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.analytics import (
    AuditLogResponse,
    DashboardSummaryResponse,
    EvidenceChainDetailResponse,
    LatencyBucketResponse,
    TopRankingsResponse,
    TrendPoint,
)
from app.schemas.common import PaginatedResponse, StandardResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/dashboard-summary", response_model=StandardResponse[DashboardSummaryResponse])
async def get_dashboard_summary(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """获取运营大盘 5 大核心 KPI 统计汇总卡片"""
    trace_id = getattr(request.state, "trace_id", None)
    service = AnalyticsService(db)
    summary_data = await service.get_dashboard_summary()
    return StandardResponse(
        code=200,
        message="获取大盘核心KPI统计成功",
        data=DashboardSummaryResponse.model_validate(summary_data),
        trace_id=trace_id,
    )


@router.get("/trends", response_model=StandardResponse[List[TrendPoint]])
async def get_trends(
    request: Request,
    days: int = Query(7, ge=1, le=90, description="统计天数 (默认近7天)"),
    db: AsyncSession = Depends(get_db),
):
    """获取近 N 天 Token 消耗与响应延时趋势数据 (适配 ECharts)"""
    trace_id = getattr(request.state, "trace_id", None)
    service = AnalyticsService(db)
    trend_items = await service.get_token_latency_trends(days=days)
    return StandardResponse(
        code=200,
        message="获取大盘趋势走势成功",
        data=[TrendPoint.model_validate(t) for t in trend_items],
        trace_id=trace_id,
    )


@router.get("/latency-distribution", response_model=StandardResponse[List[LatencyBucketResponse]])
async def get_latency_distribution(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """获取端到端响应耗时区间分布统计 (适配 ECharts/前端柱状图)"""
    trace_id = getattr(request.state, "trace_id", None)
    service = AnalyticsService(db)
    dist_items = await service.get_latency_distribution()
    return StandardResponse(
        code=200,
        message="获取端到端响应耗时分布成功",
        data=[LatencyBucketResponse.model_validate(d) for d in dist_items],
        trace_id=trace_id,
    )


@router.get("/top-rankings", response_model=StandardResponse[TopRankingsResponse])
async def get_top_rankings(
    request: Request,
    limit: int = Query(5, ge=1, le=50, description="榜单展示条数 (默认TOP 5)"),
    db: AsyncSession = Depends(get_db),
):
    """获取高频提问 TOP 5 与热门知识引用 TOP 5 双维度榜单"""
    trace_id = getattr(request.state, "trace_id", None)
    service = AnalyticsService(db)
    rankings = await service.get_top_rankings(limit=limit)
    return StandardResponse(
        code=200,
        message="获取大盘榜单成功",
        data=TopRankingsResponse.model_validate(rankings),
        trace_id=trace_id,
    )


@router.get("/audit-logs", response_model=StandardResponse[PaginatedResponse[AuditLogResponse]])
async def list_audit_logs(
    request: Request,
    page: int = Query(1, ge=1, description="当前页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页记录数"),
    keyword: Optional[str] = Query(None, description="搜索关键词 (提问内容/员工账号)"),
    is_blocked: Optional[bool] = Query(None, description="是否拦截/受限过滤"),
    trace_id: Optional[str] = Query(None, description="按链路追踪号 X-Trace-Id 过滤"),
    db: AsyncSession = Depends(get_db),
):
    """分页查询全链路安全审计流水明细"""
    req_trace_id = getattr(request.state, "trace_id", None)
    service = AnalyticsService(db)
    items, total = await service.list_audit_logs(
        page=page,
        page_size=page_size,
        keyword=keyword,
        is_blocked=is_blocked,
        trace_id=trace_id,
    )
    return StandardResponse(
        code=200,
        message="查询安全审计流水成功",
        data=PaginatedResponse(
            items=[AuditLogResponse.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
        ),
        trace_id=req_trace_id,
    )


@router.get("/audit-logs/{identifier}", response_model=StandardResponse[AuditLogResponse])
async def get_audit_log_detail(
    identifier: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """获取单条审计流水明细 (支持主键 ID 或 X-Trace-Id)"""
    trace_id = getattr(request.state, "trace_id", None)
    service = AnalyticsService(db)
    log_item = await service.get_audit_log(identifier)
    return StandardResponse(
        code=200,
        message="获取审计流水详情成功",
        data=AuditLogResponse.model_validate(log_item),
        trace_id=trace_id,
    )


@router.get("/audit-logs/{identifier}/evidence-chain", response_model=StandardResponse[EvidenceChainDetailResponse])
async def get_audit_evidence_chain(
    identifier: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """拦截证据链穿透下钻分析 (召回切片/放行切片/受限隔离切片明细)"""
    trace_id = getattr(request.state, "trace_id", None)
    service = AnalyticsService(db)
    chain_data = await service.get_evidence_chain(identifier)
    return StandardResponse(
        code=200,
        message="获取拦截证据链明细成功",
        data=EvidenceChainDetailResponse.model_validate(chain_data),
        trace_id=trace_id,
    )


@router.post("/audit-logs", response_model=StandardResponse[AuditLogResponse])
async def create_audit_log(
    payload: Dict[str, Any],
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """手工或系统打点写入全链路安全审计日志"""
    trace_id = getattr(request.state, "trace_id", None)
    if "trace_id" not in payload and trace_id:
        payload["trace_id"] = trace_id
    service = AnalyticsService(db)
    created_log = await service.record_audit_log(payload)
    return StandardResponse(
        code=200,
        message="安全审计日志写入成功",
        data=AuditLogResponse.model_validate(created_log),
        trace_id=trace_id,
    )


if __name__ == "__main__":
    import asyncio
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from app.core.database import Base
    from app.middlewares.trace_middleware import TraceMiddleware

    async def _test_analytics_router():
        print("=== [Self-Test] Starting Analytics Router Self-Test ===")
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
            test_app.include_router(router, prefix="/api/v1/analytics")

            transport = ASGITransport(app=test_app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                # 1. 写入安全审计流水 POST /audit-logs
                audit_post = await ac.post("/api/v1/analytics/audit-logs", json={
                    "trace_id": "tr-test-audit-post-01",
                    "user_id": 10086,
                    "username": "张三",
                    "user_dept": "研发部",
                    "query": "高管薪资方案与考核明细",
                    "recalled_chunk_ids": [11, 12],
                    "allowed_chunk_ids": [],
                    "restricted_chunk_ids": [11, 12],
                    "is_blocked": True,
                    "block_reason": "4D权限策略限制",
                    "total_tokens": 120,
                    "latency_ms": 95.0,
                })
                assert audit_post.status_code == 200
                post_data = audit_post.json()["data"]
                log_id = post_data["id"]
                assert post_data["trace_id"] == "tr-test-audit-post-01"
                assert post_data["is_blocked"] is True
                print(f"[Self-Test] 1. POST /audit-logs verified: log_id={log_id}")

                # 2. GET /dashboard-summary
                summary_res = await ac.get("/api/v1/analytics/dashboard-summary")
                assert summary_res.status_code == 200
                sum_data = summary_res.json()["data"]
                assert sum_data["pv"] >= 1
                assert sum_data["uv"] >= 1
                print(f"[Self-Test] 2. GET /dashboard-summary verified: PV={sum_data['pv']}, UV={sum_data['uv']}")

                # 3. GET /trends
                trends_res = await ac.get("/api/v1/analytics/trends?days=7")
                assert trends_res.status_code == 200
                trends_data = trends_res.json()["data"]
                assert len(trends_data) == 7
                print(f"[Self-Test] 3. GET /trends verified: 7 days points received.")

                # 4. GET /top-rankings
                rankings_res = await ac.get("/api/v1/analytics/top-rankings?limit=5")
                assert rankings_res.status_code == 200
                rank_data = rankings_res.json()["data"]
                assert "top_queries" in rank_data
                assert "top_knowledge" in rank_data
                print(f"[Self-Test] 4. GET /top-rankings verified.")

                # 5. GET /audit-logs
                logs_res = await ac.get("/api/v1/analytics/audit-logs?page=1&page_size=10&is_blocked=true")
                assert logs_res.status_code == 200
                logs_data = logs_res.json()["data"]
                assert logs_data["total"] >= 1
                print(f"[Self-Test] 5. GET /audit-logs verified: total={logs_data['total']}")

                # 6. GET /audit-logs/{id}
                detail_res = await ac.get(f"/api/v1/analytics/audit-logs/{log_id}")
                assert detail_res.status_code == 200
                assert detail_res.json()["data"]["id"] == log_id
                print(f"[Self-Test] 6. GET /audit-logs/{log_id} verified.")

                # 7. GET /audit-logs/{id}/evidence-chain
                chain_res = await ac.get(f"/api/v1/analytics/audit-logs/{log_id}/evidence-chain")
                assert chain_res.status_code == 200
                chain_data = chain_res.json()["data"]
                assert chain_data["trace_id"] == "tr-test-audit-post-01"
                assert chain_data["decision"]["is_blocked"] is True
                print("[Self-Test] 7. GET /audit-logs/{id}/evidence-chain verified.")

        await test_engine.dispose()
        print("=== [Self-Test] All Analytics Router tests PASSED successfully! ===")

    asyncio.run(_test_analytics_router())
