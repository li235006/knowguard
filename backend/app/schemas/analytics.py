"""
运营监控、ECharts 走势与安全审计数据契约 (Analytics Schemas)

职责:
    - 大盘核心 KPI 汇总卡片响应模型 (PV/UV, 切片总量, 已发布FAQ, 待处理缺口, 响应耗时, 缓存命中率)
    - ECharts 趋势图数据序列模型 (近7天 Token 双轴、延时趋势)
    - 高频提问 TOP 5 与热门知识 TOP 5 榜单响应模型
    - 问答全链路审计日志查询与受限明细证据链下钻模型

架构定位:
    数据契约层 (Schemas) / 模块六: 运营监控与审计大盘

作者:
    System Architect (系统架构组) & Backend Team
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class DashboardSummaryResponse(BaseModel):
    """大盘 5 大核心 KPI 统计汇总响应"""
    model_config = ConfigDict(from_attributes=True)

    pv: int = Field(default=0, description="页面/提问总访问量 (Page Views)")
    uv: int = Field(default=0, description="独立访问用户数 (Unique Visitors)")
    chunks_count: int = Field(default=0, description="知识切片总量")
    total_chunks: Optional[int] = Field(default=None, description="知识切片总量 (别名)")
    knowledge_units_count: int = Field(default=0, description="知识文档/单元总量")
    published_faqs: int = Field(default=0, description="已采纳发布的标准 FAQ 总数")
    faqs_count: Optional[int] = Field(default=None, description="已发布 FAQ 总数 (别名)")
    open_gaps: int = Field(default=0, description="待处理知识缺口盲区总数")
    pending_gaps: Optional[int] = Field(default=None, description="待处理缺口 (别名)")
    knowledge_gaps_count: Optional[int] = Field(default=None, description="知识缺口总数 (别名)")
    faq_cache_hit_rate: float = Field(default=0.0, description="FAQ 极速缓存直出命中率百分比 (0.0~100.0)")
    avg_latency_ms: float = Field(default=0.0, description="端到端平均响应耗时 (ms)")
    total_tokens: int = Field(default=0, description="累计消耗 Token 总数")
    pv_uv_delta: Optional[str] = Field(default="0% 较昨日", description="PV/UV环比增量标签")
    units_synced: Optional[int] = Field(default=0, description="已同步知识单元数")
    units_pending: Optional[int] = Field(default=0, description="待更新知识单元数")
    tokens_saved: Optional[str] = Field(default="节约 0 Token", description="节约Token数描述")
    p95_latency_ms: Optional[float] = Field(default=0.0, description="P95响应延时")
    p99_latency: Optional[str] = Field(default="0ms", description="P99响应延时")
    unresolved_gaps_count: Optional[int] = Field(default=0, description="待闭环知识缺口")
    unresolved_gaps_delta: Optional[str] = Field(default="0个 本周新增", description="待闭环缺口增量")

    @model_validator(mode="after")
    def sync_aliases(self) -> "DashboardSummaryResponse":
        if self.total_chunks is None:
            self.total_chunks = self.chunks_count
        elif self.chunks_count is None:
            self.chunks_count = self.total_chunks

        if self.faqs_count is None:
            self.faqs_count = self.published_faqs
        elif self.published_faqs is None:
            self.published_faqs = self.faqs_count

        if self.pending_gaps is None:
            self.pending_gaps = self.open_gaps
        if self.knowledge_gaps_count is None:
            self.knowledge_gaps_count = self.open_gaps
        if self.unresolved_gaps_count is None or self.unresolved_gaps_count == 0:
            self.unresolved_gaps_count = self.open_gaps
        return self


# 别名兼容
DashboardSummary = DashboardSummaryResponse


class LatencyBucketResponse(BaseModel):
    """端到端响应耗时区间统计模型 (适配 ECharts/前端柱状图)"""
    label: str = Field(..., description="延时区间标签，如 < 50ms (FAQ直出)")
    percent: float = Field(default=0.0, description="占比百分比 (0.0~100.0)")
    count: int = Field(default=0, description="该区间命中日志条数")
    sub_label: Optional[str] = Field(default=None, description="子标签说明")


class TrendPoint(BaseModel):
    """每日 Token 消耗与延时趋势走势数据点"""
    date: str = Field(..., description="日期 (YYYY-MM-DD)")
    time: Optional[str] = Field(default=None, description="时间标签 (如 MM-DD 或 HH:MM)")
    prompt_tokens: int = Field(default=0, description="输入 Prompt Tokens")
    completion_tokens: int = Field(default=0, description="输出 Completion Tokens")
    total_tokens: int = Field(default=0, description="当日消耗 Token 总量")
    latency_ms: float = Field(default=0.0, description="当日平均延时毫秒")
    avg_latency_ms: Optional[float] = Field(default=None, description="当日平均延时 (别名)")
    pv: int = Field(default=0, description="当日提问量")
    qps: Optional[float] = Field(default=0.0, description="当日峰值 QPS (次/秒)")

    @model_validator(mode="after")
    def sync_latency(self) -> "TrendPoint":
        if self.avg_latency_ms is None:
            self.avg_latency_ms = self.latency_ms
        elif self.latency_ms == 0.0 and self.avg_latency_ms is not None:
            self.latency_ms = self.avg_latency_ms
        if not self.time and self.date:
            self.time = self.date[5:] if len(self.date) >= 10 else self.date
        return self


# 别名兼容
MetricTrendPoint = TrendPoint


class TopRankingItem(BaseModel):
    """排行榜数据项 (高频提问 TOP / 热门知识引用 TOP)"""
    title: str = Field(..., description="榜单项目名称/提问文本/文档标题")
    query: Optional[str] = Field(default=None, description="提问文本 (别名)")
    count: int = Field(..., description="频次/引用热度/命中次数")
    hit_count: Optional[int] = Field(default=None, description="频次 (别名)")
    rank: Optional[int] = Field(default=1, description="排名次序 (1~5)")

    @model_validator(mode="after")
    def sync_aliases(self) -> "TopRankingItem":
        if not self.query and self.title:
            self.query = self.title
        if self.hit_count is None:
            self.hit_count = self.count
        return self


class TopRankingsResponse(BaseModel):
    """双维度 TOP 5 榜单聚合响应"""
    top_queries: List[TopRankingItem] = Field(default_factory=list, description="高频提问 TOP 5")
    top_knowledge: List[TopRankingItem] = Field(default_factory=list, description="热门知识/切片引用 TOP 5")
    items: Optional[List[TopRankingItem]] = Field(default=None, description="通用项列表")

    @model_validator(mode="after")
    def sync_items(self) -> "TopRankingsResponse":
        if self.items is None:
            self.items = list(self.top_queries)
        return self


class AuditLogResponse(BaseModel):
    """全链路安全审计日志详情响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="审计记录主键ID")
    trace_id: str = Field(..., description="全链路唯一追踪号 X-Trace-Id")
    conversation_id: Optional[str] = Field(default=None, description="会话ID")
    user_id: Optional[int] = Field(default=None, description="提问员工ID")
    username: Optional[str] = Field(default=None, description="员工登录账号/姓名")
    employee_id: Optional[str] = Field(default=None, description="员工工号")
    user_dept: Optional[str] = Field(default=None, description="所属部门")
    user_role: Optional[str] = Field(default=None, description="所属角色")
    dept_name: Optional[str] = Field(default=None, description="所属部门 (别名)")
    role_name: Optional[str] = Field(default=None, description="所属角色 (别名)")
    query_text: str = Field(..., description="用户提问内容")
    query: Optional[str] = Field(default=None, description="用户提问内容 (别名)")
    answer_snippet: Optional[str] = Field(default=None, description="答复摘要或兜底提示")
    recalled_chunk_ids: List[int] = Field(default_factory=list, description="向量检索初筛召回切片ID清单")
    recalled_count: int = Field(default=0, description="初筛召回切片总数")
    allowed_chunk_ids: List[int] = Field(default_factory=list, description="4D安全放行切片ID清单")
    allowed_count: int = Field(default=0, description="安全放行切片数")
    restricted_chunk_ids: List[int] = Field(default_factory=list, description="4D安全隔离/越权拦截受限切片ID清单")
    restricted_count: int = Field(default=0, description="受限切片数")
    is_blocked: bool = Field(default=False, description="是否触发拦截/受限隔离/静默回退")
    block_reason: Optional[str] = Field(default=None, description="拦截/受限成因")
    prompt_tokens: int = Field(default=0, description="输入消耗 Tokens")
    completion_tokens: int = Field(default=0, description="输出消耗 Tokens")
    total_tokens: int = Field(default=0, description="总消耗 Tokens")
    tokens: Optional[int] = Field(default=None, description="总消耗 Tokens (别名)")
    latency_ms: float = Field(default=0.0, description="调用处理耗时 (ms)")
    created_at: Optional[datetime] = Field(default=None, description="记录发生时间")
    time: Optional[str] = Field(default=None, description="格式化时间字符串")
    verdict_type: Optional[str] = Field(default=None, description="安全裁决类型 (BLOCKED/ALLOWED/FAQ_HIT)")
    verdict_badge_text: Optional[str] = Field(default=None, description="安全裁决徽章文案")
    sha256_hash: Optional[str] = Field(default=None, description="存证哈希指纹")
    silent_intercept_triggered: Optional[bool] = Field(default=False, description="是否触发静默防越权脱敏")
    evidence_chain: Optional[Dict[str, Any]] = Field(default=None, description="完整下钻安全证据链明细")

    @model_validator(mode="after")
    def sync_query(self) -> "AuditLogResponse":
        if not self.query and self.query_text:
            self.query = self.query_text
        elif not self.query_text and self.query:
            self.query_text = self.query

        if not self.dept_name and self.user_dept:
            self.dept_name = self.user_dept
        if not self.role_name and self.user_role:
            self.role_name = self.user_role

        if self.tokens is None:
            self.tokens = self.total_tokens

        if not self.time and self.created_at:
            self.time = self.created_at.strftime("%H:%M:%S")

        if not self.verdict_type:
            if self.is_blocked:
                self.verdict_type = "BLOCKED"
                self.verdict_badge_text = f"阻断 {self.restricted_count} (4D越权)"
                self.silent_intercept_triggered = True
            elif self.latency_ms < 50 and not self.recalled_chunk_ids:
                self.verdict_type = "FAQ_HIT"
                self.verdict_badge_text = "⚡ FAQ 命中直出"
            else:
                self.verdict_type = "ALLOWED"
                self.verdict_badge_text = "✓ 4D全部放行"

        if not self.sha256_hash and self.trace_id:
            import hashlib
            self.sha256_hash = hashlib.sha256(f"{self.trace_id}_{self.id}".encode()).hexdigest()
        return self


# 别名兼容
AuditLogItem = AuditLogResponse


class EvidenceChainDetailResponse(BaseModel):
    """拦截证据链下钻详情响应"""
    trace_id: str = Field(..., description="追踪号")
    query: str = Field(..., description="提问内容")
    user_context: Dict[str, Any] = Field(default_factory=dict, description="提问用户4D属性上下文")
    recalled_chunks: List[Dict[str, Any]] = Field(default_factory=list, description="初筛召回切片明细")
    allowed_chunks: List[Dict[str, Any]] = Field(default_factory=list, description="放行切片明细")
    restricted_chunks: List[Dict[str, Any]] = Field(default_factory=list, description="拦截受限切片证据链")
    decision: Dict[str, Any] = Field(default_factory=dict, description="安全裁决裁定结论")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="算力与延时耗时分析")
