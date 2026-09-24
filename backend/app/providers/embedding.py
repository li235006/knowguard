"""
语义向量化嵌入提供商实现 (Embedding Provider)

职责:
    - 提供企业级文本向量计算 (如 BGE-M3 / OpenAI text-embedding-3-small)
    - 统一将文本映射为固定维度高精度浮点向量列表 (如 1536 维)

架构定位:
    模型适配层 (Model Providers) / 向量计算驱动

作者:
    System Architect (系统架构组)
"""

from typing import List
from app.providers.base import BaseEmbeddingProvider


class EmbeddingProvider(BaseEmbeddingProvider):
    """向量计算提供商实现存根"""

    async def get_embedding(self, text: str) -> List[float]:
        pass

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        pass
