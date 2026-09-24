"""
系统全局强类型配置管理模块

职责:
    - 基于 pydantic-settings 加载并验证系统环境变量 (.env)
    - 提供应用配置、MySQL 数据库连接、Milvus 向量库、MongoDB 文档库、Redis 缓存、Celery 队列及模型提供商参数的单例对象

架构定位:
    核心底层支撑层 (Core Infrastructure)

输入/输出契约:
    - 输入: .env 文件或系统操作系统环境变量
    - 输出: Settings 强类型配置实例

作者:
    System Architect (系统架构组)
"""

import json
from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """系统全局配置模型存根"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # 基础应用配置
    APP_NAME: str = "KnowGuard"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    # 服务网络与跨域配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    # 关系型数据库配置 - MySQL 8.0+
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "knowguard"
    DATABASE_URL: str = "mysql+aiomysql://root:password@localhost:3306/knowguard?charset=utf8mb4"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False

    # 向量数据库配置 - Milvus 2.4+ (Linux VM Docker: 192.168.6.134)
    MILVUS_HOST: str = "192.168.6.134"
    MILVUS_PORT: int = 19530
    MILVUS_USER: str = ""
    MILVUS_PASSWORD: str = ""
    MILVUS_COLLECTION_NAME: str = "knowguard_chunks"
    MILVUS_DIMENSION: int = 1024
    MILVUS_METRIC_TYPE: str = "COSINE"
    MILVUS_INDEX_TYPE: str = "HNSW"

    # 文档型数据库配置 - MongoDB 7.0+ (Linux VM Docker: 192.168.6.134)
    MONGODB_URL: str = "mongodb://192.168.6.134:27017"
    MONGODB_DATABASE: str = "knowguard"

    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50

    # Celery 异步任务队列配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # 安全与 JWT 配置
    SECRET_KEY: str = "default-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 对象存储 (MinIO / S3) 配置 (Linux VM Docker: 192.168.6.134)
    MINIO_ENDPOINT: str = "192.168.6.134:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "knowguard-documents"
    MINIO_SECURE: bool = False

    # 大语言模型适配层 - 通义千问 (Qwen / DashScope)
    DASHSCOPE_API_KEY: Optional[str] = None
    QWEN_MODEL_NAME: str = "qwen-plus"
    QWEN_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    DEFAULT_LLM_PROVIDER: str = "qwen"

    # 本地向量与重排序模型 - BGE 系列
    EMBEDDING_PROVIDER: str = "local_bge_m3"
    EMBEDDING_MODEL_PATH: str = "BAAI/bge-m3"
    EMBEDDING_DIMENSION: int = 1024
    RERANKER_PROVIDER: str = "local_bge_reranker"
    RERANKER_MODEL_PATH: str = "BAAI/bge-reranker-large"

    # 可选辅助模型
    GEMINI_API_KEY: Optional[str] = None

    # OpenTelemetry 链路追踪配置
    OTEL_ENABLED: bool = False
    OTEL_SERVICE_NAME: str = "knowguard-backend"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"


settings = Settings()
