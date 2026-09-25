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

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.guard import get_optional_user
from app.core.database import get_db
from app.core.exceptions import EntityNotFoundError
from app.models.chat import Conversation, Message
from app.schemas.auth import UserContext
from app.schemas.chat import (
    ChatCompletionRequest,
    ConversationCreateRequest,
    ConversationResponse,
    MessageResponse,
)
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
        from app.core.exceptions import AuthenticationError
        raise AuthenticationError(message="未登录或身份凭证已失效，请先登录系统后再发起问答", code=40101)

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


# ------------------------------------------------------------------------------
# 多轮会话与历史消息管理 (P1-3 标准路由契约，基于数据库持久化与用户级隔离)
# ------------------------------------------------------------------------------
@router.get("/conversations", response_model=StandardResponse[List[ConversationResponse]])
async def get_conversations(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的历史会话列表 (支持多租户/用户数据物理隔离)"""
    user_ctx = await get_optional_user(request)
    user_id = user_ctx.user_id if user_ctx else 0

    stmt = (
        select(Conversation)
        .where(Conversation.user_id == user_id, Conversation.is_active == True)
        .order_by(Conversation.updated_at.desc())
    )
    res = await db.execute(stmt)
    convs = res.scalars().all()

    data = [
        ConversationResponse(
            id=c.id,
            title=c.title,
            created_at=c.created_at.strftime("%Y-%m-%d %H:%M:%S") if c.created_at else "刚刚",
            updated_at=c.updated_at.strftime("%Y-%m-%d %H:%M:%S") if c.updated_at else "刚刚",
            message_count=c.message_count or 0,
        )
        for c in convs
    ]
    return StandardResponse(
        code=200,
        message="获取会话列表成功",
        data=data,
    )


@router.post("/conversations", response_model=StandardResponse[ConversationResponse])
async def create_conversation(
    payload: Optional[ConversationCreateRequest] = None,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """创建全新问答会话"""
    user_ctx = await get_optional_user(request) if request else None
    user_id = user_ctx.user_id if user_ctx else 0

    conv_id = f"conv-{uuid.uuid4().hex[:12]}"
    title = payload.title if payload and payload.title else "新建智能问答"
    new_conv = Conversation(
        id=conv_id,
        user_id=user_id,
        title=title,
        message_count=0,
        is_active=True,
    )
    db.add(new_conv)
    await db.commit()
    await db.refresh(new_conv)

    return StandardResponse(
        code=200,
        message="新建会话成功",
        data=ConversationResponse(
            id=new_conv.id,
            title=new_conv.title,
            created_at=new_conv.created_at.strftime("%Y-%m-%d %H:%M:%S") if new_conv.created_at else "刚刚",
            updated_at=new_conv.updated_at.strftime("%Y-%m-%d %H:%M:%S") if new_conv.updated_at else "刚刚",
            message_count=new_conv.message_count or 0,
        ),
    )


@router.get("/conversations/{conversation_id}/messages", response_model=StandardResponse[List[MessageResponse]])
async def get_conversation_messages(
    conversation_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """获取指定会话的历史消息 (严格用户隔离)"""
    user_ctx = await get_optional_user(request)
    user_id = user_ctx.user_id if user_ctx else 0

    conv_stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == user_id,
        Conversation.is_active == True,
    )
    conv_res = await db.execute(conv_stmt)
    conv = conv_res.scalar_one_or_none()
    if not conv:
        raise EntityNotFoundError(message=f"会话 ID={conversation_id} 不存在或无权访问", code=40401)

    msg_stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.id.asc())
    )
    msgs = (await db.execute(msg_stmt)).scalars().all()
    res = [
        MessageResponse(
            id=str(m.id),
            conversation_id=m.conversation_id,
            role=m.role,
            content=m.content,
            citations=m.citations or [],
            is_silent_fallback=m.is_silent_fallback,
            created_at=m.created_at.strftime("%Y-%m-%d %H:%M:%S") if m.created_at else "",
            status=m.status,
        )
        for m in msgs
    ]
    return StandardResponse(
        code=200,
        message="获取会话历史消息成功",
        data=res,
    )


@router.delete("/conversations/{conversation_id}", response_model=StandardResponse[dict])
async def delete_conversation(
    conversation_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """软删除指定会话 (严格用户隔离与 is_active=False 标记)"""
    user_ctx = await get_optional_user(request)
    user_id = user_ctx.user_id if user_ctx else 0

    conv_stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == user_id,
        Conversation.is_active == True,
    )
    conv_res = await db.execute(conv_stmt)
    conv = conv_res.scalar_one_or_none()
    if not conv:
        raise EntityNotFoundError(message=f"会话 ID={conversation_id} 不存在或无权删除", code=40401)

    conv.is_active = False
    await db.commit()

    return StandardResponse(
        code=200,
        message="会话删除成功",
        data={"deleted_id": conversation_id},
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

            # 2. 构造测试用户 Token (张三 & 李四)
            token_zs = create_access_token({
                "sub": "10086",
                "user_id": 10086,
                "employee_id": "10086",
                "username": "zhangsan",
                "real_name": "张三",
                "dept_id": 2,
                "role_ids": [3],
                "is_superuser": False,
            })
            token_ls = create_access_token({
                "sub": "10087",
                "user_id": 10087,
                "employee_id": "10087",
                "username": "lisi",
                "real_name": "李四",
                "dept_id": 3,
                "role_ids": [2],
                "is_superuser": False,
            })

            # 3. 测试 POST /api/v1/chat/conversations
            create_res = await client.post(
                "/api/v1/chat/conversations",
                json={"title": "张三的差旅咨询"},
                headers={"Authorization": f"Bearer {token_zs}"},
            )
            assert create_res.status_code == 200
            zs_conv_id = create_res.json()["data"]["id"]
            print(f"[Self-Test] POST /conversations created: {zs_conv_id}")

            # 4. 测试 POST /api/v1/chat/completions 原生 SSE 响应并自动落库
            post_payload = {"query": "出差住宿报销标准是多少？", "conversation_id": zs_conv_id}
            res = await client.post(
                "/api/v1/chat/completions",
                json=post_payload,
                headers={"Authorization": f"Bearer {token_zs}", "Accept": "text/event-stream"},
            )
            assert res.status_code == 200
            assert "text/event-stream" in res.headers.get("Content-Type", "")
            sse_content = res.text
            assert "event: citation" in sse_content, "SSE 返回中必须包含 citation 事件"
            assert "event: text_delta" in sse_content, "SSE 返回中必须包含 text_delta 事件"
            assert "event: done" in sse_content, "SSE 返回中必须包含 done 事件"
            assert "出差管理守则.pdf" in sse_content
            print("[Self-Test] POST /api/v1/chat/completions SSE stream verified successfully")

            # 5. 测试 GET /api/v1/chat/conversations/{id}/messages 校验落库与用户隔离
            msg_res = await client.get(
                f"/api/v1/chat/conversations/{zs_conv_id}/messages",
                headers={"Authorization": f"Bearer {token_zs}"},
            )
            assert msg_res.status_code == 200
            msgs = msg_res.json()["data"]
            assert len(msgs) == 2, f"应该落库 2 条消息，实际: {len(msgs)}"
            assert msgs[0]["role"] == "user"
            assert msgs[1]["role"] == "assistant"
            print(f"[Self-Test] GET /conversations/{{id}}/messages verified: {len(msgs)} messages persisted")

            # 6. 验证跨用户数据隔离: 李四访问张三会话返回 404
            ls_get = await client.get(
                f"/api/v1/chat/conversations/{zs_conv_id}/messages",
                headers={"Authorization": f"Bearer {token_ls}"},
            )
            assert ls_get.status_code == 404
            assert ls_get.json()["code"] == 40401
            print("[Self-Test] Cross-user isolation verified: Lisi cannot access Zhangsan's conversation (404)")

            # 7. 测试 DELETE /api/v1/chat/conversations/{id} 软删除
            del_res = await client.delete(
                f"/api/v1/chat/conversations/{zs_conv_id}",
                headers={"Authorization": f"Bearer {token_zs}"},
            )
            assert del_res.status_code == 200
            assert del_res.json()["data"]["deleted_id"] == zs_conv_id

            check_del = await client.get(
                f"/api/v1/chat/conversations/{zs_conv_id}/messages",
                headers={"Authorization": f"Bearer {token_zs}"},
            )
            assert check_del.status_code == 404
            print("[Self-Test] DELETE /conversations/{id} soft-delete verified successfully")

            # 8. 测试 GET /api/v1/chat/suggestions
            sug_res = await client.get("/api/v1/chat/suggestions")
            assert sug_res.status_code == 200
            assert len(sug_res.json()["data"]) >= 3
            print(f"[Self-Test] GET /suggestions verified: {len(sug_res.json()['data'])} questions returned")

        test_app.dependency_overrides.clear()
        await test_engine.dispose()
        print("=== [Self-Test] All Chat Router tests PASSED successfully! ===")

    asyncio.run(_test_chat_router())

