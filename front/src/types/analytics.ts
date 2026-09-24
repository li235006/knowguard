/**
 * 运营监控大盘与审计流水契约 (Analytics DTO)
 * 镜像对齐: backend/app/schemas/analytics.py
 */

export interface DashboardSummary {
  pv: number
  uv: number
  knowledge_units_count: number
  faq_cache_hit_rate: number
  avg_latency_ms: number
}

export interface TrendPoint {
  date: string
  prompt_tokens: number
  completion_tokens: number
  latency_ms: number
}

export interface TopRankingItem {
  title: string
  count: number
}

export interface AuditLogItem {
  trace_id: string
  user_id: number
  username: string
  query: string
  recalled_count: number
  allowed_count: number
  restricted_count: number
  is_blocked: boolean
  latency_ms: number
  created_at: string
}
