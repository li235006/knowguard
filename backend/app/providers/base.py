"""
外部大模型与向量服务抽象基类契约 (Base Model Provider)

职责:
    - 定义 LLM 文本补全与异步生成抽象接口 (BaseLLMProvider)
    - 定义 SSE 流式文本生成抽象接口 (stream_generate)
    - 定义文本向量嵌入抽象接口 (BaseEmbeddingProvider)

架构定位:
    模型适配层 (Model Providers) / 契约基底

作者:
    System Architect (系统架构组)
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Optional


class BaseLLMProvider(ABC):
    """LLM 提供商抽象接口存根"""

    @abstractmethod
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """非流式单次文本生成存根"""
        pass

    @abstractmethod
    async def stream_generate(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """SSE 打字机流式文本生成存根"""
        pass
        yield


class BaseEmbeddingProvider(ABC):
    """Embedding 提供商抽象接口存根"""

    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """单文本向量化计算存根"""
        pass

    @abstractmethod
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """批量文本向量化计算存根"""
        pass
