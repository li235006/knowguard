"""
Google Gemini 官方 SDK 接入适配器

职责:
    - 基于 google-genai 官方 SDK 接入 Gemini 2.5 Flash / Pro 大模型
    - 实现普通文本推理及 SSE 流式 Chunk 输出
    - 处理 API 速率限制 (RateLimit) 与重试退避

架构定位:
    模型适配层 (Model Providers) / Gemini 驱动

作者:
    System Architect (系统架构组)
"""

from typing import AsyncGenerator, Optional
from app.providers.base import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    """Gemini 模型适配器存根"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        pass

    async def stream_generate(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        pass
        yield
