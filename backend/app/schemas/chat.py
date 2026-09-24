"""
AI 鉴权智能问答与 SSE 流式事件数据契约 (Chat Schemas)

职责:
    - 问答请求模型 (会话ID、用户提问、多轮历史、模型偏好)
    - SSE 流式事件 Payload 模型 (delta, citation, silent_fallback, done)
    - 知识溯源引用卡片模型

架构定位:
    数据契约层 (Schemas) / 模块四: AI 鉴权问答与智能工作台

作者:
    System Architect (系统架构组)
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatCompletionRequest(BaseModel):
    """智能问答提问请求存根"""
    conversation_id: Optional[str] = None
    query: str = Field(..., min_length=1, description="用户提问内容")
    model: Optional[str] = None


class CitationItem(BaseModel):
    """知识溯源引用卡片存根"""
    chunk_id: int
    unit_id: int
    unit_title: str
    snippet: str
    score: float


class ChatEventPayload(BaseModel):
    """SSE 流式事件帧存根"""
    event: str  # text_delta | citation | warning | done
    data: Any
