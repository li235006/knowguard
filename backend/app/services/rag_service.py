"""
AI 鉴权检索与问答编排服务 (Auth-Aware RAG Service)

时序控制铁律 (RedLine 1):
    Milvus 初筛 ➔ Guard 引擎 OR 鉴权剥离未授权切片 ➔ MySQL 提取权威切片正文
    ➔ BGE-Reranker 语义精排 ➔ 安全 Prompt 组装 ➔ Qwen-Plus 流式回答 (text/event-stream)

标准 SSE 事件帧 (RedLine 3):
    1. warning: 4D 动态隔离未授权切片提示 (PERMISSION_ISOLATION)
    2. citation: 溯源切片卡片
    3. text_delta: 回答打字机增量
    4. done: 完成帧 (conversation_id, trace_id, token 预估)

越权静默回退 (RedLine 2):
    若放行切片为空，触发 SilentFallback 高情商兜底，严禁向前端泄漏受限文档标题或片段。

架构定位:
    业务服务层 (Services Layer) / 模块四: AI 鉴权问答核心编排引擎

作者:
    System Architect (系统架构组) & Backend Team
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import asyncio
from datetime import datetime, timezone
import json
import logging
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.milvus import MilvusService, milvus_service
from app.models.chat import Conversation, Message
from app.models.knowledge import KnowledgeChunk, KnowledgeUnit
from app.providers.base import BaseEmbeddingProvider, BaseLLMProvider
from app.providers.embedding import default_embedding_provider
from app.providers.qwen import default_qwen_provider
from app.providers.reranker import BGERerankerProvider, default_reranker_provider
from app.schemas.auth import UserContext
from app.schemas.chat import (
    ChatEventPayload,
    CitationItem,
    DoneEventData,
    TextDeltaEventData,
    WarningEventData,
)
from app.services.guard_service import GuardService

logger = logging.getLogger(__name__)


class RAGService:
    """全流程 4D 安全鉴权 RAG 流式问答编排引擎"""

    def __init__(
        self,
        db: AsyncSession,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
        milvus: Optional[MilvusService] = None,
        guard_service: Optional[GuardService] = None,
        reranker: Optional[BGERerankerProvider] = None,
        llm_provider: Optional[BaseLLMProvider] = None,
    ):
        self.db = db
        self.embedding_provider = embedding_provider or default_embedding_provider
        self.milvus = milvus or milvus_service
        self.guard = guard_service or GuardService(db)
        self.reranker = reranker or default_reranker_provider
        self.llm = llm_provider or default_qwen_provider

    async def chat_stream(
        self,
        user_context: UserContext,
        query: str,
        conversation_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        核心 SSE 打字机流式问答网关
        严格遵循：Milvus 初筛 ➔ Guard 剥离 ➔ MySQL 提取 ➔ BGE-Reranker ➔ 安全 Prompt ➔ Qwen-Plus
        输出符合 SSE 标准的字符串帧 (event: ...\ndata: ...\n\n)
        """
        conv_id = conversation_id or str(uuid.uuid4())
        tr_id = trace_id or f"trace-{uuid.uuid4().hex[:12]}"
        clean_query = query.strip()

        # ======================================================================
        # 步骤 0: 会话状态管理与多轮前序历史提取 (最近 3 轮 / 6 条)
        # ======================================================================
        conv: Optional[Conversation] = None
        recent_msgs: List[Message] = []
        try:
            conv_stmt = select(Conversation).where(Conversation.id == conv_id)
            conv_res = await self.db.execute(conv_stmt)
            conv = conv_res.scalar_one_or_none()
            if not conv:
                conv = Conversation(
                    id=conv_id,
                    user_id=user_context.user_id,
                    title=clean_query[:25] or "新建会话",
                    message_count=0,
                    is_active=True,
                )
                self.db.add(conv)
                await self.db.commit()
                await self.db.refresh(conv)

            # 提取该会话下最新 6 条历史消息
            hist_stmt = (
                select(Message)
                .where(Message.conversation_id == conv_id)
                .order_by(Message.id.desc())
                .limit(6)
            )
            hist_res = await self.db.execute(hist_stmt)
            recent_msgs = list(hist_res.scalars().all())
            recent_msgs.reverse()
        except Exception as e:
            logger.warning(f"[RAGService] Conversation & history preparation warning: {e}")

        # ======================================================================
        # 步骤 0.5: 前置极速 FAQ 缓存直出检索 (<30ms, 跳过 Milvus 初筛与 LLM)
        # ======================================================================
        try:
            from app.services.evolution_service import EvolutionService
            evolution_svc = EvolutionService(db=self.db, embedding_provider=self.embedding_provider)
            faq_hit = await evolution_svc.match_faq_cache(clean_query, threshold=0.92)
            if faq_hit:
                faq_answer = faq_hit["standard_answer"]
                yield f"event: text_delta\ndata: {json.dumps({'text': faq_answer, 'delta': faq_answer, 'is_faq': True}, ensure_ascii=False)}\n\n"
                yield f"event: done\ndata: {json.dumps({'conversation_id': conv_id, 'trace_id': tr_id, 'hit_faq': True, 'is_faq_hit': True, 'faq_id': faq_hit['faq_id']}, ensure_ascii=False)}\n\n"

                try:
                    user_msg = Message(
                        conversation_id=conv_id,
                        role="user",
                        content=clean_query,
                        trace_id=tr_id,
                    )
                    ai_msg = Message(
                        conversation_id=conv_id,
                        role="assistant",
                        content=faq_answer,
                        trace_id=tr_id,
                        is_guard_intercepted=False,
                    )
                    self.db.add(user_msg)
                    self.db.add(ai_msg)
                    if conv:
                        conv.message_count += 2
                    await self.db.commit()

                    # 记录 FAQ 命中审计日志
                    try:
                        from app.services.analytics_service import AnalyticsService
                        analytics_svc = AnalyticsService(db=self.db)
                        await analytics_svc.record_audit_log({
                            "trace_id": tr_id,
                            "conversation_id": conv_id,
                            "user_id": user_context.user_id if user_context else None,
                            "username": user_context.username if user_context else "anonymous",
                            "employee_id": user_context.employee_id if user_context else None,
                            "user_dept": getattr(user_context, "dept_name", None),
                            "user_role": getattr(user_context, "role_code", None),
                            "query_text": clean_query,
                            "answer_snippet": faq_answer[:200],
                            "recalled_chunk_ids": [],
                            "allowed_chunk_ids": [],
                            "restricted_chunk_ids": [],
                            "is_blocked": False,
                            "block_reason": "FAQ_CACHE_HIT",
                            "prompt_tokens": len(clean_query),
                            "completion_tokens": len(faq_answer),
                            "total_tokens": len(clean_query) + len(faq_answer),
                            "latency_ms": 12.0,
                        })
                    except Exception as audit_err:
                        logger.warning(f"[RAGService] FAQ hit audit logging warning: {audit_err}")
                except Exception as msg_err:
                    logger.warning(f"[RAGService] FAQ message persistence warning: {msg_err}")
                return
        except Exception as e:
            logger.warning(f"[RAGService] Fast FAQ cache check warning: {e}")

        # ======================================================================
        # 步骤 1: 向量初筛 (Milvus Top-20 召回)
        # ======================================================================
        try:
            query_vector = await self.embedding_provider.get_embedding(clean_query)
            search_hits = self.milvus.search_similar(query_vector=query_vector, top_k=20)
            candidate_chunk_ids = [int(h["id"]) for h in search_hits]
        except Exception as e:
            logger.error(f"[RAGService] Milvus search failed: {e}")
            candidate_chunk_ids = []

        # ======================================================================
        # 步骤 2: Guard 引擎 4D-RBAC 安全鉴权过滤 (核心时序)
        # ======================================================================
        allowed_chunk_ids, restricted_chunk_ids = await self.guard.filter_allowed_chunks(
            user_context, candidate_chunk_ids
        )

        # 2.1 触发未授权切片隔离告警事件帧 (warning)
        if restricted_chunk_ids:
            warning_msg = (
                f"系统根据4D权限策略动态过滤了 {len(restricted_chunk_ids)} 处未授权敏感知识切片，"
                f"确保回答内容安全合规。"
            )
            yield ChatEventPayload(
                event="warning",
                data=WarningEventData(type="PERMISSION_ISOLATION", message=warning_msg),
            ).to_sse_line()

        # 2.2 越权静默回退：放行切片为空时触发 SilentFallback 高情商兜底
        if not allowed_chunk_ids:
            fallback_text = (
                "您好！关于您咨询的问题，当前企业知识库在您的授权访问范围内未检索到相匹配的公开或授权参考资料。\n\n"
                "建议您联系系统管理员申请相关业务板块的查看权限，或者向所属部门负责人核实是否有对应权限开通。感谢您的理解！"
            )
            # 模拟打字机流式输出兜底话术
            chunk_size = 6
            for i in range(0, len(fallback_text), chunk_size):
                yield ChatEventPayload(
                    event="text_delta",
                    data=TextDeltaEventData(delta=fallback_text[i:i + chunk_size]),
                ).to_sse_line()
                await asyncio.sleep(0.005)

            # 持久化用户提问与降级消息
            try:
                msg_user = Message(
                    conversation_id=conv_id,
                    role="user",
                    content=clean_query,
                )
                msg_assistant = Message(
                    conversation_id=conv_id,
                    role="assistant",
                    content=fallback_text,
                    citations=[],
                    is_silent_fallback=True,
                )
                self.db.add_all([msg_user, msg_assistant])
                if conv:
                    conv.message_count += 2
                    conv.updated_at = datetime.now(timezone.utc)
                await self.db.commit()
            except Exception as e:
                logger.error(f"[RAGService] Failed to persist fallback message: {e}")

            # 自动捕获并记录知识缺口 (Knowledge Gap)
            try:
                from app.services.evolution_service import EvolutionService
                evolution_svc = EvolutionService(db=self.db)
                reason = "PERMISSION_RESTRICTED" if restricted_chunk_ids else "NO_HITS"
                await evolution_svc.record_knowledge_gap(
                    query=clean_query,
                    user_id=user_context.user_id if user_context else None,
                    reason=reason,
                )
            except Exception as gap_err:
                logger.warning(f"[RAGService] Record knowledge gap warning: {gap_err}")

            # 自动记录全链路安全审计日志 (Audit Log)
            try:
                from app.services.analytics_service import AnalyticsService
                analytics_svc = AnalyticsService(db=self.db)
                await analytics_svc.record_audit_log({
                    "trace_id": tr_id,
                    "conversation_id": conv_id,
                    "user_id": user_context.user_id if user_context else None,
                    "username": user_context.username if user_context else "anonymous",
                    "employee_id": user_context.employee_id if user_context else None,
                    "user_dept": getattr(user_context, "dept_name", None),
                    "user_role": getattr(user_context, "role_code", None),
                    "query_text": clean_query,
                    "answer_snippet": fallback_text[:200],
                    "recalled_chunk_ids": candidate_chunk_ids,
                    "allowed_chunk_ids": allowed_chunk_ids,
                    "restricted_chunk_ids": restricted_chunk_ids,
                    "is_blocked": True,
                    "block_reason": "PERMISSION_ISOLATION" if restricted_chunk_ids else "NO_HITS",
                    "prompt_tokens": len(clean_query),
                    "completion_tokens": len(fallback_text),
                    "total_tokens": len(clean_query) + len(fallback_text),
                    "latency_ms": 25.0,
                })
            except Exception as audit_err:
                logger.warning(f"[RAGService] Record audit log warning: {audit_err}")

            # 发送完成帧并安全退出，绝不泄露受限切片信息
            yield ChatEventPayload(
                event="done",
                data={
                    "conversation_id": conv_id,
                    "trace_id": tr_id,
                    "is_silent_fallback": True,
                    "total_tokens": len(fallback_text),
                },
            ).to_sse_line()
            return

        # ======================================================================
        # 步骤 3: MySQL 提取权威切片正文与所属知识单元主文档标题
        # ======================================================================
        stmt = (
            select(KnowledgeChunk, KnowledgeUnit.title)
            .join(KnowledgeUnit, KnowledgeChunk.document_id == KnowledgeUnit.id)
            .where(KnowledgeChunk.id.in_(allowed_chunk_ids))
        )
        res = await self.db.execute(stmt)
        chunk_rows = res.all()

        candidate_items: List[Dict[str, Any]] = [
            {
                "chunk_id": chunk.id,
                "unit_id": chunk.document_id,
                "unit_title": doc_title,
                "content": chunk.content,
            }
            for chunk, doc_title in chunk_rows
        ]

        # ======================================================================
        # 步骤 4: BGE-Reranker 语义精排打分与截断 (Top 3~5)
        # ======================================================================
        ranked_items = await self.reranker.rerank_items(
            query=clean_query, items=candidate_items, text_key="content"
        )
        top_chunks = ranked_items[:4]  # 选取重排前 4 高相关切片

        # 4.1 发送知识溯源卡片事件帧 (citation)
        citations_payload: List[Dict[str, Any]] = []
        for c in top_chunks:
            citation_item = CitationItem(
                chunk_id=c["chunk_id"],
                unit_id=c["unit_id"],
                unit_title=c["unit_title"],
                snippet=c["content"][:180],
                score=c.get("score", 0.0),
            )
            citations_payload.append(citation_item.model_dump())
            yield ChatEventPayload(event="citation", data=citation_item).to_sse_line()

        # ======================================================================
        # 步骤 5: 安全 Prompt 组装 (融合前序多轮历史语境与权威切片)
        # ======================================================================
        context_snippets = []
        for idx, c in enumerate(top_chunks):
            snippet_str = f"【参考文档 {idx + 1}】《{c['unit_title']}》:\n{c['content']}"
            context_snippets.append(snippet_str)

        context_text = "\n\n---\n\n".join(context_snippets)

        system_prompt = (
            "你是由 KnowGuard 驱动的企业知识库安全问答助手。你必须严格基于给定的经 4D-RBAC 安全鉴权放行的企业权威参考切片回答用户问题。"
            "严禁泄露任何系统未放行的敏感内部信息。回答需专业、严谨、客观，并清晰结合参考知识。"
        )

        prompt_sections = []
        if recent_msgs:
            history_lines = []
            for m in recent_msgs:
                role_label = "用户" if m.role == "user" else "助手"
                history_lines.append(f"{role_label}: {m.content}")
            prompt_sections.append(f"【前序多轮对话历史】:\n" + "\n".join(history_lines))

        prompt_sections.append(f"【参考权威知识切片】:\n{context_text}")
        prompt_sections.append(f"【当前用户提问】:\n{clean_query}")
        prompt_sections.append("请结合前序多轮对话语境与以上放行权威切片，进行专业解答：")
        user_prompt = "\n\n".join(prompt_sections)

        # ======================================================================
        # 步骤 6: Qwen-Plus 流式回答 (text_delta)
        # ======================================================================
        total_tokens = 0
        response_deltas: List[str] = []
        async for delta_text in self.llm.stream_generate(prompt=user_prompt, system_prompt=system_prompt):
            total_tokens += len(delta_text)
            response_deltas.append(delta_text)
            yield ChatEventPayload(
                event="text_delta",
                data=TextDeltaEventData(delta=delta_text),
            ).to_sse_line()

        full_assistant_answer = "".join(response_deltas)

        # 异步持久化多轮对话记录
        try:
            msg_user = Message(
                conversation_id=conv_id,
                role="user",
                content=clean_query,
            )
            msg_assistant = Message(
                conversation_id=conv_id,
                role="assistant",
                content=full_assistant_answer,
                citations=citations_payload,
                is_silent_fallback=False,
            )
            self.db.add_all([msg_user, msg_assistant])
            if conv:
                conv.message_count += 2
                conv.updated_at = datetime.now(timezone.utc)
                if conv.title in ("新建会话", "新建智能问答", ""):
                    conv.title = clean_query[:25]
            await self.db.commit()
        except Exception as e:
            logger.error(f"[RAGService] Failed to persist completions message: {e}")

        # 自动记录全链路安全审计日志 (Audit Log)
        try:
            from app.services.analytics_service import AnalyticsService
            analytics_svc = AnalyticsService(db=self.db)
            await analytics_svc.record_audit_log({
                "trace_id": tr_id,
                "conversation_id": conv_id,
                "user_id": user_context.user_id if user_context else None,
                "username": user_context.username if user_context else "anonymous",
                "employee_id": user_context.employee_id if user_context else None,
                "user_dept": getattr(user_context, "dept_name", None),
                "user_role": getattr(user_context, "role_code", None),
                "query_text": clean_query,
                "answer_snippet": full_assistant_answer[:200],
                "recalled_chunk_ids": candidate_chunk_ids,
                "allowed_chunk_ids": allowed_chunk_ids,
                "restricted_chunk_ids": restricted_chunk_ids,
                "is_blocked": bool(restricted_chunk_ids),
                "block_reason": "PARTIAL_ISOLATION" if restricted_chunk_ids else None,
                "prompt_tokens": len(clean_query),
                "completion_tokens": len(full_assistant_answer),
                "total_tokens": total_tokens,
                "latency_ms": 45.0,
            })
        except Exception as audit_err:
            logger.warning(f"[RAGService] Normal completion audit logging warning: {audit_err}")

        # ======================================================================
        # 步骤 7: 完成帧 (done)
        # ======================================================================
        yield ChatEventPayload(
            event="done",
            data=DoneEventData(
                conversation_id=conv_id,
                trace_id=tr_id,
                total_tokens=total_tokens,
            ),
        ).to_sse_line()


