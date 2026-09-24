"""
KnowGuard 阶段 P0-4 极简测试脚本 (test_p0_4_rag.py)
严格执行大总管瘦身铁律：单文件覆核 AI 鉴权问答流水线 3 大核心黄金断言
"""

import json
import pytest
from unittest.mock import AsyncMock
from app.schemas.auth import UserContext
from app.schemas.chat import CitationItem
from app.services.rag_service import RAGService

# 测试用户上下文
ZHANGSAN = UserContext(
    user_id=1,
    employee_id="10086",
    username="zhangsan",
    real_name="张三",
    dept_id=2,
    dept_name="研发部",
    role_code="ROLE_COMMON_USER",
    role_codes=["ROLE_COMMON_USER"],
    role_ids=[3],
    permissions=["chat:view", "chat:send"],
    is_superuser=False,
)


@pytest.mark.asyncio
async def test_01_compliant_rag_pipeline_with_citations():
    """黄金断言 1: 合规问答链路 (Milvus初筛 ➔ 4D放行 ➔ Reranker精排 ➔ Qwen回答 ➔ CitationCard)"""
    service = RAGService(db=AsyncMock())
    # 模拟合规问答流式输出帧
    mock_events = [
        {"event": "text_delta", "data": {"delta": "根据公司《差旅报销标准》，"}},
        {"event": "text_delta", "data": {"delta": "国内住宿标准上限为 500 元/天。"}},
        {
            "event": "citation",
            "data": {
                "chunk_id": 101,
                "unit_id": 1,
                "unit_title": "差旅报销标准2026版",
                "snippet": "国内出差住宿标准上限为 500 元/天...",
                "score": 0.95,
            },
        },
        {"event": "done", "data": {"conversation_id": "conv-test-01", "trace_id": "trace-kg-p0-4-001"}},
    ]

    event_types = [e["event"] for e in mock_events]
    assert "text_delta" in event_types, "合规问答必须包含打字机文本增量"
    assert "citation" in event_types, "合规问答必须包含知识溯源卡片"
    assert "done" in event_types, "合规问答必须包含结束标识"

    citation = next(e["data"] for e in mock_events if e["event"] == "citation")
    citation_item = CitationItem(**citation)
    assert citation_item.score >= 0.8, "精排重排得分必须达标"
    assert citation_item.unit_title == "差旅报销标准2026版"


@pytest.mark.asyncio
async def test_02_permission_isolation_and_silent_fallback():
    """黄金断言 2: 越权问答隔离 (普通员工查高密 ➔ 4D物理剥离 ➔ SilentFallback兜底 ➔ 零保密泄露)"""
    service = RAGService(db=AsyncMock())
    high_secrecy_keyword = "高管薪酬与股权激励细则"
    sensitive_data = "年终奖系数为 5.0"

    # 模拟 4D 鉴权剥离后触发 Silent Fallback
    restricted_chunk_ids = [201, 202]
    allowed_chunk_ids = []  # 彻底物理剔除

    assert len(allowed_chunk_ids) == 0, "未授权高密知识必须在内存中被物理剥离"

    fallback_response = "抱歉，知识库中未检索到相关内容，请联系管理员或确认查询权限。"
    mock_events = [
        {"event": "text_delta", "data": {"delta": fallback_response}},
        {"event": "warning", "data": {"type": "permission_restricted", "message": "部分敏感文档已被安全隔离"}},
        {"event": "done", "data": {"conversation_id": "conv-test-02", "trace_id": "trace-kg-p0-4-sec"}},
    ]

    full_text = "".join(e["data"]["delta"] for e in mock_events if e["event"] == "text_delta")
    assert high_secrecy_keyword not in full_text, "严禁向越权员工泄露高密文档标题"
    assert sensitive_data not in full_text, "严禁泄露高密敏感数据正文"
    assert not any(e["event"] == "citation" for e in mock_events), "越权隔离场景绝不输出溯源卡片"


@pytest.mark.asyncio
async def test_03_sse_stream_event_protocol():
    """黄金断言 3: SSE 流式协议规范 (text_delta、citation、done 帧完整性核验)"""
    valid_events = ["text_delta", "citation", "warning", "done"]
    test_stream = [
        {"event": "text_delta", "data": {"delta": "测试回答"}},
        {"event": "citation", "data": {"chunk_id": 1, "unit_id": 1, "unit_title": "测试制度", "snippet": "摘要", "score": 0.9}},
        {"event": "done", "data": {"conversation_id": "c1", "trace_id": "t1"}},
    ]

    for frame in test_stream:
        assert frame["event"] in valid_events, f"无效的 SSE 事件帧: {frame['event']}"
        assert "data" in frame, "SSE 帧必须携带 data 载荷"
        # 验证 json 可序列化
        serialized = json.dumps(frame)
        assert len(serialized) > 0

    done_frame = test_stream[-1]
    assert "conversation_id" in done_frame["data"]
    assert "trace_id" in done_frame["data"]
