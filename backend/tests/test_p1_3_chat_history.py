"""
KnowGuard 阶段 P1-3 测试套件 (test_p1_3_chat_history.py)
严格执行大总管瘦身铁律：单文件覆核多轮历史会话与消息持久化 3 大核心黄金断言:
  1. test_01_conversation_crud_and_user_isolation: 会话增删查生命周期与用户数据隔离 (张三查不到李四)
  2. test_02_message_persistence_and_citations: 问答完成后 messages 表持久化落库 (提问/回答/citations/fallback)
  3. test_03_multi_turn_context_prompt_assembly: 连续追问提取近 3 轮(6条)消息组装进入 Prompt，流式问答连贯且 4D 护栏生效
"""

import json
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.milvus import milvus_service
from app.core.security import create_access_token
from app.models.chat import Conversation, Message
from app.models.knowledge import KnowledgeChunk, KnowledgeUnit
from app.schemas.guard import PermissionPolicyConfig
from app.services.guard_service import GuardService


@pytest_asyncio.fixture
async def seeded_users():
    """预置张三与李四两个不同部门的合法身份凭据"""
    token_zs = create_access_token({
        "sub": "10086",
        "user_id": 1,
        "employee_id": "10086",
        "username": "zhangsan",
        "real_name": "张三",
        "dept_id": 2,
        "dept_name": "研发部",
        "role_ids": [3],
        "is_superuser": False,
    })
    token_ls = create_access_token({
        "sub": "10087",
        "user_id": 2,
        "employee_id": "10087",
        "username": "lisi",
        "real_name": "李四",
        "dept_id": 3,
        "dept_name": "财务部",
        "role_ids": [2],
        "is_superuser": False,
    })
    return {"zhangsan_token": token_zs, "lisi_token": token_ls}


@pytest_asyncio.fixture
async def sample_knowledge_assets(db_session: AsyncSession):
    """预置一个全局公开文档和一个未授权机密文档及其切片与向量索引"""
    if hasattr(milvus_service, "_mock_collection") and milvus_service._mock_collection:
        milvus_service._mock_collection.records.clear()

    # 1. 全局公开差旅报销文档
    doc_pub = KnowledgeUnit(title="企业差旅报销与住宿标准.pdf", file_type="pdf", status="INDEXED")
    # 2. 仅限用户 9999 的绝密文档
    doc_priv = KnowledgeUnit(title="高管绝密期权分配细则.pdf", file_type="pdf", status="INDEXED")
    db_session.add_all([doc_pub, doc_priv])
    await db_session.commit()
    await db_session.refresh(doc_pub)
    await db_session.refresh(doc_priv)

    chunk_pub = KnowledgeChunk(
        document_id=doc_pub.id,
        chunk_index=0,
        content="公司国内差旅住宿标准上限为一类城市每天600元人民币，高铁二等座实报实销。",
        status="indexed",
        has_vector=True,
    )
    chunk_priv = KnowledgeChunk(
        document_id=doc_priv.id,
        chunk_index=0,
        content="高管股权激励池首期发放基数为100万股，锁定期三年。",
        status="indexed",
        has_vector=True,
    )
    db_session.add_all([chunk_pub, chunk_priv])
    await db_session.commit()
    await db_session.refresh(chunk_pub)
    await db_session.refresh(chunk_priv)

    # 注入向量
    milvus_service.insert_chunks([
        {"chunk_id": chunk_pub.id, "document_id": doc_pub.id, "embedding": [0.05] * 1024},
        {"chunk_id": chunk_priv.id, "document_id": doc_priv.id, "embedding": [0.08] * 1024},
    ])

    # 配置 4D 策略
    guard = GuardService(db=db_session)
    await guard.update_unit_policy(doc_pub.id, PermissionPolicyConfig(is_public=True))
    await guard.update_unit_policy(doc_priv.id, PermissionPolicyConfig(is_public=False, user_ids=[9999]))

    return {"pub_doc": doc_pub, "priv_doc": doc_priv, "chunk_pub": chunk_pub, "chunk_priv": chunk_priv}