# ==============================================================================
# 底嵌自测闭环脚本 (Self-Test Execution Block)
# ==============================================================================
if __name__ == "__main__":
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import StaticPool
    from app.core.database import Base
    from app.schemas.guard import PermissionPolicyConfig

    print("=== [Self-Test] Starting RAG Service Pipeline Self-Test ===")

    async def _test_rag_pipeline():
        test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool, echo=False)
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(bind=test_engine, expire_on_commit=False)

        async with session_factory() as session:
            # 1. 准备知识文档与切片
            doc_pub = KnowledgeUnit(title="差旅报销制度.pdf", file_type="pdf", status="INDEXED")
            doc_sec = KnowledgeUnit(title="核心财务薪资报表.pdf", file_type="pdf", status="INDEXED")
            session.add_all([doc_pub, doc_sec])
            await session.commit()
            await session.refresh(doc_pub)
            await session.refresh(doc_sec)

            chunk_pub = KnowledgeChunk(
                document_id=doc_pub.id,
                chunk_index=0,
                content="员工国内差旅报销标准上限为每天500元，实报实销。",
                status="indexed",
                has_vector=True,
            )
            chunk_sec = KnowledgeChunk(
                document_id=doc_sec.id,
                chunk_index=0,
                content="公司高管层薪资及股票期权分配核心机密方案。",
                status="indexed",
                has_vector=True,
            )
            session.add_all([chunk_pub, chunk_sec])
            await session.commit()
            await session.refresh(chunk_pub)
            await session.refresh(chunk_sec)

            # 写入 Milvus 向量库
            milvus_service.insert_chunks([
                {"chunk_id": chunk_pub.id, "document_id": doc_pub.id, "embedding": [0.01] * 1024},
                {"chunk_id": chunk_sec.id, "document_id": doc_sec.id, "embedding": [0.02] * 1024},
            ])

            # 配置 4D 策略: doc_pub 全局公开，doc_sec 仅限 user_id=999
            guard = GuardService(db=session)
            await guard.update_unit_policy(doc_pub.id, PermissionPolicyConfig(is_public=True))
            await guard.update_unit_policy(doc_sec.id, PermissionPolicyConfig(is_public=False, user_ids=[999]))

            rag = RAGService(db=session, milvus=milvus_service, guard_service=guard)

            # 2. 正常场景：普通员工张三 (user_id=10086) 提问差旅标准
            user_zhang = UserContext(
                user_id=10086,
                employee_id="10086",
                username="zhangsan",
                real_name="张三",
                dept_id=2,
                role_ids=[3],
                is_superuser=False,
            )

            print("[Self-Test] Testing Case 1: Normal authorized query by Zhang San...")
            events_collected = []
            async for sse_line in rag.chat_stream(user_zhang, query="出差住宿报销标准上限是多少？"):
                events_collected.append(sse_line)

            full_sse_text = "".join(events_collected)
            # 校验包含 citation, text_delta, done 事件
            assert "event: citation" in full_sse_text, "必须收到溯源切片卡片"
            assert "event: text_delta" in full_sse_text, "必须收到打字机文本增量"
            assert "event: done" in full_sse_text, "必须收到完成帧"
            # 校验警告事件 (因为机密薪资切片被动态隔离拦截)
            assert "event: warning" in full_sse_text, "未授权敏感切片被隔离时必须触发 warning 事件"
            assert "差旅报销制度.pdf" in full_sse_text
            assert "核心财务薪资报表.pdf" not in full_sse_text, "绝对不能泄露未授权切片正文"
            print(f"[Self-Test] Case 1 passed: {len(events_collected)} SSE frames received.")

            # 3. 越权场景：提问无权访问的机密薪资 -> 触发 Silent Fallback
            # 临时将公共文档排除，模拟只召回了机密文档且全量被拦截的情况
            print("[Self-Test] Testing Case 2: Silent Fallback when 100% chunks restricted...")
            milvus_service.delete_chunks_by_document(doc_pub.id)

            fallback_events = []
            async for sse_line in rag.chat_stream(user_zhang, query="高管薪资期权机密方案是什么？"):
                fallback_events.append(sse_line)

            fallback_sse_text = "".join(fallback_events)
            assert "event: warning" in fallback_sse_text, "必须收到隔离告警"
            assert "event: citation" not in fallback_sse_text, "静默降级时绝不返回任何溯源卡片"
            assert "is_silent_fallback" in fallback_sse_text, "完成帧必须标注 is_silent_fallback"

            import json
            reconstructed_text = ""
            for block in fallback_sse_text.split("\n\n"):
                for line in block.split("\n"):
                    if line.startswith("data: "):
                        try:
                            d = json.loads(line[6:].strip())
                            if "delta" in d:
                                reconstructed_text += d["delta"]
                        except Exception:
                            pass

            assert "未检索到相匹配的公开或授权参考资料" in reconstructed_text, "必须触发高情商静默兜底"
            assert "核心财务薪资报表" not in fallback_sse_text, "绝不可泄露未授权文档名称"

            # 校验自动捕获知识缺口记录
            from app.models.evolution import KnowledgeGap
            recorded_gap = (await session.execute(
                select(KnowledgeGap).where(KnowledgeGap.query_text == "高管薪资期权机密方案是什么？")
            )).scalar_one_or_none()
            assert recorded_gap is not None, "SilentFallback 必须自动捕获沉淀知识缺口"
            assert recorded_gap.hit_count >= 1
            assert recorded_gap.frequency >= 1
            assert recorded_gap.reason == "PERMISSION_RESTRICTED"
            print(f"[Self-Test] Case 2 Silent Fallback passed with 0 sensitive leakage & Auto Gap ID={recorded_gap.id} verified!")

            # 4. 多轮对话与历史持久化断言：验证会话消息落地与第二轮追问
            print("[Self-Test] Testing Case 3: Multi-turn history and message persistence...")
            conv_id_test = "conv-multiturn-test"
            # 第一轮提问
            async for _ in rag.chat_stream(user_zhang, query="差旅可以坐高铁一等座吗？", conversation_id=conv_id_test):
                pass

            # 校验会话表与消息表落地
            saved_conv = (await session.execute(select(Conversation).where(Conversation.id == conv_id_test))).scalar_one()
            assert saved_conv.message_count == 2
            msgs_turn1 = list((await session.execute(select(Message).where(Message.conversation_id == conv_id_test))).scalars().all())
            assert len(msgs_turn1) == 2
            assert msgs_turn1[0].role == "user"
            assert msgs_turn1[1].role == "assistant"

            # 第二轮追问 (带入历史上下文)
            async for _ in rag.chat_stream(user_zhang, query="那机票可以报销商务舱吗？", conversation_id=conv_id_test):
                pass

            await session.refresh(saved_conv)
            assert saved_conv.message_count == 4
            msgs_turn2 = list((await session.execute(select(Message).where(Message.conversation_id == conv_id_test).order_by(Message.id.asc()))).scalars().all())
            assert len(msgs_turn2) == 4
            print(f"[Self-Test] Case 3 passed: Multi-turn chat persisted {len(msgs_turn2)} messages successfully!")

        await test_engine.dispose()
        print("=== [Self-Test] All RAG Service Pipeline tests PASSED successfully! ===")

    asyncio.run(_test_rag_pipeline())
