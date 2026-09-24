"""
OpenAI / 标准 Compatible 格式大模型适配器

职责:
    - 基于 openai-python SDK 接入 GPT-4o / GPT-4o-mini 或第三方兼容服务 (如 DeepSeek, vLLM)
    - 支持标准流式与非流式调用

架构定位:
    模型适配层 (Model Providers) / OpenAI 兼容驱动

作者:
    System Architect (系统架构组)
"""

from typing import AsyncGenerator, Optional
from app.providers.base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """OpenAI 模型适配器存根"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        pass

    async def stream_generate(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        pass
        yield
