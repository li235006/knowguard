"""
AI 智能问答与工作台流式交互控制器 (Chat Router)

接口清单:
    - POST /api/v1/chat/completions: 核心 SSE 打字机流式问答网关 (text/event-stream)
    - GET  /api/v1/chat/suggestions: 获取智能联想推荐提问

安全时序与事件流规范:
    1. Milvus 初筛 ➔ Guard 剥离 ➔ MySQL 提取 ➔ BGE-Reranker ➔ 安全 Prompt ➔ Qwen-Plus 流式输出
    2. SSE 事件帧: text_delta, citation, warning, done
    3. 越权静默回退: SilentFallback

架构定位:
    API 控制器层 / 模块四: AI 鉴权问答与智能工作台

作者:
    System Architect (系统架构组) & Backend Team
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from typing import List, Optional
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.guard import get_optional_user
from app.core.database import get_db
from app.schemas.auth import UserContext
from app.schemas.chat import ChatCompletionRequest
from app.schemas.common import StandardResponse
from app.services.rag_service import RAGService

router = APIRouter()


@router.post("/completions")
async def chat_completions(
    payload: ChatCompletionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    核心 AI 鉴权智能问答 SSE 原生流式网关 (text/event-stream)
    - 严格遵循 4D 安全时序过滤
    - 标准 SSE 事件帧: text_delta, citation, warning, done
    - 越权静默回退: SilentFallback 高情商兜底
    """
    user_ctx = await get_optional_user(request)
    if not user_ctx:
        user_ctx = UserContext(
            user_id=0,
            employee_id="anonymous",
            username="anonymous",
            real_name="匿名员工",
            is_superuser=False,
        )

    trace_id = getattr(request.state, "trace_id", None) or request.headers.get("X-Trace-Id")

    rag_service = RAGService(db=db)
    stream_generator = rag_service.chat_stream(
        user_context=user_ctx,
        query=payload.query,
        conversation_id=payload.conversation_id,
        trace_id=trace_id,
    )

    response_headers = {
        "Content-Type": "text/event-stream; charset=utf-8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    if trace_id:
        response_headers["X-Trace-Id"] = trace_id

    return StreamingResponse(
        stream_generator,
        media_type="text/event-stream",
        headers=response_headers,
    )


@router.get("/suggestions", response_model=StandardResponse[List[str]])
async def get_suggestions():
    """获取智能联想推荐提问"""
    suggestions = [
        "国内差旅报销标准上限是多少？",
        "研发中心 Git 分支合并规范是什么？",
        "企业知识库 4D-RBAC 动态权限如何配置？",
        "如何申请补充知识资产缺口？",
    ]
    return StandardResponse(
        code=200,
        message="获取推荐提问成功",
        data=suggestions,
    )


# ==============================================================================
# 底嵌自测闭环脚本 (Self-Test Execution Block)
# ==============================================================================
if __name__ == "__main__":
    import asyncio
    from httpx import ASGITransport, AsyncClient
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import StaticPool
    from app.core.database import Base
    from app.core.milvus import milvus_service
    from app.core.security import create_access_token
    from app.models.knowledge import KnowledgeChunk, KnowledgeUnit
    from app.schemas.guard import PermissionPolicyConfig
    from app.services.guard_service import GuardService
    from main import create_app

    print("=== [Self-Test] Starting Chat Router Self-Test ===")

    async def _test_chat_router():
        test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool, echo=False)
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(bind=test_engine, expire_on_commit=False)

        async def _override_get_db():
            async with session_factory() as session:
                yield session

        test_app = create_app()
        test_app.dependency_overrides[get_db] = _override_get_db

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. 准备测试数据
            async with session_factory() as session:
                doc = KnowledgeUnit(title="出差管理守则.pdf", file_type="pdf", status="INDEXED")
                session.add(doc)
                await session.commit()
                await session.refresh(doc)

                chunk = KnowledgeChunk(
                    document_id=doc.id,
                    chunk_index=0,
                    content="公司员工国内差旅住宿费报销上限为每天500元人民币。",
                    status="indexed",
                    has_vector=True,
                )
                session.add(chunk)
                await session.commit()
                await session.refresh(chunk)

                milvus_service.insert_chunks([
                    {"chunk_id": chunk.id, "document_id": doc.id, "embedding": [0.05] * 1024}
                ])

                guard = GuardService(db=session)
                await guard.update_unit_policy(doc.id, PermissionPolicyConfig(is_public=True))

            # 2. 构造测试用户 Token
            token = create_access_token({
                "sub": "10086",
                "user_id": 10086,
                "employee_id": "10086",
                "username": "zhangsan",
                "real_name": "张三",
                "dept_id": 2,
                "role_ids": [3],
                "is_superuser": False,
            })

            # 3. 测试 POST /api/v1/chat/completions 原生 SSE 响应
            post_payload = {"query": "出差住宿报销标准是多少？", "conversation_id": "conv-test-001"}
            res = await client.post(
                "/api/v1/chat/completions",
                json=post_payload,
                headers={"Authorization": f"Bearer {token}", "Accept": "text/event-stream"},
            )
            assert res.status_code == 200
            assert "text/event-stream" in res.headers.get("Content-Type", "")
            sse_content = res.text
            assert "event: citation" in sse_content, "SSE 返回中必须包含 citation 事件"
            assert "event: text_delta" in sse_content, "SSE 返回中必须包含 text_delta 事件"
            assert "event: done" in sse_content, "SSE 返回中必须包含 done 事件"
            assert "出差管理守则.pdf" in sse_content
            print("[Self-Test] POST /api/v1/chat/completions SSE stream verified successfully")

            # 4. 测试 GET /api/v1/chat/suggestions
            sug_res = await client.get("/api/v1/chat/suggestions")
            assert sug_res.status_code == 200
            assert len(sug_res.json()["data"]) >= 3
            print(f"[Self-Test] GET /suggestions verified: {len(sug_res.json()['data'])} questions returned")

        test_app.dependency_overrides.clear()
        await test_engine.dispose()
        print("=== [Self-Test] All Chat Router tests PASSED successfully! ===")

    asyncio.run(_test_chat_router())
