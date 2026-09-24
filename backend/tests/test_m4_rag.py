"""
模块 M4 AI 鉴权检索与问答流式编排自动化测试套件 (test_m4_rag.py)

测试范围:
    1. POST /api/v1/chat/completions 原生 SSE 流式接口 (text/event-stream)
    2. 安全时序: Milvus 初筛 ➔ Guard 鉴权 ➔ MySQL 提取 ➔ BGE-Reranker 精排 ➔ 安全 Prompt ➔ Qwen-Plus 流式回答
    3. SSE 帧事件协议验证: text_delta, citation, warning, done
    4. 越权静默回退: SilentFallback 高情商兜底，0 泄露受限切片标题与内容
    5. GET /api/v1/chat/suggestions 智能联想推荐提问

作者:
    Backend Team & QA
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import json
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.milvus import milvus_service
from app.core.security import create_access_token
from app.models.knowledge import KnowledgeChunk, KnowledgeUnit
from app.schemas.auth import UserContext
from app.schemas.guard import PermissionPolicyConfig
from app.services.guard_service import GuardService
from app.services.rag_service import RAGService


@pytest.mark.asyncio
async def test_compliant_rag_stream_full_flow(client: AsyncClient, db_session: AsyncSession):
    """测试合规问答全流程 SSE 流式输出 (包含 warning, citation, text_delta, done)"""
    # 1. 准备测试数据: 一个公开文档，一个未授权私有文档
    doc_pub = KnowledgeUnit(title="企业差旅规范2026.pdf", file_type="pdf", status="INDEXED")
    doc_priv = KnowledgeUnit(title="高层绝密薪酬方案.pdf", file_type="pdf", status="INDEXED")
    db_session.add_all([doc_pub, doc_priv])
    await db_session.commit()
    await db_session.refresh(doc_pub)
    await db_session.refresh(doc_priv)

    chunk_pub = KnowledgeChunk(
        document_id=doc_pub.id,
        chunk_index=0,
        content="公司差旅住宿补贴标准为每天500元人民币，高铁二等座实报实销。",
        status="indexed",
        has_vector=True,
    )
    chunk_priv = KnowledgeChunk(
        document_id=doc_priv.id,
        chunk_index=0,
        content="管理层年终股权激励基数为100万股，限制流通期三年。",
        status="indexed",
        has_vector=True,
    )
    db_session.add_all([chunk_pub, chunk_priv])
    await db_session.commit()
    await db_session.refresh(chunk_pub)
    await db_session.refresh(chunk_priv)

    # 写入 Milvus
    milvus_service.insert_chunks([
        {"chunk_id": chunk_pub.id, "document_id": doc_pub.id, "embedding": [0.03] * 1024},
        {"chunk_id": chunk_priv.id, "document_id": doc_priv.id, "embedding": [0.03] * 1024},
    ])

    # 4D 策略: doc_pub 全局公开，doc_priv 仅限用户 9999
    guard = GuardService(db=db_session)
    await guard.update_unit_policy(doc_pub.id, PermissionPolicyConfig(is_public=True))
    await guard.update_unit_policy(doc_priv.id, PermissionPolicyConfig(is_public=False, user_ids=[9999]))

    # 普通员工张三 Token
    token = create_access_token({
        "sub": "10086",
        "user_id": 10086,
        "employee_id": "10086",
        "username": "zhangsan",
        "dept_id": 2,
        "role_ids": [3],
        "is_superuser": False,
    })

    # 2. 发起 SSE 问答请求
    res = await client.post(
        "/api/v1/chat/completions",
        json={"query": "请问出差住宿报销标准是多少？", "conversation_id": "conv-rag-test"},
        headers={"Authorization": f"Bearer {token}", "Accept": "text/event-stream"},
    )
    assert res.status_code == 200
    assert "text/event-stream" in res.headers.get("Content-Type", "")

    sse_lines = res.text.split("\n\n")
    events = []
    text_deltas = []
    citations = []

    for block in sse_lines:
        if not block.strip():
            continue
        lines = block.strip().split("\n")
        ev_type = None
        ev_data = None
        for line in lines:
            if line.startswith("event: "):
                ev_type = line[7:].strip()
            elif line.startswith("data: "):
                ev_data = json.loads(line[6:].strip())
        if ev_type:
            events.append(ev_type)
            if ev_type == "text_delta" and ev_data:
                text_deltas.append(ev_data.get("delta", ""))
            elif ev_type == "citation" and ev_data:
                citations.append(ev_data)

    # 3. 验证事件流符合时序与规范
    assert "warning" in events, "因初筛中包含私有切片，必须收到 warning 隔离事件帧"
    assert "citation" in events, "必须收到溯源切片事件帧"
    assert "text_delta" in events, "必须收到打字机文本增量"
    assert "done" in events, "必须收到结束完成帧"

    # 4. 验证溯源切片及安全隔离
    assert len(citations) >= 1
    assert citations[0]["unit_title"] == "企业差旅规范2026.pdf"
    assert "500" in citations[0]["snippet"]

    full_answer = "".join(text_deltas)
    assert len(full_answer) > 0
    # 绝对禁止泄露私有绝密切片内容
    assert "股权激励" not in full_answer
    assert "高层绝密薪酬方案" not in res.text


@pytest.mark.asyncio
async def test_silent_fallback_on_full_restriction(client: AsyncClient, db_session: AsyncSession):
    """测试当检索切片 100% 被 4D 鉴权剥离时触发 SilentFallback 高情商兜底"""
    # 准备仅限财务专员的秘密文档
    doc_secret = KnowledgeUnit(title="董事会期权分配机密方案.pdf", file_type="pdf", status="INDEXED")
    db_session.add(doc_secret)
    await db_session.commit()
    await db_session.refresh(doc_secret)

    chunk = KnowledgeChunk(
        document_id=doc_secret.id,
        chunk_index=0,
        content="公司各合伙人股份分配比例与股权回购条款细则。",
        status="indexed",
        has_vector=True,
    )
    db_session.add(chunk)
    await db_session.commit()
    await db_session.refresh(chunk)

    milvus_service.insert_chunks([
        {"chunk_id": chunk.id, "document_id": doc_secret.id, "embedding": [0.08] * 1024}
    ])

    # 策略: 仅限 user_id=8888
    guard = GuardService(db=db_session)
    await guard.update_unit_policy(doc_secret.id, PermissionPolicyConfig(is_public=False, user_ids=[8888]))

    # 普通员工李四 (user_id=10087)
    token = create_access_token({
        "sub": "10087",
        "user_id": 10087,
        "employee_id": "10087",
        "username": "lisi",
        "dept_id": 3,
        "role_ids": [2],
        "is_superuser": False,
    })

    res = await client.post(
        "/api/v1/chat/completions",
        json={"query": "董事会期权股份分配比例是什么？"},
        headers={"Authorization": f"Bearer {token}", "Accept": "text/event-stream"},
    )
    assert res.status_code == 200
    sse_text = res.text

    # 1. 绝不泄露受限切片信息
    assert "董事会期权分配机密方案" not in sse_text, "严禁泄露受限文档标题"
    assert "合伙人股份分配" not in sse_text, "严禁泄露敏感正文"
    assert "event: citation" not in sse_text, "越权静默回退绝不提供溯源卡片"

    # 2. 验证高情商兜底话术与 done 标记
    reconstructed = ""
    for line in sse_text.splitlines():
        if line.startswith("data: ") and "delta" in line:
            try:
                reconstructed += json.loads(line[6:].strip()).get("delta", "")
            except Exception:
                pass

    assert "未检索到相匹配的公开或授权参考资料" in reconstructed, "必须触发高情商静默兜底"
    assert "is_silent_fallback" in sse_text


@pytest.mark.asyncio
async def test_chat_suggestions_api(client: AsyncClient):
    """测试 GET /api/v1/chat/suggestions 接口"""
    res = await client.get("/api/v1/chat/suggestions")
    assert res.status_code == 200
    res_data = res.json()["data"]
    assert isinstance(res_data, list)
    assert len(res_data) >= 3
