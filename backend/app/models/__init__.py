"""
SQLAlchemy 2.0 ORM 持久化实体模型定义包

包含组织身份模型、知识单元与切片、4D 权限策略实体、多轮会话消息模型、FAQ 进化实体及全链路审计日志。
"""

from app.models.audit import AuditLog, ChatAuditLog
from app.models.base import BaseModel
from app.models.chat import Conversation, Message, ChatMessage
from app.models.evolution import FAQ, FAQCandidate, FAQItem, KnowledgeGap
from app.models.knowledge import KnowledgeChunk, KnowledgeUnit
from app.models.policy import PermissionPolicy
from app.models.user import Department, Role, User, UserRole

__all__ = [
    "BaseModel",
    "User",
    "Department",
    "Role",
    "UserRole",
    "KnowledgeUnit",
    "KnowledgeChunk",
    "PermissionPolicy",
    "Conversation",
    "Message",
    "ChatMessage",
    "FAQ",
    "FAQItem",
    "FAQCandidate",
    "KnowledgeGap",
    "AuditLog",
    "ChatAuditLog",
]

