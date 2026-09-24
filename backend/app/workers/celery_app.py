"""
Celery 实例初始化与 Broker 配置

职责:
    - 基于 Redis 初始化 Celery 异步任务应用实例
    - 配置任务序列化协议、结果过期时间及任务路由

架构定位:
    异步后台计算层 (Workers)

作者:
    System Architect (系统架构组)
"""

from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "knowguard_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
)
