"""
多轮历史会话与对话消息持久化实体模型 (Conversation & ChatMessage)

职责:
    - conversations (主表): id(VARCHAR(64) PK), user_id(BIGINT), title(VARCHAR(128)), message_count(INT), is_active(BOOLEAN), created_at, updated_at
    - messages (明细表): id(BIGINT PK AI), conversation_id(VARCHAR(64)), role(VARCHAR(16)), content(TEXT), citations(JSON), is_silent_fallback(BOOLEAN), created_at
    - 严格的数据隔离性: 基于 user_id 的行级隔离
    - 兼容别名: Message = ChatMessage, ChatSession = Conversation

架构定位:
    持久化数据模型层 (Data Models) / 模块四: AI 鉴权问答与智能工作台 (MySQL 8.0+)
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Conversation(Base):
    """
    智能问答会话主表实体 (conversations)
    """
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"conv-{uuid.uuid4().hex[:12]}",
        comment="会话全局唯一标识 UUID"
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        nullable=False,
        index=True,
        comment="归属员工用户 ID (多租户物理隔离键)"
    )
    title: Mapped[str] = mapped_column(
        String(128),
        default="新建智能问答",
        nullable=False,
        comment="会话显示标题"
    )
    message_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="当前会话累计消息数量"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="会话有效状态 (True 正常, False 软删除)"
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="软删除标记兼容字段"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="会话创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="会话最后活跃时间"
    )

    # 级联关系映射
    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ChatMessage.id.asc()",
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "message_count": self.message_count,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Conversation id='{self.id}' user_id={self.user_id} title='{self.title}'>"


class ChatMessage(Base):
    """
    智能问答消息明细表实体 (messages)
    """
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
        comment="消息自增主键 ID"
    )
    conversation_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属会话全局唯一 ID"
    )
    role: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        comment="消息角色: user / assistant / system"
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="对话正文"
    )
    citations: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON,
        default=list,
        nullable=True,
        comment="4D 知识切片溯源引用列表 (JSON)"
    )
    is_silent_fallback: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否触发了4D越权静默回退兜底"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="done",
        nullable=False,
        comment="消息状态: streaming | done | error"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="消息产生时间"
    )

    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="messages"
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "citations": self.citations or [],
            "is_silent_fallback": self.is_silent_fallback,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<Message id={self.id} role='{self.role}' conv_id='{self.conversation_id}'>"


# 兼容契约别名
Message = ChatMessage
ChatSession = Conversation


# ==============================================================================
# 底嵌自测闭环脚本 (Self-Test Execution Block)
# ==============================================================================
if __name__ == "__main__":
    import asyncio
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import StaticPool

    print("=== [Self-Test] Starting Chat Model Self-Test ===")

    async def _test_chat_models():
        test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool, echo=False)
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(bind=test_engine, expire_on_commit=False)

        async with session_factory() as session:
            # 1. 创建会话
            conv_id = f"conv-{uuid.uuid4().hex[:8]}"
            conv = Conversation(
                id=conv_id,
                user_id=1001,
                title="企业出差与差旅报销咨询",
                message_count=0,
                is_active=True,
            )
            session.add(conv)
            await session.commit()
            await session.refresh(conv)
            assert conv.id == conv_id
            assert conv.user_id == 1001
            assert conv.message_count == 0
            print(f"[Self-Test] Created Conversation: {conv}")

            # 2. 写入一问一答两条消息
            msg_user = Message(
                conversation_id=conv_id,
                role="user",
                content="请问国内出差每天的住宿上限是多少？",
            )
            msg_bot = Message(
                conversation_id=conv_id,
                role="assistant",
                content="根据企业差旅规范，一类城市每天上限为600元人民币。",
                citations=[{"chunk_id": 1, "unit_id": 10, "unit_title": "差旅制度.pdf", "score": 0.95}],
                is_silent_fallback=False,
            )
            session.add_all([msg_user, msg_bot])
            conv.message_count += 2
            await session.commit()

            # 3. 查询会话及级联消息
            stmt = select(Conversation).where(Conversation.id == conv_id)
            res = await session.execute(stmt)
            fetched_conv = res.scalar_one()
            assert fetched_conv.message_count == 2

            msg_stmt = select(Message).where(Message.conversation_id == conv_id).order_by(Message.id.asc())
            msgs = list((await session.execute(msg_stmt)).scalars().all())
            assert len(msgs) == 2
            assert msgs[0].role == "user"
            assert msgs[1].role == "assistant"
            assert len(msgs[1].citations) == 1
            print(f"[Self-Test] Loaded {len(msgs)} messages from conversation successfully")

            # 4. 测试级联物理清除
            await session.delete(fetched_conv)
            await session.commit()

            msgs_after = list((await session.execute(msg_stmt)).scalars().all())
            assert len(msgs_after) == 0
            print("[Self-Test] Cascade delete verified: deleting conversation purged all messages")

        await test_engine.dispose()
        print("=== [Self-Test] All Chat Model tests PASSED successfully! ===")

    asyncio.run(_test_chat_models())
