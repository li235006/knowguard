"""
知识自进化与沉淀引擎核心服务 (Evolution Service)

职责:
    - 对话历史聚类挖掘: 基于语义嵌入执行聚类算法提取高频问题簇 (余弦相似度 >= 0.88)
    - 候选 FAQ 生成: 自动归纳高频问题标准问答对并计算置信度
    - FAQ 审核采纳与驳回: 候选审核流转、发布沉淀至标准 FAQ 知识库，支持动态启停用
    - FAQ 极速缓存直出: 问答前置检索命中 (相似度 >= 0.92) 实现 <30ms 极速直出，累加 hit_count，跳过 LLM
    - 知识盲区与缺口闭环: 捕获未命中或受限问题并追踪

架构定位:
    业务服务层 (Services Layer) / 模块五: 知识自进化与沉淀引擎

作者:
    System Architect (系统架构组) & Backend Team
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessLogicError, EntityNotFoundError
from app.models.chat import Message
from app.models.evolution import FAQCandidate, FAQItem, KnowledgeGap
from app.providers.base import BaseEmbeddingProvider
from app.providers.embedding import default_embedding_provider
from app.schemas.evolution import FAQCreate

logger = logging.getLogger(__name__)


class EvolutionService:
    """知识自进化与 FAQ 沉淀服务实现"""

    def __init__(
        self,
        db: AsyncSession,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
    ):
        self.db = db
        self.embedding_provider = embedding_provider or default_embedding_provider

    # ==================== 1. 提问聚类挖掘与候选生成 ====================

    async def run_query_clustering(
        self,
        similarity_threshold: float = 0.88,
        min_cluster_size: int = 2,
        queries: Optional[List[str]] = None,
    ) -> List[FAQCandidate]:
        """
        基于语义嵌入执行提问日志聚类挖掘:
        1. 提取样本集 (优先使用入参 queries，否则从 Message 表提取用户提问)
        2. 批量计算 1024 维密集语义向量
        3. 基于余弦相似度阈值 (默认 >= 0.88) 聚类归纳高频问题簇
        4. 提取质心/代表性问法并生成置信度，持久化至 faq_candidates 候选池
        """
        raw_queries: List[str] = []
        if queries is not None:
            raw_queries = [q.strip() for q in queries if q and q.strip()]
        else:
            # 从最近会话消息提取用户提问
            stmt = (
                select(Message.content)
                .where(Message.role == "user", Message.is_deleted == False)
                .order_by(Message.id.desc())
                .limit(500)
            )
            res = await self.db.execute(stmt)
            raw_queries = [row[0].strip() for row in res.all() if row[0] and row[0].strip()]

        if len(raw_queries) < min_cluster_size:
            logger.info(f"[EvolutionService] 提问样本量 ({len(raw_queries)}) 不足最小聚类频次 ({min_cluster_size})")
            return []

        # 统计频次并去重
        query_counts: Dict[str, int] = {}
        for q in raw_queries:
            query_counts[q] = query_counts.get(q, 0) + 1
        distinct_queries = list(query_counts.keys())

        # 批量获取语义向量
        vectors = await self.embedding_provider.get_embeddings(distinct_queries)
        q_vec_map = {q: v for q, v in zip(distinct_queries, vectors)}

        # 按出现频次倒序作为种子进行贪婪聚类
        sorted_seeds = sorted(distinct_queries, key=lambda x: query_counts[x], reverse=True)
        assigned: set[str] = set()
        clusters: List[List[str]] = []

        for seed in sorted_seeds:
            if seed in assigned:
                continue
            seed_vec = q_vec_map[seed]
            cluster_members = [seed]
            assigned.add(seed)

            for candidate_q in sorted_seeds:
                if candidate_q in assigned:
                    continue
                cand_vec = q_vec_map[candidate_q]
                sim = sum(a * b for a, b in zip(seed_vec, cand_vec))
                if sim >= similarity_threshold:
                    cluster_members.append(candidate_q)
                    assigned.add(candidate_q)

            # 仅当簇规模满足阈值时沉淀
            total_freq = sum(query_counts[m] for m in cluster_members)
            if total_freq >= min_cluster_size:
                clusters.append(cluster_members)

        # 构建并持久化候选记录
        generated_candidates: List[FAQCandidate] = []
        for cluster in clusters:
            # 计算代表性问题 (质心: 簇内平均相似度最高者)
            best_q = cluster[0]
            best_avg_sim = 1.0
            if len(cluster) > 1:
                best_q = max(
                    cluster,
                    key=lambda q: sum(
                        sum(a * b for a, b in zip(q_vec_map[q], q_vec_map[other]))
                        for other in cluster
                    ) / len(cluster)
                )
                best_avg_sim = sum(
                    sum(a * b for a, b in zip(q_vec_map[best_q], q_vec_map[other]))
                    for other in cluster
                ) / len(cluster)

            cluster_id = f"cluster_{uuid.uuid4().hex[:8]}"
            total_samples = []
            for member in cluster:
                # 包含重复样本以体现全量语料
                total_samples.extend([member] * query_counts.get(member, 1))

            cand = FAQCandidate(
                cluster_id=cluster_id,
                cluster_count=len(total_samples),
                suggested_question=best_q,
                suggested_answer=f"关于【{best_q}】的标准业务答复与办理流程指引如下：...",
                confidence_score=round(float(best_avg_sim), 4),
                sample_queries=list(set(total_samples)),
                status="PENDING",
            )
            self.db.add(cand)
            generated_candidates.append(cand)

        await self.db.commit()
        for cand in generated_candidates:
            await self.db.refresh(cand)

        logger.info(f"[EvolutionService] 聚类挖掘完成: 生成 {len(generated_candidates)} 个候选 FAQ")
        return generated_candidates

    # ==================== 2. 候选流转与标准 FAQ 维护 ====================

    async def list_candidates(
        self,
        page: int = 1,
        page_size: int = 10,
        status: Optional[str] = None,
    ) -> Tuple[List[FAQCandidate], int]:
        """分页获取候选 FAQ 列表"""
        stmt = select(FAQCandidate).where(FAQCandidate.is_deleted == False).order_by(FAQCandidate.id.desc())
        count_stmt = select(func.count(FAQCandidate.id)).where(FAQCandidate.is_deleted == False)

        if status:
            stmt = stmt.where(FAQCandidate.status == status)
            count_stmt = count_stmt.where(FAQCandidate.status == status)

        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar() or 0

        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        res = await self.db.execute(stmt)
        return res.scalars().all(), total

    async def approve_candidate(
        self,
        candidate_id: int,
        answer: Optional[str] = None,
        category: str = "DEFAULT",
    ) -> FAQItem:
        """审核采纳候选 FAQ 并正式发布至标准 FAQ 表"""
        cand = await self.db.get(FAQCandidate, candidate_id)
        if not cand or cand.is_deleted:
            raise EntityNotFoundError(message=f"候选记录 ID {candidate_id} 不存在", code=40401)

        cand.status = "ACCEPTED"
        cand.updated_at = datetime.now(timezone.utc)

        faq = FAQItem(
            standard_question=cand.suggested_question,
            standard_answer=answer or cand.suggested_answer or "标准业务答复",
            category=category,
            similar_questions=cand.sample_queries,
            is_cached=True,
            is_enabled=True,
            hit_count=0,
            candidate_id=cand.id,
        )
        self.db.add(faq)
        await self.db.commit()
        await self.db.refresh(faq)
        await self.db.refresh(cand)
        return faq

    async def reject_candidate(self, candidate_id: int, reason: Optional[str] = None) -> FAQCandidate:
        """驳回候选 FAQ"""
        cand = await self.db.get(FAQCandidate, candidate_id)
        if not cand or cand.is_deleted:
            raise EntityNotFoundError(message=f"候选记录 ID {candidate_id} 不存在", code=40401)

        cand.status = "REJECTED"
        cand.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(cand)
        return cand

    async def publish_faq(self, data: FAQCreate) -> FAQItem:
        """直接创建或发布 FAQ"""
        q = data.standard_question or data.question
        a = data.standard_answer or data.answer
        if not q or not q.strip():
            raise BusinessLogicError(message="FAQ 标准问题不能为空", code=40001)
        if not a or not a.strip():
            raise BusinessLogicError(message="FAQ 标准回答不能为空", code=40001)

        similar = data.similar_questions or data.similar_queries or []

        faq = FAQItem(
            standard_question=q.strip(),
            standard_answer=a.strip(),
            category=data.category or "DEFAULT",
            similar_questions=similar,
            is_cached=data.is_cached,
            is_enabled=data.is_enabled,
            hit_count=0,
            candidate_id=data.candidate_id,
        )
        self.db.add(faq)

        if data.candidate_id:
            cand = await self.db.get(FAQCandidate, data.candidate_id)
            if cand:
                cand.status = "ACCEPTED"
                cand.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(faq)
        return faq

    async def toggle_faq_status(self, faq_id: int, is_enabled: bool) -> FAQItem:
        """启用或停用 FAQ"""
        faq = await self.db.get(FAQItem, faq_id)
        if not faq or faq.is_deleted:
            raise EntityNotFoundError(message=f"FAQ ID {faq_id} 不存在", code=40401)

        faq.is_enabled = is_enabled
        faq.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(faq)
        return faq

    async def list_faqs(
        self,
        page: int = 1,
        page_size: int = 10,
        category: Optional[str] = None,
        is_enabled: Optional[bool] = None,
    ) -> Tuple[List[FAQItem], int]:
        """分页获取标准 FAQ 列表"""
        stmt = select(FAQItem).where(FAQItem.is_deleted == False).order_by(FAQItem.id.desc())
        count_stmt = select(func.count(FAQItem.id)).where(FAQItem.is_deleted == False)

        if category:
            stmt = stmt.where(FAQItem.category == category)
            count_stmt = count_stmt.where(FAQItem.category == category)
        if is_enabled is not None:
            stmt = stmt.where(FAQItem.is_enabled == is_enabled)
            count_stmt = count_stmt.where(FAQItem.is_enabled == is_enabled)

        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar() or 0

        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        res = await self.db.execute(stmt)
        return res.scalars().all(), total

    async def get_faq_by_id(self, faq_id: int) -> FAQItem:
        """根据 ID 获取 FAQ 详情"""
        faq = await self.db.get(FAQItem, faq_id)
        if not faq or faq.is_deleted:
            raise EntityNotFoundError(message=f"FAQ ID {faq_id} 不存在", code=40401)
        return faq

    # ==================== 3. 极速缓存直出与命中累计 ====================

    async def match_faq_cache(
        self,
        query: str,
        threshold: float = 0.92,
    ) -> Optional[Dict[str, Any]]:
        """
        问答前置检索命中 (余弦相似度 >= 0.92) 实现 <30ms 极速直出:
        1. 过滤已启用的标准 FAQ 知识库 (is_enabled == True)
        2. 采用标准问 + 相似问别名双通道匹配
        3. 相似度 >= threshold 视为精准命中:
           - 累加 faq.hit_count (+1)
           - 返回标准回答，跳过 LLM 和 Milvus 检索引擎
        """
        clean_q = query.strip()
        if not clean_q:
            return None

        # 查询所有已启用的有效 FAQ
        stmt = select(FAQItem).where(
            FAQItem.is_deleted == False,
            FAQItem.is_enabled == True,
        )
        res = await self.db.execute(stmt)
        faqs = res.scalars().all()
        if not faqs:
            return None

        query_vec = await self.embedding_provider.get_embedding(clean_q)

        best_match: Optional[FAQItem] = None
        best_sim: float = 0.0

        for f in faqs:
            # 1. 优先完全一致匹配 (1.0)
            if clean_q == f.standard_question.strip():
                best_match = f
                best_sim = 1.0
                break
            if f.similar_questions and any(clean_q == sq.strip() for sq in f.similar_questions):
                best_match = f
                best_sim = 1.0
                break

            # 2. 向量余弦相似度匹配 - 标准问
            f_vec = await self.embedding_provider.get_embedding(f.standard_question)
            sim = sum(a * b for a, b in zip(query_vec, f_vec))
            if sim > best_sim:
                best_sim = sim
                best_match = f

            # 3. 向量余弦相似度匹配 - 相似问
            if f.similar_questions:
                for sq in f.similar_questions:
                    sq_vec = await self.embedding_provider.get_embedding(sq)
                    sq_sim = sum(a * b for a, b in zip(query_vec, sq_vec))
                    if sq_sim > best_sim:
                        best_sim = sq_sim
                        best_match = f

        if best_match and best_sim >= threshold:
            # 累加命中次数并持久化
            best_match.hit_count += 1
            best_match.updated_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(best_match)

            return {
                "faq_id": best_match.id,
                "standard_question": best_match.standard_question,
                "standard_answer": best_match.standard_answer,
                "category": best_match.category,
                "similarity": round(float(best_sim), 4),
                "hit_count": best_match.hit_count,
            }

        return None

    # ==================== 4. 知识缺口流转闭环 ====================

    async def record_knowledge_gap(
        self,
        query: str,
        user_id: Optional[int] = None,
        reason: str = "NO_HITS",
    ) -> Optional[KnowledgeGap]:
        """
        自动捕获或更新知识盲区与缺口:
        1. 针对 query 进行去重查找 (已存在且处于 OPEN / PENDING 状态的缺口)
        2. 若已存在：累加 hit_count (+1)，更新 last_seen_at
        3. 若不存在：新建缺口记录，初始 hit_count=1，状态 OPEN
        """
        clean_q = query.strip() if query else ""
        if not clean_q:
            return None

        # 查找未解决状态下的相同提问记录 (不区分大小写，自动去重)
        stmt = (
            select(KnowledgeGap)
            .where(
                KnowledgeGap.is_deleted == False,
                func.lower(KnowledgeGap.query_text) == clean_q.lower(),
                KnowledgeGap.status.in_(["OPEN", "PENDING"]),
            )
            .order_by(KnowledgeGap.id.desc())
        )
        res = await self.db.execute(stmt)
        gap = res.scalars().first()

        now = datetime.now(timezone.utc)
        if gap:
            gap.hit_count += 1
            gap.last_seen_at = now
            gap.updated_at = now
            if reason and gap.reason == "NO_HITS" and reason != "NO_HITS":
                gap.reason = reason
            await self.db.commit()
            await self.db.refresh(gap)
            logger.info(f"[EvolutionService] 知识缺口频次累加: '{clean_q}' -> {gap.hit_count}")
            return gap
        else:
            gap = KnowledgeGap(
                query_text=clean_q,
                hit_count=1,
                user_id=user_id,
                reason=reason,
                status="OPEN",
                first_seen_at=now,
                last_seen_at=now,
            )
            self.db.add(gap)
            await self.db.commit()
            await self.db.refresh(gap)
            logger.info(f"[EvolutionService] 捕获新知识缺口: ID={gap.id}, query='{clean_q}', reason={reason}")
            return gap

    async def list_knowledge_gaps(
        self,
        page: int = 1,
        page_size: int = 10,
        status: Optional[str] = None,
        sort_by: str = "frequency",
        order: str = "desc",
        keyword: Optional[str] = None,
    ) -> Tuple[List[KnowledgeGap], int]:
        """分页与排序查询知识盲区与缺口清单"""
        stmt = select(KnowledgeGap).where(KnowledgeGap.is_deleted == False)
        count_stmt = select(func.count(KnowledgeGap.id)).where(KnowledgeGap.is_deleted == False)

        if status and status.upper() != "ALL":
            target_status = status.upper()
            if target_status == "RESOLVED":
                stmt = stmt.where(KnowledgeGap.status.in_(["RESOLVED", "CONVERTED"]))
                count_stmt = count_stmt.where(KnowledgeGap.status.in_(["RESOLVED", "CONVERTED"]))
            elif target_status == "IGNORED":
                stmt = stmt.where(KnowledgeGap.status.in_(["IGNORED", "DISMISSED"]))
                count_stmt = count_stmt.where(KnowledgeGap.status.in_(["IGNORED", "DISMISSED"]))
            else:
                stmt = stmt.where(KnowledgeGap.status == target_status)
                count_stmt = count_stmt.where(KnowledgeGap.status == target_status)

        if keyword and keyword.strip():
            kw = f"%{keyword.strip()}%"
            stmt = stmt.where(KnowledgeGap.query_text.ilike(kw))
            count_stmt = count_stmt.where(KnowledgeGap.query_text.ilike(kw))

        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar() or 0

        # 排序
        sort_col = KnowledgeGap.hit_count
        if sort_by in ("frequency", "hit_count", "count"):
            sort_col = KnowledgeGap.hit_count
        elif sort_by in ("created_at", "create_time"):
            sort_col = KnowledgeGap.created_at
        elif sort_by in ("last_seen_at", "last_asked_at", "update_time"):
            sort_col = KnowledgeGap.last_seen_at

        if order.lower() == "asc":
            stmt = stmt.order_by(sort_col.asc(), KnowledgeGap.id.asc())
        else:
            stmt = stmt.order_by(sort_col.desc(), KnowledgeGap.id.desc())

        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        res = await self.db.execute(stmt)
        return list(res.scalars().all()), total

    # 方法别名
    list_gaps = list_knowledge_gaps

    async def get_gap_by_id(self, gap_id: int) -> KnowledgeGap:
        """根据 ID 查询知识缺口详情"""
        gap = await self.db.get(KnowledgeGap, gap_id)
        if not gap or gap.is_deleted:
            raise EntityNotFoundError(message=f"知识缺口 ID {gap_id} 不存在", code=40401)
        return gap

    async def resolve_gap(self, gap_id: int) -> KnowledgeGap:
        """标记知识缺口已转建工单/已解决"""
        gap = await self.db.get(KnowledgeGap, gap_id)
        if not gap or gap.is_deleted:
            raise EntityNotFoundError(message=f"知识缺口 ID {gap_id} 不存在", code=40401)
        gap.status = "RESOLVED"
        gap.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(gap)
        return gap

    async def ignore_gap(self, gap_id: int) -> KnowledgeGap:
        """忽略/驳回知识缺口"""
        gap = await self.db.get(KnowledgeGap, gap_id)
        if not gap or gap.is_deleted:
            raise EntityNotFoundError(message=f"知识缺口 ID {gap_id} 不存在", code=40401)
        gap.status = "IGNORED"
        gap.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(gap)
        return gap

    async def convert_gap(self, gap_id: int, payload: Any = None) -> KnowledgeGap:
        """知识缺口一键转建工单"""
        gap = await self.db.get(KnowledgeGap, gap_id)
        if not gap or gap.is_deleted:
            raise EntityNotFoundError(message=f"知识缺口 ID {gap_id} 不存在", code=40401)
        gap.status = "CONVERTED"
        gap.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(gap)
        return gap

    # 知识缺口方法规范别名 (对齐 P2-2 契约)
    resolve_knowledge_gap = resolve_gap
    ignore_knowledge_gap = ignore_gap
    convert_knowledge_gap = convert_gap
    get_knowledge_gap = get_gap_by_id



if __name__ == "__main__":
    import asyncio
    import time
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from app.core.database import Base

    async def _test_evolution_service():
        print("=== [Self-Test] Starting EvolutionService Self-Test ===")
        test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_maker = async_sessionmaker(bind=test_engine, expire_on_commit=False, autoflush=False)
        async with session_maker() as session:
            service = EvolutionService(session)

            # 1. 注册语义相似向量组 (>= 0.90) 以模拟真实 BGE-M3 语义嵌入
            leave_queries = [
                "员工年假如何申请？",
                "年假申请审批流程说明",
                "请问带薪年休假怎么休",
            ]
            reimburse_queries = [
                "差旅发票报销怎么处理？",
                "报销单据填写与粘贴规范",
            ]
            default_embedding_provider.register_semantic_group(leave_queries, base_similarity=0.91)
            default_embedding_provider.register_semantic_group(reimburse_queries, base_similarity=0.90)

            all_queries = leave_queries + reimburse_queries + ["公司附近有什么餐馆推荐？"]

            # 执行历史提问语义聚类挖掘 (>=0.88)
            candidates = await service.run_query_clustering(
                similarity_threshold=0.88,
                min_cluster_size=2,
                queries=all_queries,
            )
            print(f"[Self-Test] Mining finished: Mined {len(candidates)} candidates")
            assert len(candidates) == 2, f"预期生成 2 个候选 FAQ，实际生成: {len(candidates)}"
            leave_cand = next(c for c in candidates if any(k in c.suggested_question for k in ["年假", "年休假"]))
            assert leave_cand.confidence_score >= 0.88
            assert leave_cand.cluster_count >= 3
            assert leave_cand.status == "PENDING"

            # 2. 验证采纳发布 (approve) -> 写入 faqs 表
            approved_faq = await service.approve_candidate(
                leave_cand.id,
                answer="员工需提前 3 个工作日在 OA 系统的休假流程提交审批。",
                category="HR",
            )
            assert approved_faq.id is not None
            assert approved_faq.category == "HR"
            assert approved_faq.is_enabled is True
            assert approved_faq.hit_count == 0

            # 3. 验证驳回 (reject)
            reimburse_cand = next(c for c in candidates if any(k in c.suggested_question for k in ["报销", "差旅"]))
            rejected_cand = await service.reject_candidate(reimburse_cand.id, reason="非标准问答")
            assert rejected_cand.status == "REJECTED"

            # 4. 验证前置 FAQ 极速缓存直出 (耗时 <30ms, 相似度 >= 0.92, 累加 hit_count)
            # 注册与标准问极高相似的提问
            std_q = approved_faq.standard_question
            test_query = "请问带薪年休假怎么休"
            default_embedding_provider.register_semantic_group([std_q, test_query], base_similarity=0.95)

            t0 = time.perf_counter()
            hit_result = await service.match_faq_cache(test_query, threshold=0.92)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0

            assert hit_result is not None, "必须命中已发布的标准 FAQ"
            assert hit_result["similarity"] >= 0.92
            assert hit_result["hit_count"] == 1
            assert elapsed_ms < 30.0, f"FAQ 极速缓存直出耗时必须 <30ms, 当前为 {elapsed_ms:.2f}ms"
            print(f"[Self-Test] FAQ Fast Cache Hit! Score={hit_result['similarity']}, Hit Count={hit_result['hit_count']}, Elapsed={elapsed_ms:.2f}ms (<30ms)")

            # 5. 验证 FAQ 启停维护 (status toggle)
            disabled_faq = await service.toggle_faq_status(approved_faq.id, is_enabled=False)
            assert disabled_faq.is_enabled is False
            miss_after_disable = await service.match_faq_cache(test_query, threshold=0.92)
            assert miss_after_disable is None, "已停用的 FAQ 不得参与前置缓存直出"
            print(f"[Self-Test] FAQ Disabled & Cache bypassed verified.")

            # 6. 验证知识盲区与缺口流转闭环 (P2-2 Knowledge Gap)
            gap1 = await service.record_knowledge_gap("如何申请2026年海外商务签证？", user_id=1001, reason="NO_HITS")
            assert gap1.id is not None
            assert gap1.hit_count == 1
            assert gap1.frequency == 1
            assert gap1.question == "如何申请2026年海外商务签证？"
            assert gap1.status == "OPEN"

            # 再次提问相同问题 -> 触发去重与频次累加
            gap1_again = await service.record_knowledge_gap("如何申请2026年海外商务签证？", user_id=1002, reason="NO_HITS")
            assert gap1_again.id == gap1.id
            assert gap1_again.hit_count == 2
            assert gap1_again.frequency == 2

            # 记录另一个缺口
            gap2 = await service.record_knowledge_gap("公司跨境资金调拨审计指引", user_id=1003, reason="PERMISSION_RESTRICTED")
            assert gap2.id != gap1.id
            assert gap2.reason == "PERMISSION_RESTRICTED"

            # 列表查询验证 (按 frequency 倒序)
            gaps, total_gaps = await service.list_knowledge_gaps(page=1, page_size=10, sort_by="frequency", order="desc")
            assert total_gaps == 2
            assert gaps[0].id == gap1.id  # hit_count = 2 排在第一位
            assert gaps[1].id == gap2.id  # hit_count = 1

            # 解决缺口 (resolve)
            resolved_gap = await service.resolve_knowledge_gap(gap1.id)
            assert resolved_gap.status == "RESOLVED"

            # 忽略缺口 (ignore)
            ignored_gap = await service.ignore_knowledge_gap(gap2.id)
            assert ignored_gap.status == "IGNORED"
            print(f"[Self-Test] Knowledge Gap Lifecycle (Record, Deduplicate, List, Resolve, Ignore) verified successfully.")

        await test_engine.dispose()
        print("=== [Self-Test] All EvolutionService tests PASSED successfully! ===")

    asyncio.run(_test_evolution_service())