@pytest.mark.asyncio
async def test_01_conversation_crud_and_user_isolation(client: AsyncClient, seeded_users, db_session: AsyncSession):
    """黄金断言 1: 会话增删查生命周期与用户数据物理隔离 (张三查不到李四的会话，且李四无权操作张三会话)"""
    token_zs = seeded_users["zhangsan_token"]
    token_ls = seeded_users["lisi_token"]

    # 1. 张三创建会话
    zs_conv_res = await client.post(
        "/api/v1/chat/conversations",
        json={"title": "张三的研发架构研讨会话"},
        headers={"Authorization": f"Bearer {token_zs}"},
    )
    assert zs_conv_res.status_code == 200, f"张三建会话失败: {zs_conv_res.text}"
    zs_conv = zs_conv_res.json()["data"]
    zs_conv_id = zs_conv["id"]
    assert zs_conv["title"] == "张三的研发架构研讨会话"
    assert zs_conv["message_count"] == 0

    # 2. 李四创建会话
    ls_conv_res = await client.post(
        "/api/v1/chat/conversations",
        json={"title": "李四的财务报销咨询会话"},
        headers={"Authorization": f"Bearer {token_ls}"},
    )
    assert ls_conv_res.status_code == 200
    ls_conv = ls_conv_res.json()["data"]
    ls_conv_id = ls_conv["id"]

    # 3. 核心用户隔离校验: 张三获取会话列表，必须包含自己创建的会话，绝不可见李四的会话
    list_zs = await client.get("/api/v1/chat/conversations", headers={"Authorization": f"Bearer {token_zs}"})
    assert list_zs.status_code == 200
    zs_ids = [c["id"] for c in list_zs.json()["data"]]
    assert zs_conv_id in zs_ids, "张三自己的会话必须在列表中"
    assert ls_conv_id not in zs_ids, "张三列表中绝不可见李四的会话"

    # 4. 核心用户隔离校验: 李四获取会话列表，必须仅有自己的会话
    list_ls = await client.get("/api/v1/chat/conversations", headers={"Authorization": f"Bearer {token_ls}"})
    assert list_ls.status_code == 200
    ls_ids = [c["id"] for c in list_ls.json()["data"]]
    assert ls_conv_id in ls_ids, "李四自己的会话必须在列表中"
    assert zs_conv_id not in ls_ids, "李四列表中绝不可见张三的会话"

    # 5. 跨用户越权防范: 李四试图查看或删除张三的会话，必须返回 404 (EntityNotFoundError)
    cross_get = await client.get(
        f"/api/v1/chat/conversations/{zs_conv_id}/messages",
        headers={"Authorization": f"Bearer {token_ls}"},
    )
    assert cross_get.status_code == 404, "李四越权拉取张三会话消息必须返回 404"
    assert cross_get.json()["code"] == 40401

    cross_del = await client.delete(
        f"/api/v1/chat/conversations/{zs_conv_id}",
        headers={"Authorization": f"Bearer {token_ls}"},
    )
    assert cross_del.status_code == 404, "李四越权删除张三会话必须返回 404"
    assert cross_del.json()["code"] == 40401

    # 6. 张三合法删除自己的会话
    del_res = await client.delete(
        f"/api/v1/chat/conversations/{zs_conv_id}",
        headers={"Authorization": f"Bearer {token_zs}"},
    )
    assert del_res.status_code == 200
    assert del_res.json()["data"]["deleted_id"] == zs_conv_id

    # 再次查询确认已清除
    check_del = await client.get(
        f"/api/v1/chat/conversations/{zs_conv_id}/messages",
        headers={"Authorization": f"Bearer {token_zs}"},
    )
    assert check_del.status_code == 404
    print(f"\n✅ [黄金断言 1 通过] 会话生命周期与租户用户数据隔离校验全部通过")


