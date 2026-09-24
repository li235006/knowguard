"""
全链路穿透式问答审计流水实体模型 (ChatAuditLog)

职责:
    - 留存每一次智能问答交互的完整安全审计证据链
    - 记录: X-Trace-Id、提问员工工号/姓名、会话 ID、用户输入文本
    - 记录安全裁决明细: 召回切片候选集、4D 放行切片集、4D 拦截受限切片集
    - 记录算力指标: Prompt Tokens、Completion Tokens、总延时毫秒、拦截原因

架构定位:
    持久化数据模型层 (Data Models) / 模块六: 运营监控与审计大盘 (MySQL 8.0+)

作者:
    System Architect (系统架构组)
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class ChatAuditLog(BaseModel):
    """问答安全审计流水实体存根 (MySQL 8.0+)"""
    __tablename__ = "chat_audit_logs"
    pass
