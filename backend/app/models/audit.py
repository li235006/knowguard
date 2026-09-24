"""
全链路穿透式问答安全审计流水实体模型 (AuditLog & ChatAuditLog)

职责:
    - 留存每一次智能问答交互的完整安全审计证据链
    - 严格对齐 MVP 8.3 节数据表规范: audit_logs
    - 记录: trace_id, conversation_id, user_id, user_real_name, dept_name, question
    - 记录安全裁决明细: retrieved_chunk_ids, authorized_chunk_ids, blocked_chunk_ids, is_intercepted
    - 记录算力与性能指标: tokens, latency_ms, evidence_chain

架构定位:
    持久化数据模型层 (Data Models) / 模块六: 运营监控与审计大盘 (MySQL 8.0+)

作者:
    System Architect (系统架构组) & Backend Team
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class AuditBaseModel(Base):
    """审计模型通用审计基类 (避免模块循环导入)"""
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)


class AuditLog(AuditBaseModel):
    """
    问答安全审计流水实体 (表名: audit_logs, 严格对齐 MVP 8.3 节)
    """
    __tablename__ = "audit_logs"
    __table_args__ = {"extend_existing": True}

    trace_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="全链路调用追踪号")
    conversation_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True, comment="关联会话ID")
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True, comment="提问用户员工ID")
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="员工登录名/真实姓名")
    employee_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="员工工号")
    user_dept: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="归属部门名称")
    user_role: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="用户角色名称")

    query_text: Mapped[str] = mapped_column(Text, nullable=False, comment="提问内容")
    answer_snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="答复摘要")

    recalled_chunk_ids: Mapped[List[int]] = mapped_column(JSON, default=list, comment="召回切片ID列表")
    recalled_count: Mapped[int] = mapped_column(Integer, default=0, comment="召回切片数")

    allowed_chunk_ids: Mapped[List[int]] = mapped_column(JSON, default=list, comment="4D安全放行切片ID列表")
    allowed_count: Mapped[int] = mapped_column(Integer, default=0, comment="放行切片数")

    restricted_chunk_ids: Mapped[List[int]] = mapped_column(JSON, default=list, comment="4D安全拦截受限切片ID列表")
    restricted_count: Mapped[int] = mapped_column(Integer, default=0, comment="受限切片数")

    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, index=True, comment="是否触发越权拦截")
    block_reason: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="拦截原因")

    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, comment="Prompt Token 消耗")
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, comment="Completion Token 消耗")
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, comment="总 Token 消耗")
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0, comment="全链路响应延迟 (ms)")

    evidence_chain: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, comment="下钻证据链明细")

    # ==================== MVP 8.3 属性别名映射 ====================
    @property
    def question(self) -> str:
        return self.query_text

    @question.setter
    def question(self, val: str):
        self.query_text = val

    @property
    def query(self) -> str:
        return self.query_text

    @query.setter
    def query(self, val: str):
        self.query_text = val

    @property
    def user_real_name(self) -> Optional[str]:
        return self.username

    @user_real_name.setter
    def user_real_name(self, val: Optional[str]):
        self.username = val

    @property
    def dept_name(self) -> Optional[str]:
        return self.user_dept

    @dept_name.setter
    def dept_name(self, val: Optional[str]):
        self.user_dept = val

    @property
    def retrieved_chunk_ids(self) -> List[int]:
        return self.recalled_chunk_ids

    @retrieved_chunk_ids.setter
    def retrieved_chunk_ids(self, val: List[int]):
        self.recalled_chunk_ids = val

    @property
    def authorized_chunk_ids(self) -> List[int]:
        return self.allowed_chunk_ids

    @authorized_chunk_ids.setter
    def authorized_chunk_ids(self, val: List[int]):
        self.allowed_chunk_ids = val

    @property
    def blocked_chunk_ids(self) -> List[int]:
        return self.restricted_chunk_ids

    @blocked_chunk_ids.setter
    def blocked_chunk_ids(self, val: List[int]):
        self.restricted_chunk_ids = val

    @property
    def is_intercepted(self) -> bool:
        return self.is_blocked

    @is_intercepted.setter
    def is_intercepted(self, val: bool):
        self.is_blocked = val

    @property
    def tokens(self) -> int:
        return self.total_tokens

    @tokens.setter
    def tokens(self, val: int):
        self.total_tokens = val


# 兼容历史别名
ChatAuditLog = AuditLog


if __name__ == "__main__":
    print("=== [Self-Test] Starting Audit Models Self-Test ===")
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    test_engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        log = AuditLog(
            trace_id="tr-test-audit-8899",
            conversation_id="conv-audit-01",
            user_id=10086,
            user_real_name="张三",
            dept_name="研发部",
            question="高管期权分配细则是什么？",
            retrieved_chunk_ids=[101, 102, 103],
            authorized_chunk_ids=[101],
            blocked_chunk_ids=[102, 103],
            is_intercepted=True,
            tokens=450,
            latency_ms=280.5,
        )
        session.add(log)
        session.flush()

        assert log.id is not None
        assert log.__tablename__ == "audit_logs"
        assert log.question == "高管期权分配细则是什么？"
        assert log.query == "高管期权分配细则是什么？"
        assert log.user_real_name == "张三"
        assert log.dept_name == "研发部"
        assert log.is_intercepted is True
        assert log.tokens == 450
        assert log.retrieved_chunk_ids == [101, 102, 103]
        assert log.authorized_chunk_ids == [101]
        assert log.blocked_chunk_ids == [102, 103]
        print(f"[Self-Test] AuditLog created: ID={log.id}, table={log.__tablename__}, is_intercepted={log.is_intercepted}")

        # 别名兼容断言
        assert isinstance(log, ChatAuditLog)
        assert log.username == "张三"
        assert log.user_dept == "研发部"
        assert log.query_text == "高管期权分配细则是什么？"
        assert log.is_blocked is True
        assert log.total_tokens == 450
        print("[Self-Test] ChatAuditLog aliases verified successfully.")

    test_engine.dispose()
    print("=== [Self-Test] All Audit Models tests PASSED successfully! ===")
