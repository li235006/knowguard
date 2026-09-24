"""
运营监控、ECharts 走势与安全审计数据契约 (Analytics Schemas)

职责:
    - 大盘核心 KPI 汇总卡片响应模型 (PV/UV, Token, 响应耗时, 缓存命中率)
    - ECharts 趋势图数据序列模型 (双轴面积折线图、延时分布柱状图)
    - 问答全链路审计日志查询与受限明细响应模型

架构定位:
    数据契约层 (Schemas) / 模块六: 运营监控与审计大盘

作者:
    System Architect (系统架构组)
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DashboardSummaryResponse(BaseModel):
    """大盘核心 KPI 统计响应存根"""
    pass


class MetricTrendPoint(BaseModel):
    """ECharts 趋势走势数据点存根"""
    pass


class TopRankingItem(BaseModel):
    """排行榜数据项存根"""
    pass


class AuditLogResponse(BaseModel):
    """问答审计流水详情响应存根"""
    pass
