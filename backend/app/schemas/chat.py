"""
AI 鉴权智能问答与 SSE 流式事件数据契约 (Chat Schemas)

职责:
    - 问答请求模型 (会话ID、用户提问、多轮历史、模型偏好)
    - SSE 流式事件 Payload 模型 (text_delta, citation, warning, done)
    - 知识溯源引用卡片模型 (CitationItem)
    - 提供标准化 SSE 帧编码方法 (to_sse_line)

架构定位:
    数据契约层 (Schemas) / 模块四: AI 鉴权问答与智能工作台

作者:
    System Architect (系统架构组) & Backend Team
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatCompletionRequest(BaseModel):
    """智能问答提问请求模型"""
    conversation_id: Optional[str] = Field(None, description="会话唯一标识 UUID")
    query: str = Field(..., min_length=1, description="用户提问内容")
    model: Optional[str] = Field("qwen-plus", description="偏好模型名称")


class ConversationCreateRequest(BaseModel):
    """新建会话请求"""
    title: Optional[str] = Field("新建智能问答", description="会话标题")


class ConversationResponse(BaseModel):
    """会话摘要响应模型"""
    id: str = Field(..., description="会话唯一标识")
    title: str = Field(..., description="会话标题")
    created_at: str = Field(..., description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")
    message_count: Optional[int] = Field(0, description="消息总数")


class MessageResponse(BaseModel):
    """问答单条消息响应模型"""
    id: str = Field(..., description="消息唯一标识")
    conversation_id: str = Field(..., description="会话标识")
    role: str = Field(..., description="角色: user | assistant")
    content: str = Field(..., description="消息正文")
    citations: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="溯源引用")
    is_silent_fallback: Optional[bool] = Field(False, description="是否静默降级")
    created_at: str = Field(..., description="时间戳")
    status: Optional[str] = Field("done", description="状态: streaming | done | error")


class CitationItem(BaseModel):
    """知识溯源引用卡片数据模型"""
    chunk_id: int = Field(..., description="切片 ID")
    unit_id: int = Field(..., description="所属知识单元 ID")
    unit_title: str = Field(..., description="知识单元标题")
    snippet: str = Field(..., description="切片摘要正文")
    score: float = Field(default=0.0, description="语义重排相关度分数")


class TextDeltaEventData(BaseModel):
    """文本增量事件数据"""
    delta: str = Field(..., description="打字机增量字符片段")
    is_faq: Optional[bool] = Field(default=False, description="是否来自 FAQ 极速直出")


class WarningEventData(BaseModel):
    """安全警告与隔离事件数据"""
    type: str = Field(default="PERMISSION_ISOLATION", description="警告类型")
    message: str = Field(..., description="隔离提示文案")


class DoneEventData(BaseModel):
    """问答完成帧数据"""
    conversation_id: str = Field(..., description="会话 ID")
    trace_id: str = Field(..., description="链路追踪 ID")
    total_tokens: Optional[int] = Field(0, description="消耗 Token 预估")
    is_silent_fallback: Optional[bool] = Field(default=False, description="是否静默降级")
    is_faq_hit: Optional[bool] = Field(default=False, description="是否命中标准 FAQ 极速缓存直出")
    hit_faq: Optional[bool] = Field(default=False, description="是否命中标准 FAQ 极速缓存直出 (别名)")
    faq_id: Optional[int] = Field(default=None, description="命中的 FAQ ID")
    llm_source: Optional[str] = Field(default="remote_dashscope", description="LLM执行来源")
    llm_model: Optional[str] = Field(default="qwen3.7-flash", description="LLM模型名称")
    is_real_llm: Optional[bool] = Field(default=True, description="是否为真实云端LLM调用")


class ChatEventPayload(BaseModel):
    """SSE 流式事件帧统一模型"""
    event: str = Field(..., description="事件类型: text_delta | citation | warning | done")
    data: Any = Field(..., description="事件数据载荷")

    def to_sse_line(self) -> str:
        """编码为标准 SSE 数据传输帧 (event: ...\ndata: ...\n\n)"""
        data_val = self.data
        if hasattr(data_val, "model_dump"):
            data_val = data_val.model_dump()
        json_str = json.dumps(data_val, ensure_ascii=False)
        return f"event: {self.event}\ndata: {json_str}\n\n"


# ==============================================================================
# 底嵌自测闭环脚本 (Self-Test Execution Block)
# ==============================================================================
if __name__ == "__main__":
    print("=== [Self-Test] Starting Chat Schemas Self-Test ===")

    # 1. 验证 ChatCompletionRequest
    req = ChatCompletionRequest(query="公司差旅补贴标准是多少？")
    assert req.query == "公司差旅补贴标准是多少？"
    assert req.model == "qwen-plus"
    print(f"[Self-Test] ChatCompletionRequest validated: query='{req.query}'")

    # 2. 验证 CitationItem
    cit = CitationItem(
        chunk_id=101,
        unit_id=1,
        unit_title="差旅规范.pdf",
        snippet="住宿标准为每天500元...",
        score=0.925
    )
    assert cit.score == 0.925
    print(f"[Self-Test] CitationItem validated: title='{cit.unit_title}'")

    # 3. 验证 SSE 格式化 (to_sse_line)
    ev_delta = ChatEventPayload(event="text_delta", data={"delta": "根据知识库规定"})
    raw_delta = ev_delta.to_sse_line()
    assert raw_delta.startswith("event: text_delta\ndata: ")
    assert raw_delta.endswith("\n\n")

    ev_done = ChatEventPayload(event="done", data={"conversation_id": "c-123", "trace_id": "t-456"})
    raw_done = ev_done.to_sse_line()
    assert "event: done" in raw_done

    print("=== [Self-Test] All Chat Schemas tests PASSED successfully! ===")
