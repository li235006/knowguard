/**
 * 运营监控大盘与审计流水契约 (Analytics DTO)
 * 原型对应: PAGE-07 (operations_analytics.pen)
 * 镜像对齐: backend/app/schemas/analytics.py
 */

export interface DashboardSummary {
  // KPI 1: 今日总访问 PV / UV
  pv: number
  uv: number
  pv_uv_delta: string

  // KPI 2: 知识单元总资产与切片总量
  knowledge_units_count: number
  chunks_count: number
  units_synced: number
  units_pending: number

  // KPI 3: FAQ 缓存直出率
  faq_cache_hit_rate: string | number
  tokens_saved: string

  // KPI 4: 端到端平均延迟
  avg_latency_ms: number
  p95_latency_ms: number
  p99_latency: string

  // KPI 5: 待闭环知识缺口
  unresolved_gaps_count: number
  unresolved_gaps_delta: string
  published_faqs_count: number
}

export interface TokenTrendPoint {
  time?: string
  date?: string
  prompt_tokens: number
  completion_tokens: number
  qps?: number
  pv?: number
  total_tokens?: number
  latency_ms?: number
}

export interface LatencyBucket {
  label: string
  percent: number
  count?: number
  sub_label?: string
}

export interface TopQueryItem {
  rank: number
  query: string
  count: number
}

export interface TopKnowledgeItem {
  rank: number
  title: string
  count: number
}

export interface TopRankingsResponse {
  top_queries: TopQueryItem[]
  top_knowledge: TopKnowledgeItem[]
}

export interface ChunkVerdict {
  chunk_id: string | number
  chunk_name: string
  doc_code?: string
  doc_title?: string
  status: 'ALLOWED' | 'BLOCKED'
  checks: {
    global_public: boolean
    dept_matched: boolean
    dept_actual?: string
    dept_target?: string
    role_matched: boolean
    role_actual?: string
    role_target?: string
    user_matched: boolean
  }
  reason?: string
}

export interface LatencyWaterfallStep {
  step_name: string
  latency_ms: number
}

export interface AuditLogItem {
  id: number
  trace_id: string
  created_at: string
  time?: string
  user_id: number
  username: string
  dept_name: string
  role_name: string
  client_endpoint: string
  query: string
  recalled_count: number
  allowed_count: number
  restricted_count: number
  is_blocked: boolean
  verdict_type: 'BLOCKED' | 'ALLOWED' | 'FAQ_HIT'
  verdict_badge_text: string
  tokens: number
  latency_ms: number
  silent_intercept_triggered: boolean
  sha256_hash: string
  chunk_verdicts?: ChunkVerdict[]
  waterfall?: LatencyWaterfallStep[]
}