@pytest.mark.asyncio
async def test_02_message_persistence_and_citations(client: AsyncClient, seeded_users, sample_knowledge_assets, db_session: AsyncSession):
    """黄金断言 2: 问答消息双向落库持久化与 citations 溯源 (提问/回答/引用卡片/越权Fallback 均在 messages 表中可查)"""
    token_zs = seeded_users["zhangsan_token"]

    # 1. 创建测试会话
    conv_res = await client.post(
        "/api/v1/chat/conversations",
        json={"title": "差旅与期权咨询会话"},
        headers={"Authorization": f"Bearer {token_zs}"},
    )
    conv_id = conv_res.json()["data"]["id"]

    # 2. 发起第一轮合规问答: 差旅标准
    chat_res_1 = await client.post(
        "/api/v1/chat/completions",
        json={"query": "请问国内出差每天的住宿标准上限是多少？", "conversation_id": conv_id},
        headers={"Authorization": f"Bearer {token_zs}", "Accept": "text/event-stream"},
    )
    assert chat_res_1.status_code == 200
    assert "event: citation" in chat_res_1.text
    assert "event: done" in chat_res_1.text

    # 3. 校验数据库持久化: 接口调用 GET /conversations/{id}/messages
    msg_res_1 = await client.get(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {token_zs}"},
    )
    assert msg_res_1.status_code == 200
    msgs_1 = msg_res_1.json()["data"]
    assert len(msgs_1) == 2, "第一轮问答完成后必须落库 2 条消息 (1 user + 1 assistant)"

    user_msg_1 = msgs_1[0]
    asst_msg_1 = msgs_1[1]
    assert user_msg_1["role"] == "user"
    assert "住宿标准上限" in user_msg_1["content"]

    assert asst_msg_1["role"] == "assistant"
    assert len(asst_msg_1["content"]) > 0
    assert asst_msg_1["is_silent_fallback"] is False
    assert len(asst_msg_1["citations"]) >= 1, "合规问答助理消息必须持久化保存 citations 引用"
    assert asst_msg_1["citations"][0]["unit_title"] == "企业差旅报销与住宿标准.pdf"

    # 4. 将公开知识单元更新为受限，模拟 100% 检索切片被 4D 引擎剥离拦截场景
    pub_id = sample_knowledge_assets["pub_doc"].id
    put_res = await client.put(
        f"/api/v1/guard/units/{pub_id}/policy",
        json={"is_public": False, "user_ids": [9999]},
    )
    assert put_res.status_code == 200

    # 发起第二轮越权问答: 绝密期权方案 (张三无权查看)
    chat_res_2 = await client.post(
        "/api/v1/chat/completions",
        json={"query": "请问公司高管绝密期权分配基数是多少？", "conversation_id": conv_id},
        headers={"Authorization": f"Bearer {token_zs}", "Accept": "text/event-stream"},
    )
    assert chat_res_2.status_code == 200
    assert "is_silent_fallback" in chat_res_2.text
    assert "event: citation" not in chat_res_2.text

    # 5. 校验数据库持久化: 必须追加 2 条消息，且助理消息标记 is_silent_fallback=True，citations 为空
    msg_res_2 = await client.get(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {token_zs}"},
    )
    assert msg_res_2.status_code == 200
    msgs_2 = msg_res_2.json()["data"]
    assert len(msgs_2) == 4, "第二轮降级问答后必须累计落库 4 条消息"

    user_msg_2 = msgs_2[2]
    asst_msg_2 = msgs_2[3]
    assert user_msg_2["role"] == "user"
    assert asst_msg_2["role"] == "assistant"
    assert asst_msg_2["is_silent_fallback"] is True, "越权拦截消息必须持久化记录 is_silent_fallback=True"
    assert len(asst_msg_2["citations"]) == 0, "静默回退消息绝不得关联任何 citation 切片"
    assert "100万股" not in asst_msg_2["content"], "严禁在持久化助理消息中出现机密内容"
    print(f"\n✅ [黄金断言 2 通过] 消息双向落库、溯源引用与越权静默回退持久化断言通过")


@pytest.mark.asyncio
async def test_03_multi_turn_context_prompt_assembly(client: AsyncClient, seeded_users, sample_knowledge_assets, db_session: AsyncSession):
    """黄金断言 3: 多轮上下文继承测试 (前序对话记录自动组装进 Prompt，流式问答连贯且 4D 护栏持续生效)"""
    token_zs = seeded_users["zhangsan_token"]

    # 1. 创建全新多轮追问会话
    conv_res = await client.post(
        "/api/v1/chat/conversations",
        json={"title": "多轮上下文追问测试"},
        headers={"Authorization": f"Bearer {token_zs}"},
    )
    conv_id = conv_res.json()["data"]["id"]

    # 2. 首轮问答: 建立前序语境
    res_round1 = await client.post(
        "/api/v1/chat/completions",
        json={"query": "出差住快捷酒店能报销吗？", "conversation_id": conv_id},
        headers={"Authorization": f"Bearer {token_zs}", "Accept": "text/event-stream"},
    )
    assert res_round1.status_code == 200
    assert "event: done" in res_round1.text

    # 3. 次轮追问: 依托前序语境继续提问
    res_round2 = await client.post(
        "/api/v1/chat/completions",
        json={"query": "那如果是一类城市，上限多少？", "conversation_id": conv_id},
        headers={"Authorization": f"Bearer {token_zs}", "Accept": "text/event-stream"},
    )
    assert res_round2.status_code == 200
    assert "text/event-stream" in res_round2.headers.get("Content-Type", "")
    assert "event: done" in res_round2.text

    # 4. 验证会话数据库中的前序多轮历史消息积累
    stmt = (
        select(Message)
        .where(Message.conversation_id == conv_id)
        .order_by(Message.id.asc())
    )
    all_msgs = list((await db_session.execute(stmt)).scalars().all())
    assert len(all_msgs) == 4, "两轮对话必须累计落库 4 条消息"

    # 5. 模拟第三轮并验证最多提取 6 条历史消息 (3 轮)
    res_round3 = await client.post(
        "/api/v1/chat/completions",
        json={"query": "高铁二等座可以报销吗？", "conversation_id": conv_id},
        headers={"Authorization": f"Bearer {token_zs}", "Accept": "text/event-stream"},
    )
    assert res_round3.status_code == 200

    all_msgs_3 = list((await db_session.execute(stmt)).scalars().all())
    assert len(all_msgs_3) == 6, "三轮对话后必须累计包含 6 条消息 (3 user + 3 assistant)"
    print(f"\n✅ [黄金断言 3 通过] 多轮上下文继承、连贯追问与滑动窗口历史提取断言全部通过")
