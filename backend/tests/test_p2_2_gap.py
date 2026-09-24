"""
KnowGuard 阶段 P2-2 知识缺口 Knowledge Gap 流转闭环测试套件 (test_p2_2_gap.py)
严格执行大总管 MVP 极简铁律：单文件高密度覆核 3 大核心黄金断言:
  1. test_01_gap_auto_collection_and_deduplication: 问答未命中与静默回退时自动捕获缺口，重复提问去重并累加频次 frequency (hit_count)
  2. test_02_gap_query_and_sorting: GET /gaps (或 /knowledge-gaps) 支持按频次 frequency 倒序排列和按状态筛选 (status=OPEN, etc.)
  3. test_03_gap_resolve_and_ignore_lifecycle: 缺口一键转建/解决 (resolve) 与忽略 (ignore) 生命周期状态流转 (OPEN -> RESOLVED / IGNORED)
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evolution import KnowledgeGap
from app.services.evolution_service import EvolutionService


@pytest.mark.asyncio
async def test_01_gap_auto_collection_and_deduplication(client: AsyncClient, db_session: AsyncSession):
    """
    黄金断言 1: 问答未命中与静默回退时自动捕获缺口，重复提问去重并累加频次 frequency (hit_count)
    1. 用户向网关发起企业未收录知识的提问，触发 SilentFallback 静默回退兜底
    2. 知识缺口池自动捕获该问题，记录为 OPEN 状态，频次 frequency == 1
    3. 用户或同事重复提问相同问题（包含首尾空格容错），触发幂等去重，不新增记录行，频次累计为 frequency == 2
    4. 验证 EvolutionService.record_knowledge_gap 服务层与数据库底层状态一致性
    """
    test_query = "2026年企业量子加密网络接入规范"

    # 1. 模拟用户首次提问未命中知识库，触发 RAG 静默回退 (SilentFallback)
    chat_res_1 = await client.post("/api/v1/chat/completions", json={
        "query": test_query,
    })
    assert chat_res_1.status_code == 200
    assert "text/event-stream" in chat_res_1.headers.get("content-type", "")
    sse_text_1 = chat_res_1.text
    assert "is_silent_fallback" in sse_text_1 or "未检索到相匹配" in sse_text_1

    # 2. 校验知识盲区缺口池已自动捕获并记录该提问
    gaps_stmt = select(KnowledgeGap).where(KnowledgeGap.is_deleted == False)
    db_gaps = (await db_session.execute(gaps_stmt)).scalars().all()
    assert len(db_gaps) == 1, f"未命中提问后预期自动捕获 1 条缺口，实际记录数: {len(db_gaps)}"

    gap_record = db_gaps[0]
    assert gap_record.query_text == test_query
    assert gap_record.question == test_query
    assert gap_record.query == test_query
    assert gap_record.hit_count == 1
    assert gap_record.frequency == 1
    assert gap_record.status == "OPEN"
    initial_first_seen = gap_record.first_seen_at
    initial_last_seen = gap_record.last_seen_at
    assert initial_first_seen is not None
    assert initial_last_seen is not None

    # 3. 用户携带空格再次提问相同问题，验证系统级自动去重与频次累加
    duplicate_query = f"   {test_query}   "
    chat_res_2 = await client.post("/api/v1/chat/completions", json={
        "query": duplicate_query,
    })
    assert chat_res_2.status_code == 200

    # 刷新数据库会话并断言：记录行数依然为 1，frequency 累加为 2
    db_gaps_after = (await db_session.execute(gaps_stmt)).scalars().all()
    assert len(db_gaps_after) == 1, "重复提问必须去重聚合，绝不能生成重复记录行"

    updated_gap = db_gaps_after[0]
    assert updated_gap.id == gap_record.id
    assert updated_gap.hit_count == 2
    assert updated_gap.frequency == 2
    assert updated_gap.status == "OPEN"
    assert updated_gap.last_seen_at >= initial_last_seen

    # 4. 直接验证 EvolutionService.record_knowledge_gap 接口幂等性与大小写容错去重
    svc = EvolutionService(db=db_session)
    third_gap = await svc.record_knowledge_gap(query=test_query, reason="NO_HITS")
    assert third_gap.id == gap_record.id
    assert third_gap.hit_count == 3
    assert third_gap.frequency == 3

    # API 接口验证 /api/v1/evolution/gaps 响应中的 query 与 frequency 字段
    api_res = await client.get("/api/v1/evolution/gaps")
    assert api_res.status_code == 200
    res_data = api_res.json()["data"]
    assert res_data["total"] == 1
    api_gap = res_data["items"][0]
    assert api_gap["query"] == test_query
    assert api_gap["frequency"] == 3
    assert api_gap["hit_count"] == 3
    assert api_gap["status"] == "OPEN"

    print("\n✅ [黄金断言 1 通过] 问答未命中与静默回退时自动捕获缺口，重复提问去重并累加频次 frequency 验证成功")


@pytest.mark.asyncio
async def test_02_gap_query_and_sorting(client: AsyncClient, db_session: AsyncSession):
    """
    黄金断言 2: GET /gaps (或 /knowledge-gaps) 支持按频次 frequency 倒序排列和按状态筛选
    1. 灌入不同频次 (frequency: 25, 12, 8, 3, 1) 和不同状态 (OPEN, RESOLVED, IGNORED) 的缺口样本
    2. GET /gaps 默认及显式按 frequency desc 倒序排列，验证高频缺口精准置顶
    3. GET /knowledge-gaps 别名路由一致性验证
    4. 按 status=OPEN 筛选，排除已解决/已忽略记录；按 status=RESOLVED 筛选已闭环记录
    5. 分页参数校验 (page, page_size, total)
    """
    # 1. 批量构造 5 条不同频次与状态的测试样本
    gap_samples = [
        KnowledgeGap(query_text="海外仓滞期免收费用申请政策", hit_count=8, status="OPEN", reason="NO_HITS"),
        KnowledgeGap(query_text="境外差旅高危国家安全特别指引", hit_count=25, status="OPEN", reason="PERMISSION_RESTRICTED"),
        KnowledgeGap(query_text="2026年食堂餐卡充值退款规范", hit_count=3, status="OPEN", reason="NO_HITS"),
        KnowledgeGap(query_text="旧版内部公积金查询入口地址", hit_count=12, status="RESOLVED", reason="NO_HITS"),
        KnowledgeGap(query_text="无关废弃提问测试样本", hit_count=1, status="IGNORED", reason="NO_HITS"),
    ]
    db_session.add_all(gap_samples)
    await db_session.commit()

    # 2. GET /api/v1/evolution/gaps 按频次倒序查询 (sort_by=frequency, order=desc)
    res_sorted = await client.get("/api/v1/evolution/gaps?sort_by=frequency&order=desc")
    assert res_sorted.status_code == 200
    sorted_data = res_sorted.json()["data"]
    assert sorted_data["total"] == 5
    items = sorted_data["items"]
    assert len(items) == 5

    # 断言频次严格倒序排列: 25 -> 12 -> 8 -> 3 -> 1
    frequencies = [item["frequency"] for item in items]
    hit_counts = [item["hit_count"] for item in items]
    assert frequencies == [25, 12, 8, 3, 1], f"频次倒序不符预期: {frequencies}"
    assert hit_counts == [25, 12, 8, 3, 1]
    assert items[0]["query"] == "境外差旅高危国家安全特别指引"
    assert items[0]["reason"] == "PERMISSION_RESTRICTED"

    # 3. 验证路由别名 GET /api/v1/evolution/knowledge-gaps
    alias_res = await client.get("/api/v1/evolution/knowledge-gaps?sort_by=frequency&order=desc")
    assert alias_res.status_code == 200
    alias_items = alias_res.json()["data"]["items"]
    assert [i["frequency"] for i in alias_items] == [25, 12, 8, 3, 1]

    # 4. 状态筛选验证: status=OPEN
    open_res = await client.get("/api/v1/evolution/gaps?status=OPEN&sort_by=frequency")
    assert open_res.status_code == 200
    open_data = open_res.json()["data"]
    assert open_data["total"] == 3
    open_items = open_data["items"]
    assert len(open_items) == 3
    assert all(i["status"] == "OPEN" for i in open_items)
    assert [i["frequency"] for i in open_items] == [25, 8, 3]

    # 状态筛选验证: status=RESOLVED
    resolved_res = await client.get("/api/v1/evolution/gaps?status=RESOLVED")
    assert resolved_res.status_code == 200
    resolved_items = resolved_res.json()["data"]["items"]
    assert len(resolved_items) == 1
    assert resolved_items[0]["query"] == "旧版内部公积金查询入口地址"
    assert resolved_items[0]["status"] == "RESOLVED"

    # 5. 分页参数验证 (page=1, page_size=2)
    page_res = await client.get("/api/v1/evolution/gaps?page=1&page_size=2&sort_by=frequency")
    assert page_res.status_code == 200
    page_data = page_res.json()["data"]
    assert page_data["page"] == 1
    assert page_data["page_size"] == 2
    assert page_data["total"] == 5
    assert len(page_data["items"]) == 2
    assert page_data["items"][0]["frequency"] == 25
    assert page_data["items"][1]["frequency"] == 12

    print("\n✅ [黄金断言 2 通过] GET /gaps (及 /knowledge-gaps) 支持频次倒序与状态筛选功能校验完毕")


@pytest.mark.asyncio
async def test_03_gap_resolve_and_ignore_lifecycle(client: AsyncClient, db_session: AsyncSession):
    """
    黄金断言 3: 缺口一键转建/解决 (resolve) 与忽略 (ignore) 生命周期状态流转
    1. 创建初始 OPEN 状态的缺口记录
    2. POST /gaps/{id}/resolve 标记解决，验证状态流转为 RESOLVED 并持久化
    3. POST /gaps/{id}/ignore 忽略废弃，验证状态流转为 IGNORED 并持久化
    4. 验证 /knowledge-gaps/{id}/resolve 与 /knowledge-gaps/{id}/ignore 别名端点
    5. 验证 POST /gaps/{id}/convert 转建工单流转
    6. 验证不存在 ID 的 404 容错处理
    """
    # 1. 插入两条初始待处理缺口
    g1 = KnowledgeGap(query_text="年终奖金扣税递延计算公式", hit_count=18, status="OPEN")
    g2 = KnowledgeGap(query_text="火星基地常驻员工防辐射补贴", hit_count=2, status="OPEN")
    g3 = KnowledgeGap(query_text="企业AI算力集群配额申报规范", hit_count=30, status="OPEN")

    db_session.add_all([g1, g2, g3])
    await db_session.commit()
    await db_session.refresh(g1)
    await db_session.refresh(g2)
    await db_session.refresh(g3)

    # 2. 执行缺口解决 (POST /gaps/{id}/resolve)
    res_resolve = await client.post(f"/api/v1/evolution/gaps/{g1.id}/resolve")
    assert res_resolve.status_code == 200
    resolve_data = res_resolve.json()["data"]
    assert resolve_data["id"] == g1.id
    assert resolve_data["status"] == "RESOLVED"

    # 数据库核验
    await db_session.refresh(g1)
    assert g1.status == "RESOLVED"
    assert g1.updated_at is not None

    # 3. 执行缺口忽略 (POST /gaps/{id}/ignore)
    res_ignore = await client.post(f"/api/v1/evolution/gaps/{g2.id}/ignore")
    assert res_ignore.status_code == 200
    ignore_data = res_ignore.json()["data"]
    assert ignore_data["id"] == g2.id
    assert ignore_data["status"] == "IGNORED"

    # 数据库核验
    await db_session.refresh(g2)
    assert g2.status == "IGNORED"

    # 4. 路由别名验证: POST /api/v1/evolution/knowledge-gaps/{id}/resolve
    g4 = KnowledgeGap(query_text="别名路由测试缺口", hit_count=5, status="OPEN")
    db_session.add(g4)
    await db_session.commit()
    await db_session.refresh(g4)

    alias_res = await client.post(f"/api/v1/evolution/knowledge-gaps/{g4.id}/resolve")
    assert alias_res.status_code == 200
    assert alias_res.json()["data"]["status"] == "RESOLVED"
    await db_session.refresh(g4)
    assert g4.status == "RESOLVED"

    # 5. 一键转建工单验证: POST /gaps/{id}/convert
    res_convert = await client.post(f"/api/v1/evolution/gaps/{g3.id}/convert", json={
        "title": "【知识库补全】企业AI算力集群配额申报规范",
        "domain": "技术基建",
        "assignee": "架构组",
        "notes": "优先补全文档并下发部门培训",
    })
    assert res_convert.status_code == 200
    assert res_convert.json()["data"]["status"] == "CONVERTED"
    await db_session.refresh(g3)
    assert g3.status == "CONVERTED"

    # 6. 不存在 ID 异常测试 (404)
    not_found_res = await client.post("/api/v1/evolution/gaps/99999/resolve")
    assert not_found_res.status_code == 404

    # 7. 单条详情查询接口验证: GET /api/v1/evolution/gaps/{id}
    detail_res = await client.get(f"/api/v1/evolution/gaps/{g1.id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["data"]["id"] == g1.id
    assert detail_res.json()["data"]["status"] == "RESOLVED"

    print("\n✅ [黄金断言 3 通过] 缺口一键转建/解决 (resolve) 与忽略 (ignore) 全生命周期流转验证完毕")
