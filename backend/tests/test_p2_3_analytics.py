"""
KnowGuard 阶段 P2-3 运营监控大盘与全链路审计测试套件 (test_p2_3_analytics.py)
严格执行大总管 MVP 极简铁律：单文件高密度覆核 3 大核心黄金断言:
  1. test_01_dashboard_summary_kpi_aggregation: 5 大核心 KPI 聚合统计 (PV/UV/切片总量/已发布FAQ/待处理缺口)
  2. test_02_trends_and_top_rankings: 近 7 天 Token/延时趋势数据及高频提问/热门知识 TOP 5 榜单查询
  3. test_03_audit_logs_and_evidence_chain: 全链路安全审计日志分页与拦截证据链下钻 (召回/放行/拦截受限切片明细)
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import ChatAuditLog
from app.models.chat import Conversation, Message
from app.models.evolution import FAQItem, KnowledgeGap
from app.models.knowledge import KnowledgeChunk, KnowledgeUnit
from app.models.user import User


@pytest.mark.asyncio
async def test_01_dashboard_summary_kpi_aggregation(client: AsyncClient, db_session: AsyncSession):
    """
    黄金断言 1: 5 大核心 KPI 聚合统计 (PV/UV/切片总量/已发布FAQ/待处理缺口)
    1. 灌入底层业务多源基础数据:
       - 知识单元与切片: 2 个文档，共 6 个有效切片
       - FAQ 知识沉淀库: 3 条已发布启用的标准 FAQ，1 条已停用的 FAQ
       - 知识盲区缺口池: 4 条 OPEN 状态待处理缺口，2 条 RESOLVED 已解决缺口
       - 用户提问与审计日志: 2 位不同员工发起的 5 条提问交互流水
    2. 调用 GET /api/v1/analytics/dashboard-summary 接口
    3. 断言 5 大核心运营指标精准聚合:
       - pv == 5 (提问总访问量)
       - uv == 2 (独立员工访问数)
       - chunks_count / total_chunks == 6 (知识切片总量)
       - published_faqs / faqs_count == 3 (已发布生效的 FAQ 总数)
       - open_gaps / pending_gaps == 4 (待处理缺口数，已解决缺口准确排除)
    4. 断言辅助计算指标: faq_cache_hit_rate 与 avg_latency_ms 响应正常
    """
    # 1. 构造文档与切片数据 (切片总量 = 6)
    doc1 = KnowledgeUnit(title="员工差旅管理办法2026.pdf", file_type="pdf", status="INDEXED")
    doc2 = KnowledgeUnit(title="信息安全红线保密规程.docx", file_type="docx", status="INDEXED")
    db_session.add_all([doc1, doc2])
    await db_session.commit()
    await db_session.refresh(doc1)
    await db_session.refresh(doc2)

    chunks = [
        KnowledgeChunk(document_id=doc1.id, chunk_index=i, content=f"差旅规程切片内容段落 {i}", status="indexed")
        for i in range(4)
    ] + [
        KnowledgeChunk(document_id=doc2.id, chunk_index=i, content=f"保密红线规程切片内容 {i}", status="indexed")
        for i in range(2)
    ]
    db_session.add_all(chunks)

    # 2. 构造 FAQ 沉淀库 (已启用发布 = 3, 停用 = 1)
    faqs = [
        FAQItem(standard_question="如何申请报销年休假补贴？", standard_answer="请在OA提交流程", is_enabled=True, hit_count=5),
        FAQItem(standard_question="公司打卡考勤时间范围", standard_answer="弹性打卡 9:00-10:00", is_enabled=True, hit_count=3),
        FAQItem(standard_question="新员工入职体检报销指引", standard_answer="凭发票至人事报销", is_enabled=True, hit_count=2),
        FAQItem(standard_question="已废止旧版OA公文流转规范", standard_answer="已停用废弃", is_enabled=False, hit_count=0),
    ]
    db_session.add_all(faqs)

    # 3. 构造知识盲区缺口池 (待处理 OPEN = 4, 已解决 RESOLVED = 2)
    gaps = [
        KnowledgeGap(query_text="企业AI私有化算力申请方案", hit_count=12, status="OPEN"),
        KnowledgeGap(query_text="境外直属子公司合规转账申报", hit_count=9, status="OPEN"),
        KnowledgeGap(query_text="员工补充商业医疗保险报销范围", hit_count=6, status="OPEN"),
        KnowledgeGap(query_text="2026年夏季高温补贴发放标准", hit_count=4, status="OPEN"),
        KnowledgeGap(query_text="旧办公楼搬迁车位续期指引", hit_count=8, status="RESOLVED"),
        KnowledgeGap(query_text="疫情期间居家办公指引", hit_count=1, status="RESOLVED"),
    ]
    db_session.add_all(gaps)

    # 4. 构造问答交互日志流水 (PV = 5, UV = 2: 员工 1001 发起 3 次，员工 1002 发起 2 次)
    logs = [
        ChatAuditLog(
            trace_id=f"trace_kpi_00{i}",
            user_id=1001,
            username="zhangsan",
            query_text=f"员工张三提问_{i}",
            prompt_tokens=20,
            completion_tokens=60,
            total_tokens=80,
            latency_ms=25.0,
        )
        for i in range(3)
    ] + [
        ChatAuditLog(
            trace_id=f"trace_kpi_00{i}",
            user_id=1002,
            username="lisi",
            query_text=f"员工李四提问_{i}",
            prompt_tokens=30,
            completion_tokens=80,
            total_tokens=110,
            latency_ms=35.0,
        )
        for i in range(3, 5)
    ]
    db_session.add_all(logs)
    await db_session.commit()

    # 5. 调用大盘核心 KPI 汇总接口
    res = await client.get("/api/v1/analytics/dashboard-summary")
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["code"] == 200
    kpi = res_json["data"]

    # 6. 深度断言 5 大核心 KPI 聚合统计数值
    assert kpi["pv"] == 5, f"PV 总提问量必须为 5，当前为: {kpi['pv']}"
    assert kpi["uv"] == 2, f"UV 独立用户数必须为 2，当前为: {kpi['uv']}"
    assert kpi["chunks_count"] == 6, f"切片总量必须为 6，当前为: {kpi['chunks_count']}"
    assert kpi["total_chunks"] == 6
    assert kpi["knowledge_units_count"] == 2
    assert kpi["published_faqs"] == 3, f"已发布 FAQ 数必须为 3，当前为: {kpi['published_faqs']}"
    assert kpi["faqs_count"] == 3
    assert kpi["open_gaps"] == 4, f"待处理缺口数必须为 4，已解决缺口必须准确排除，当前为: {kpi['open_gaps']}"
    assert kpi["pending_gaps"] == 4
    assert kpi["knowledge_gaps_count"] == 4

    # 校验端到端延时与缓存命中率
    assert kpi["avg_latency_ms"] > 0
    assert kpi["total_tokens"] == (80 * 3 + 110 * 2)

    print("\n✅ [黄金断言 1 通过] 5 大核心 KPI (PV/UV/切片总量/已发布FAQ/待处理缺口) 聚合统计核验完毕")


@pytest.mark.asyncio
async def test_02_trends_and_top_rankings(client: AsyncClient, db_session: AsyncSession):
    """
    黄金断言 2: 近 7 天 Token/延时趋势数据及高频提问/热门知识 TOP 5 榜单查询
    1. 灌入多条带有算力消耗与延时的审计流水，覆盖连续时间窗口
    2. GET /api/v1/analytics/trends?days=7 验证近 7 天双轴面积折线图数据格式:
       - 返回长度为 7 的时间序列数组
       - 每个节点均包含 date, prompt_tokens, completion_tokens, total_tokens, latency_ms, pv
       - 日期严格按时间先后顺序排列 (YYYY-MM-DD)
    3. 灌入高频缺口与热门知识单元样本
    4. GET /api/v1/analytics/top-rankings 验证双维度 TOP 5 榜单:
       - top_queries: 必须返回高频提问 TOP 5，严格按频次倒序排列 (rank 1 为最高频)
       - top_knowledge: 必须返回热门知识库文档 TOP 5
    """
    # 1. 灌入审计流水数据
    now = datetime.now(timezone.utc)
    audit_today = ChatAuditLog(
        trace_id="trace_trend_01",
        user_id=1,
        username="admin",
        query_text="今日核心业务流程咨询",
        prompt_tokens=150,
        completion_tokens=350,
        total_tokens=500,
        latency_ms=28.5,
    )
    db_session.add(audit_today)

    # 2. 灌入高频提问缺口数据 (共 6 条，验证 TOP 5 截断与频次倒序)
    query_samples = [
        ("企业算力GPU集群申请配额", 88),
        ("境外跨境汇款合规申报手续", 65),
        ("差旅超标报销特殊审批说明", 42),
        ("企业年金提前支取政策规定", 30),
        ("公司附近停车位月租优惠政策", 18),
        ("茶水间咖啡机使用操作说明", 5),  # 排名第 6，不应出现在 TOP 5 中
    ]
    for q_text, freq in query_samples:
        db_session.add(KnowledgeGap(query_text=q_text, hit_count=freq, status="OPEN"))

    # 3. 灌入热门知识文档样本
    doc_samples = [
        "企业财务报销与内控审计规范手册2026.pdf",
        "大模型算力调度与容器基础设施白皮书.pdf",
        "境外投资合规指引与外汇管制政策.pdf",
        "员工薪酬福利与绩效考评办法.pdf",
        "商业秘密防泄露与信息安全红线制度.pdf",
        "低频备用文档.pdf",
    ]
    for title in doc_samples:
        u = KnowledgeUnit(title=title, file_type="pdf", status="INDEXED")
        db_session.add(u)

    await db_session.commit()

    # 4. 验证近 7 天趋势走势接口 (GET /api/v1/analytics/trends?days=7)
    trend_res = await client.get("/api/v1/analytics/trends?days=7")
    assert trend_res.status_code == 200
    trend_data = trend_res.json()["data"]
    assert isinstance(trend_data, list)
    assert len(trend_data) == 7, f"趋势图必须返回 7 天序列，当前长度: {len(trend_data)}"

    # 校验每个时间节点的结构完整性与连续性
    for idx, point in enumerate(trend_data):
        assert "date" in point
        assert "prompt_tokens" in point
        assert "completion_tokens" in point
        assert "total_tokens" in point
        assert "latency_ms" in point
        assert "pv" in point
        if idx > 0:
            assert point["date"] > trend_data[idx - 1]["date"], "趋势图日期序列必须按升序排列"

    today_str = now.strftime("%Y-%m-%d")
    today_point = next((p for p in trend_data if p["date"] == today_str), None)
    assert today_point is not None
    assert today_point["total_tokens"] >= 500
    assert today_point["prompt_tokens"] >= 150
    assert today_point["completion_tokens"] >= 350
    assert today_point["pv"] >= 1

    # 5. 验证双维度 TOP 5 榜单接口 (GET /api/v1/analytics/top-rankings)
    rank_res = await client.get("/api/v1/analytics/top-rankings?limit=5")
    assert rank_res.status_code == 200
    rank_json = rank_res.json()["data"]

    # 5.1 高频提问 TOP 5 校验
    top_queries = rank_json["top_queries"]
    assert len(top_queries) == 5, f"高频提问预期返回 TOP 5，实际返回: {len(top_queries)}"
    assert top_queries[0]["title"] == "企业算力GPU集群申请配额"
    assert top_queries[0]["count"] == 88
    assert top_queries[0]["rank"] == 1

    # 频次必须严格倒序: 88 >= 65 >= 42 >= 30 >= 18
    query_counts = [item["count"] for item in top_queries]
    assert query_counts == [88, 65, 42, 30, 18], f"TOP 5 提问频次必须严格降序: {query_counts}"
    assert all(item["rank"] == i for i, item in enumerate(top_queries, start=1))

    # 5.2 热门知识 TOP 5 校验
    top_knowledge = rank_json["top_knowledge"]
    assert len(top_knowledge) == 5, f"热门知识预期返回 TOP 5，实际返回: {len(top_knowledge)}"
    assert all("title" in k and "count" in k for k in top_knowledge)

    print("\n✅ [黄金断言 2 通过] 近 7 天 Token/延时趋势数据及高频提问/热门知识 TOP 5 榜单查询验证完毕")


@pytest.mark.asyncio
async def test_03_audit_logs_and_evidence_chain(client: AsyncClient, db_session: AsyncSession):
    """
    黄金断言 3: 全链路安全审计日志分页与拦截证据链下钻 (召回/放行/拦截受限切片明细)
    1. 模拟落库 3 种典型安全时序问答审计流水:
       - 场景 A (越权拦截): 普通员工越权提问核心机密，初筛召回 3 个切片，4D 放行 1 个，拦截隔离 2 个敏感切片 (is_blocked=True)
       - 场景 B (合规放行): 提问公开报销，召回 2 个切片全部安全放行 (is_blocked=False)
       - 场景 C (静默回退): 提问未收录知识，召回 0 个切片触发 SilentFallback (is_blocked=True)
    2. GET /api/v1/analytics/audit-logs 分页与条件过滤断言:
       - 分页 total == 3, items == 3
       - 按 is_blocked=true 过滤，精准返回 2 条拦截/受限记录
       - 按 keyword=核心机密 关键词检索，精准匹配场景 A
    3. GET /api/v1/analytics/audit-logs/{id}/evidence-chain 拦截证据链下钻穿透断言:
       - 验证穿透证据链详情中完整包含: trace_id, query, user_context
       - recalled_chunks 包含 3 处初筛切片
       - allowed_chunks 包含 1 处放行切片
       - restricted_chunks 包含 2 处受限拦截切片及其 isolation_reason 隔离成因
       - decision 裁决结论包含 is_blocked=True 与 action=BLOCK
    """
    # 1. 构造切片与知识单元
    unit_sec = KnowledgeUnit(title="核心财务薪资及股权分配机密.pdf", file_type="pdf", status="INDEXED")
    unit_pub = KnowledgeUnit(title="员工差旅餐补公开标准.pdf", file_type="pdf", status="INDEXED")
    db_session.add_all([unit_sec, unit_pub])
    await db_session.commit()
    await db_session.refresh(unit_sec)
    await db_session.refresh(unit_pub)

    chunk_pub = KnowledgeChunk(document_id=unit_pub.id, chunk_index=0, content="国内出差差旅餐补上限为每天100元。")
    chunk_sec_1 = KnowledgeChunk(document_id=unit_sec.id, chunk_index=0, content="2026年高管层股权期权激励计划明细清单。")
    chunk_sec_2 = KnowledgeChunk(document_id=unit_sec.id, chunk_index=1, content="核心董事会津贴与离职竞业限制补偿金额。")
    db_session.add_all([chunk_pub, chunk_sec_1, chunk_sec_2])
    await db_session.commit()
    await db_session.refresh(chunk_pub)
    await db_session.refresh(chunk_sec_1)
    await db_session.refresh(chunk_sec_2)

    # 场景 A: 越权拦截隔离审计流水
    log_intercepted = ChatAuditLog(
        trace_id="trace_kg_audit_sec_01",
        user_id=101,
        username="wangwu",
        employee_id="10101",
        user_dept="市场部",
        user_role="ROLE_COMMON_USER",
        query_text="请提供公司高管股权期权分配核心机密方案",
        answer_snippet="系统根据4D权限策略动态过滤了敏感切片...",
        recalled_chunk_ids=[chunk_pub.id, chunk_sec_1.id, chunk_sec_2.id],
        recalled_count=3,
        allowed_chunk_ids=[chunk_pub.id],
        allowed_count=1,
        restricted_chunk_ids=[chunk_sec_1.id, chunk_sec_2.id],
        restricted_count=2,
        is_blocked=True,
        block_reason="PERMISSION_ISOLATION",
        prompt_tokens=45,
        completion_tokens=80,
        total_tokens=125,
        latency_ms=32.0,
    )

    # 场景 B: 完全合规放行流水
    log_normal = ChatAuditLog(
        trace_id="trace_kg_audit_pub_02",
        user_id=101,
        username="wangwu",
        employee_id="10101",
        user_dept="市场部",
        user_role="ROLE_COMMON_USER",
        query_text="出差差旅餐补每天是多少钱",
        answer_snippet="国内出差差旅餐补上限为每天100元。",
        recalled_chunk_ids=[chunk_pub.id],
        recalled_count=1,
        allowed_chunk_ids=[chunk_pub.id],
        allowed_count=1,
        restricted_chunk_ids=[],
        restricted_count=0,
        is_blocked=False,
        block_reason=None,
        prompt_tokens=25,
        completion_tokens=40,
        total_tokens=65,
        latency_ms=18.0,
    )

    # 场景 C: 缺口静默回退流水
    log_fallback = ChatAuditLog(
        trace_id="trace_kg_audit_fb_03",
        user_id=102,
        username="zhaoliu",
        employee_id="10102",
        user_dept="行政部",
        user_role="ROLE_COMMON_USER",
        query_text="火星基地常驻员工防辐射补贴发放规定",
        answer_snippet="您好！关于您咨询的问题，当前企业知识库未检索到相匹配资料...",
        recalled_chunk_ids=[],
        recalled_count=0,
        allowed_chunk_ids=[],
        allowed_count=0,
        restricted_chunk_ids=[],
        restricted_count=0,
        is_blocked=True,
        block_reason="NO_HITS",
        prompt_tokens=30,
        completion_tokens=60,
        total_tokens=90,
        latency_ms=15.0,
    )

    db_session.add_all([log_intercepted, log_normal, log_fallback])
    await db_session.commit()
    await db_session.refresh(log_intercepted)
    await db_session.refresh(log_normal)
    await db_session.refresh(log_fallback)

    # 2. GET /api/v1/analytics/audit-logs 列表查询与分页过滤验证
    list_res = await client.get("/api/v1/analytics/audit-logs?page=1&page_size=10")
    assert list_res.status_code == 200
    list_data = list_res.json()["data"]
    assert list_data["total"] == 3
    assert len(list_data["items"]) == 3

    # 按 is_blocked=true 条件筛选
    blocked_res = await client.get("/api/v1/analytics/audit-logs?is_blocked=true")
    assert blocked_res.status_code == 200
    blocked_items = blocked_res.json()["data"]["items"]
    assert len(blocked_items) == 2
    assert all(item["is_blocked"] is True for item in blocked_items)

    # 按 keyword 关键词过滤
    kw_res = await client.get("/api/v1/analytics/audit-logs?keyword=高管股权期权")
    assert kw_res.status_code == 200
    kw_items = kw_res.json()["data"]["items"]
    assert len(kw_items) == 1
    assert kw_items[0]["trace_id"] == "trace_kg_audit_sec_01"

    # 3. GET /api/v1/analytics/audit-logs/{id}/evidence-chain 拦截证据链穿透下钻分析
    evidence_res = await client.get(f"/api/v1/analytics/audit-logs/{log_intercepted.id}/evidence-chain")
    assert evidence_res.status_code == 200
    chain = evidence_res.json()["data"]

    # 证据链身份与提问核验
    assert chain["trace_id"] == "trace_kg_audit_sec_01"
    assert chain["query"] == "请提供公司高管股权期权分配核心机密方案"
    assert chain["user_context"]["username"] == "wangwu"
    assert chain["user_context"]["dept"] == "市场部"

    # 初筛召回证据集 (3 处)
    recalled = chain["recalled_chunks"]
    assert len(recalled) == 3
    recalled_ids = [r["chunk_id"] for r in recalled]
    assert chunk_pub.id in recalled_ids
    assert chunk_sec_1.id in recalled_ids
    assert chunk_sec_2.id in recalled_ids

    # 4D放行证据集 (1 处)
    allowed = chain["allowed_chunks"]
    assert len(allowed) == 1
    assert allowed[0]["chunk_id"] == chunk_pub.id

    # 4D拦截受限切片证据集 (2 处敏感切片及隔离理由)
    restricted = chain["restricted_chunks"]
    assert len(restricted) == 2
    restricted_ids = [r["chunk_id"] for r in restricted]
    assert chunk_sec_1.id in restricted_ids
    assert chunk_sec_2.id in restricted_ids
    for r in restricted:
        assert "isolation_reason" in r
        assert "PERMISSION_ISOLATION" in r["isolation_reason"] or "安全护栏" in r["isolation_reason"]

    # 决策裁决与算力消耗
    assert chain["decision"]["is_blocked"] is True
    assert chain["decision"]["action"] == "BLOCK"
    assert chain["metrics"]["total_tokens"] == 125
    assert chain["metrics"]["latency_ms"] == 32.0

    print("\n✅ [黄金断言 3 通过] 全链路安全审计日志分页与拦截证据链下钻穿透深度验证完毕")
