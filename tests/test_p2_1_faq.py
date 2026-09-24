"""
KnowGuard 阶段 P2-1 FAQ 自动聚类挖掘与极速缓存直出测试套件 (test_p2_1_faq.py)
严格执行大总管 MVP 极简铁律：单文件高密度覆核 3 大核心黄金断言:
  1. test_01_faq_clustering_and_candidate_generation: 聚类挖掘算法验证，余弦相似度 >= 0.88 生成候选池
  2. test_02_faq_approval_and_publishing_lifecycle: 候选审核采纳/驳回流转，发布至 faqs 表并支持启用/停用
  3. test_03_fast_cache_direct_hit_and_hit_count: 问答前置检索命中 (相似度 >= 0.92) 实现 <30ms 极速缓存直出，累加 hit_count，跳过 LLM
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import json
import time
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evolution import FAQCandidate, FAQItem
from app.providers.embedding import default_embedding_provider
from app.services.evolution_service import EvolutionService


@pytest.fixture(autouse=True)
def clean_custom_embeddings():
    """每次测试前后清理自定义语义向量缓存，保证用例独立纯净"""
    default_embedding_provider.clear_custom_embeddings()
    yield
    default_embedding_provider.clear_custom_embeddings()


@pytest.mark.asyncio
async def test_01_faq_clustering_and_candidate_generation(client: AsyncClient, db_session: AsyncSession):
    """黄金断言 1: 聚类挖掘算法验证，余弦相似度 >= 0.88 生成候选池"""
    service = EvolutionService(db=db_session)

    # 1. 准备聚类语料样本:
    # 簇 1 (休假咨询, 3 条，语义相似度 >= 0.90)
    leave_queries = [
        "员工年假如何申请？",
        "年假申请审批流程说明",
        "请问带薪年休假怎么休",
    ]
    default_embedding_provider.register_semantic_group(leave_queries, base_similarity=0.91)

    # 簇 2 (报销咨询, 2 条，语义相似度 >= 0.90)
    reimburse_queries = [
        "差旅发票报销怎么处理？",
        "报销单据填写与粘贴规范",
    ]
    default_embedding_provider.register_semantic_group(reimburse_queries, base_similarity=0.90)

    # 离群孤立样本 (1 条，频次不足最小簇规模 min_cluster_size=2)
    singleton_query = "公司附近有什么好吃的餐馆推荐？"

    all_queries = leave_queries + reimburse_queries + [singleton_query]

    # 2. 执行聚类挖掘算法 (相似度阈值 0.88, 最小簇规模 2)
    candidates = await service.run_query_clustering(
        similarity_threshold=0.88,
        min_cluster_size=2,
        queries=all_queries,
    )

    # 3. 断言验证候选生成结果
    assert len(candidates) == 2, f"预期生成 2 个候选 FAQ 簇，实际生成: {len(candidates)}"

    cand_map = {c.suggested_question: c for c in candidates}
    # 查找休假簇与报销簇
    leave_cand = next((c for c in candidates if any(lq in c.suggested_question for lq in ["年假", "年休假"])), None)
    reimburse_cand = next((c for c in candidates if any(rq in c.suggested_question for rq in ["报销", "差旅"])), None)

    assert leave_cand is not None, "必须成功挖掘出休假咨询候选 FAQ"
    assert leave_cand.confidence_score >= 0.88, f"置信度必须 >= 0.88，当前为: {leave_cand.confidence_score}"
    assert leave_cand.cluster_count >= 3, f"休假簇频次必须 >= 3，当前为: {leave_cand.cluster_count}"
    assert leave_cand.status == "PENDING", "候选初始状态必须为 PENDING"
    assert len(leave_cand.sample_queries) >= 3

    assert reimburse_cand is not None, "必须成功挖掘出报销咨询候选 FAQ"
    assert reimburse_cand.confidence_score >= 0.88, f"置信度必须 >= 0.88，当前为: {reimburse_cand.confidence_score}"
    assert reimburse_cand.cluster_count >= 2
    assert reimburse_cand.status == "PENDING"

    # 4. 数据库物理持久化验证
    db_candidates = (await db_session.execute(
        select(FAQCandidate).where(FAQCandidate.is_deleted == False)
    )).scalars().all()
    assert len(db_candidates) == 2

    # 5. API 接口检索验证 (GET /api/v1/evolution/candidates)
    api_res = await client.get("/api/v1/evolution/candidates?page=1&page_size=10&status=PENDING")
    assert api_res.status_code == 200
    res_json = api_res.json()
    assert res_json["code"] == 200
    paginated = res_json["data"]
    assert paginated["total"] == 2
    assert len(paginated["items"]) == 2

    print(f"\n✅ [黄金断言 1 通过] 提问语义聚类挖掘成功 (>=0.88)，准确生成 2 个高置信候选 FAQ 且物理入库")


@pytest.mark.asyncio
async def test_02_faq_approval_and_publishing_lifecycle(client: AsyncClient, db_session: AsyncSession):
    """黄金断言 2: 候选审核采纳/驳回流转，发布至 faqs 表并支持启用/停用"""
    service = EvolutionService(db=db_session)

    # 1. 预置两个候选 FAQ
    cand_leave = FAQCandidate(
        cluster_id="cluster_leave_01",
        cluster_count=5,
        suggested_question="员工带薪年假申请规范与流程",
        suggested_answer="员工可在 OA 系统发起年假申请...",
        confidence_score=0.93,
        sample_queries=["年假怎么休", "如何申请带薪年假"],
        status="PENDING",
    )
    cand_other = FAQCandidate(
        cluster_id="cluster_junk_02",
        cluster_count=2,
        suggested_question="今天天气怎么样",
        suggested_answer="请查阅当地天气预报",
        confidence_score=0.89,
        sample_queries=["查天气", "今天冷不冷"],
        status="PENDING",
    )
    db_session.add_all([cand_leave, cand_other])
    await db_session.commit()
    await db_session.refresh(cand_leave)
    await db_session.refresh(cand_other)

    # 2. 驳回无效候选 (POST /api/v1/evolution/candidates/{id}/reject)
    reject_res = await client.post(f"/api/v1/evolution/candidates/{cand_other.id}/reject?reason=闲聊问题非企业知识")
    assert reject_res.status_code == 200
    assert reject_res.json()["data"]["status"] == "REJECTED"

    # 重新加载确认 DB 状态
    await db_session.refresh(cand_other)
    assert cand_other.status == "REJECTED", "被驳回候选状态必须流转为 REJECTED"

    # 3. 采纳候选并发布至标准 FAQ 知识库 (POST /api/v1/evolution/candidates/{id}/approve)
    standard_ans = "员工需提前 3 个工作日在 OA 系统的【休假流程】提交审批，由主管和 HRBP 审批通过后生效。"
    approve_res = await client.post(
        f"/api/v1/evolution/candidates/{cand_leave.id}/approve?answer={standard_ans}&category=HR"
    )
    assert approve_res.status_code == 200
    faq_data = approve_res.json()["data"]
    faq_id = faq_data["id"]
    assert faq_data["standard_question"] == cand_leave.suggested_question
    assert faq_data["standard_answer"] == standard_ans
    assert faq_data["category"] == "HR"
    assert faq_data["is_enabled"] is True
    assert faq_data["hit_count"] == 0

    await db_session.refresh(cand_leave)
    assert cand_leave.status == "ACCEPTED", "已采纳候选状态必须流转为 ACCEPTED"

    # 4. 直接新增发布标准 FAQ (POST /api/v1/evolution/faqs/publish)
    direct_faq_res = await client.post("/api/v1/evolution/faqs/publish", json={
        "standard_question": "企业公积金缴存比例是多少？",
        "standard_answer": "KnowGuard 全员按照最高法定标准 12% 缴纳住房公积金。",
        "category": "BENEFITS",
        "similar_questions": ["公积金交几个点", "住房公积金比例"],
        "is_enabled": True,
        "is_cached": True,
    })
    assert direct_faq_res.status_code == 200
    direct_faq = direct_faq_res.json()["data"]
    direct_faq_id = direct_faq["id"]
    assert direct_faq["standard_question"] == "企业公积金缴存比例是多少？"

    # 5. FAQ 启停用状态切换 (PATCH /api/v1/evolution/faqs/{id}/status)
    # 停用
    disable_res = await client.patch(f"/api/v1/evolution/faqs/{faq_id}/status", json={"is_enabled": False})
    assert disable_res.status_code == 200
    assert disable_res.json()["data"]["is_enabled"] is False

    # 验证列表中停用过滤
    list_disabled = await client.get("/api/v1/evolution/faqs?is_enabled=false")
    assert list_disabled.status_code == 200
    assert any(f["id"] == faq_id for f in list_disabled.json()["data"]["items"])

    # 重新启用
    enable_res = await client.patch(f"/api/v1/evolution/faqs/{faq_id}/status", json={"is_enabled": True})
    assert enable_res.status_code == 200
    assert enable_res.json()["data"]["is_enabled"] is True

    print(f"\n✅ [黄金断言 2 通过] 候选审核采纳/驳回流转、正式发布沉淀与启用/停用状态切换全部验证通过")


@pytest.mark.asyncio
async def test_03_fast_cache_direct_hit_and_hit_count(client: AsyncClient, db_session: AsyncSession):
    """黄金断言 3: 问答前置检索命中 (相似度 >= 0.92) 实现 <30ms 极速缓存直出，累加 hit_count，跳过 LLM"""
    service = EvolutionService(db=db_session)

    # 1. 预置启用状态的标准 FAQ
    std_q = "如何申请企业年假？"
    std_a = "员工登录 OA 系统点击【行政人事】-【请假管理】-【年休假】，填写请假起止时间并提交主管审批。"
    similar_q = "年假申请操作指引"

    # 注册高相似向量 (>= 0.92)
    default_embedding_provider.register_semantic_group([std_q, similar_q, "请问如何申请企业年假？"], base_similarity=0.95)

    faq = FAQItem(
        standard_question=std_q,
        standard_answer=std_a,
        category="HR",
        similar_questions=[similar_q],
        is_cached=True,
        is_enabled=True,
        hit_count=0,
    )
    db_session.add(faq)
    await db_session.commit()
    await db_session.refresh(faq)
    faq_id = faq.id

    # 2. 诊断接口匹配与延时性能核验 (<30ms, 相似度 >= 0.92)
    t0 = time.perf_counter()
    match_res = await client.post(f"/api/v1/evolution/faqs/match?query={std_q}&threshold=0.92")
    latency_ms = (time.perf_counter() - t0) * 1000

    assert match_res.status_code == 200
    match_data = match_res.json()["data"]
    assert match_data["hit"] is True, "余弦相似度 >= 0.92 必须命中 FAQ 缓存"
    assert match_data["faq_id"] == faq_id
    assert match_data["standard_answer"] == std_a
    assert match_data["similarity"] >= 0.92
    assert latency_ms < 30.0, f"FAQ 极速缓存匹配耗时必须 < 30ms，当前耗时: {latency_ms:.2f}ms"

    # 验证 hit_count 累加至 1
    await db_session.refresh(faq)
    assert faq.hit_count == 1, f"初次命中后 hit_count 必须递增至 1，当前为: {faq.hit_count}"

    # 3. 相似别名命中与二次累加
    t1 = time.perf_counter()
    match_res2 = await client.post(f"/api/v1/evolution/faqs/match?query={similar_q}&threshold=0.92")
    latency_ms2 = (time.perf_counter() - t1) * 1000

    assert match_res2.status_code == 200
    assert match_res2.json()["data"]["hit"] is True
    assert latency_ms2 < 30.0

    await db_session.refresh(faq)
    assert faq.hit_count == 2, f"二次命中后 hit_count 必须递增至 2，当前为: {faq.hit_count}"

    # 4. 原生问答网关前置极速直出 (POST /api/v1/chat/completions)
    chat_res = await client.post("/api/v1/chat/completions", json={
        "query": std_q,
    })
    assert chat_res.status_code == 200
    assert "text/event-stream" in chat_res.headers.get("content-type", "")

    # 解析 SSE 数据帧
    sse_body = chat_res.text
    assert "event: text_delta" in sse_body
    assert std_a in sse_body, "SSE 输出流必须直接输出标准 FAQ 回答"
    assert "hit_faq" in sse_body, "done 事件中必须标明 hit_faq: true"
    assert f'"faq_id": {faq_id}' in sse_body or f'"faq_id":{faq_id}' in sse_body

    # 校验问答网关直出再次累加 hit_count 至 3
    await db_session.refresh(faq)
    assert faq.hit_count == 3, f"问答流式直出后 hit_count 必须递增至 3，当前为: {faq.hit_count}"

    # 5. FAQ 停用后不再命中缓存直出，回退普通检索
    faq.is_enabled = False
    await db_session.commit()

    disabled_match = await service.match_faq_cache(query=std_q, threshold=0.92)
    assert disabled_match is None, "已停用的 FAQ 绝对不得命中缓存直出"

    # hit_count 不再增加
    await db_session.refresh(faq)
    assert faq.hit_count == 3

    print(f"\n✅ [黄金断言 3 通过] 问答前置检索命中 (>=0.92) 极速直出耗时 {latency_ms:.2f}ms (<30ms)，hit_count 准确累加至 3，停用后拦截正常")
