/**
 * 运营监控大盘与全链路审计流水 API
 * 模块: FE-M6 / M6: Analytics
 * 原型对应: PAGE-07 (operations_analytics.pen)
 */

import request, { generateTraceId } from '@/utils/request'
import type { ApiResponse, PaginatedData, PaginationParams } from '@/types/common'
import type {
  DashboardSummary,
  TokenTrendPoint,
  LatencyBucket,
  TopRankingsResponse,
  AuditLogItem
} from '@/types/analytics'

const isMockEnabled = (): boolean => {
  return import.meta.env.VITE_ENABLE_MOCK === 'true'
}

// 预置原型 1:1 运营指标 Mock 数据
const liveMockSummary: DashboardSummary = {
  pv: 34280,
  uv: 2840,
  pv_uv_delta: '↑ 12.4% 较昨日',
  knowledge_units_count: 128,
  chunks_count: 1420,
  units_synced: 124,
  units_pending: 4,
  faq_cache_hit_rate: '41.8%',
  tokens_saved: '节约 8.4M Token',
  avg_latency_ms: 380,
  p95_latency_ms: 820,
  p99_latency: '1.2s',
  unresolved_gaps_count: 14,
  unresolved_gaps_delta: '↑ 3个 本周新增',
  published_faqs_count: 86
}

const liveMockTokenTrends: TokenTrendPoint[] = [
  { time: '00:00', prompt_tokens: 120000, completion_tokens: 45000, qps: 8 },
  { time: '06:00', prompt_tokens: 80000, completion_tokens: 30000, qps: 4 },
  { time: '09:00', prompt_tokens: 380000, completion_tokens: 140000, qps: 32 },
  { time: '12:00', prompt_tokens: 290000, completion_tokens: 110000, qps: 24 },
  { time: '15:00', prompt_tokens: 450000, completion_tokens: 180000, qps: 45 },
  { time: '18:00', prompt_tokens: 320000, completion_tokens: 130000, qps: 28 },
  { time: '20:00', prompt_tokens: 210000, completion_tokens: 90000, qps: 16 }
]

const liveMockLatencyDistribution: LatencyBucket[] = [
  { label: '< 50ms (FAQ直出)', percent: 41.8, count: 14328, sub_label: '极速缓存命中' },
  { label: '50-200ms (小切片)', percent: 22.4, count: 7678, sub_label: '精确索引匹配' },
  { label: '200-500ms (多跳)', percent: 18.2, count: 6238, sub_label: '混合重排解析' },
  { label: '500ms-1s (重排)', percent: 12.1, count: 4147, sub_label: '复杂语义召回' },
  { label: '> 1s (长上下文)', percent: 5.5, count: 1889, sub_label: '大模型推理消耗' }
]

const liveMockTopRankings: TopRankingsResponse = {
  top_queries: [
    { rank: 1, query: '差旅与住宿报销标准及额度', count: 142 },
    { rank: 2, query: '跨境清关关税与港口延误预警', count: 118 },
    { rank: 3, query: '年假与带薪病假折算规则', count: 96 },
    { rank: 4, query: '研发内网 VPN 与堡垒机权限', count: 84 },
    { rank: 5, query: '供应商准入资质与付款账期', count: 72 }
  ],
  top_knowledge: [
    { rank: 1, title: '《员工差旅与住宿报销管理规范》', count: 186 },
    { rank: 2, title: '《跨境电商出口清关与税务政策指南》', count: 145 },
    { rank: 3, title: '《企业考勤管理与法定假期实施办法》', count: 129 },
    { rank: 4, title: '《研发基础架构与内网安全访问指引》', count: 112 },
    { rank: 5, title: '《供应链采购流程与供应商管理办法》', count: 98 }
  ]
}

const liveMockAuditLogs: AuditLogItem[] = [
  {
    id: 1,
    trace_id: 'trace-kg-10086-q01',
    created_at: '2026-09-24 14:23:05',
    time: '14:23:05',
    user_id: 1001,
    username: '张三',
    dept_name: '市场营销部',
    role_name: '普通员工',
    client_endpoint: 'Web 问答工作台',
    query: '请告诉我副总裁级别的期权激励折算系数是多少？',
    recalled_count: 3,
    allowed_count: 2,
    restricted_count: 1,
    is_blocked: true,
    verdict_type: 'BLOCKED',
    verdict_badge_text: '阻断 1 (4D越权) · 放行 2',
    tokens: 1120,
    latency_ms: 380,
    silent_intercept_triggered: true,
    sha256_hash: '8f9a2b77c3e5d0124a9f9394bf34a8e29d749a2ef778bca64e89139589d4d1e',
    chunk_verdicts: [
      {
        chunk_id: 'Chunk-101',
        chunk_name: 'Chunk-101: 《财务审批权限管理办法》 4.2节',
        doc_code: 'KU-1001',
        doc_title: '财务审批权限管理办法.docx',
        status: 'ALLOWED',
        checks: {
          global_public: true,
          dept_matched: true,
          role_matched: true,
          user_matched: true
        }
      },
      {
        chunk_id: 'Chunk-102',
        chunk_name: 'Chunk-102: 《2024年度薪酬分配基本总则》',
        doc_code: 'KU-1003',
        doc_title: '2024年度薪酬分配基本总则.pdf',
        status: 'ALLOWED',
        checks: {
          global_public: true,
          dept_matched: true,
          role_matched: true,
          user_matched: true
        }
      },
      {
        chunk_id: 'Chunk-103',
        chunk_name: 'Chunk-103: 高管期权折算系数与特别激励授予条件',
        doc_code: 'KU-1002',
        doc_title: '集团核心高管中长期薪酬与股权激励细则.docx',
        status: 'BLOCKED',
        checks: {
          global_public: false,
          dept_matched: false,
          dept_actual: '市场营销部',
          dept_target: '人力资源中心',
          role_matched: false,
          role_actual: '普通员工',
          role_target: '核心高管/HRBP',
          user_matched: false
        },
        reason: 'UNAUTHORIZED_DEPARTMENT_AND_ROLE: 所属部门与角色均未在授权策略内'
      }
    ],
    waterfall: [
      { step_name: '网关鉴权与会话校验', latency_ms: 12 },
      { step_name: '向量混合检索召回', latency_ms: 85 },
      { step_name: '4D-RBAC 权限判定硬过滤', latency_ms: 18 },
      { step_name: 'LLM 安全脱敏流式生成', latency_ms: 265 }
    ]
  },
  {
    id: 2,
    trace_id: 'trace-kg-10085-q04',
    created_at: '2026-09-24 14:18:22',
    time: '14:18:22',
    user_id: 1002,
    username: '王浩',
    dept_name: '基础架构部',
    role_name: '研发工程师',
    client_endpoint: 'Web 问答工作台',
    query: 'Apollo 生产集群故障转移应急操作手册与主备切换规程',
    recalled_count: 4,
    allowed_count: 4,
    restricted_count: 0,
    is_blocked: false,
    verdict_type: 'ALLOWED',
    verdict_badge_text: '✓ 4D全部放行',
    tokens: 2450,
    latency_ms: 310,
    silent_intercept_triggered: false,
    sha256_hash: '3e41b9c79234857ef09a47120a4bcfd39589a10385920dae783459cba671b2ef',
    chunk_verdicts: [
      {
        chunk_id: 'Chunk-201',
        chunk_name: 'Chunk-201: Apollo 集群高可用部署拓扑架构',
        doc_code: 'KU-2001',
        doc_title: 'Apollo运维操作指引.md',
        status: 'ALLOWED',
        checks: {
          global_public: false,
          dept_matched: true,
          role_matched: true,
          user_matched: true
        }
      },
      {
        chunk_id: 'Chunk-202',
        chunk_name: 'Chunk-202: 主备机房故障检测与秒级自动切换流程',
        doc_code: 'KU-2001',
        doc_title: 'Apollo运维操作指引.md',
        status: 'ALLOWED',
        checks: {
          global_public: false,
          dept_matched: true,
          role_matched: true,
          user_matched: true
        }
      }
    ],
    waterfall: [
      { step_name: '网关鉴权与会话校验', latency_ms: 10 },
      { step_name: '向量混合检索召回', latency_ms: 68 },
      { step_name: '4D-RBAC 权限判定硬过滤', latency_ms: 14 },
      { step_name: 'LLM 安全脱敏流式生成', latency_ms: 218 }
    ]
  },
  {
    id: 3,
    trace_id: 'trace-kg-10084-q02',
    created_at: '2026-09-24 14:12:08',
    time: '14:12:08',
    user_id: 1003,
    username: '张雪',
    dept_name: '市场营销部',
    role_name: '设计专员',
    client_endpoint: 'Web 问答工作台',
    query: '2024 年度新版品牌 VI 配色标准及字体下载授权路径',
    recalled_count: 1,
    allowed_count: 1,
    restricted_count: 0,
    is_blocked: false,
    verdict_type: 'FAQ_HIT',
    verdict_badge_text: '⚡ FAQ 命中直出',
    tokens: 0,
    latency_ms: 32,
    silent_intercept_triggered: false,
    sha256_hash: '12a9bc45ef7834091a457cba385901239845efacbd783920148593aef475892c',
    waterfall: [
      { step_name: '网关鉴权与会话校验', latency_ms: 8 },
      { step_name: 'Redis 极速缓存匹配', latency_ms: 14 },
      { step_name: '直出格式化封装', latency_ms: 10 }
    ]
  },
  {
    id: 4,
    trace_id: 'trace-kg-10083-q09',
    created_at: '2026-09-24 14:05:40',
    time: '14:05:40',
    user_id: 1004,
    username: '陈明',
    dept_name: '跨境电商部',
    role_name: '物流专员',
    client_endpoint: '移动端服务助手',
    query: '东南亚跨境电商清关延误预警与港口集装箱调度标准',
    recalled_count: 5,
    allowed_count: 5,
    restricted_count: 0,
    is_blocked: false,
    verdict_type: 'ALLOWED',
    verdict_badge_text: '✓ 4D全部放行',
    tokens: 3120,
    latency_ms: 480,
    silent_intercept_triggered: false,
    sha256_hash: '908475aebc4512987fec45672398450123948571029384756102938475610293',
    waterfall: [
      { step_name: '网关鉴权与会话校验', latency_ms: 15 },
      { step_name: '向量混合检索召回', latency_ms: 95 },
      { step_name: '4D-RBAC 权限判定硬过滤', latency_ms: 20 },
      { step_name: 'LLM 安全脱敏流式生成', latency_ms: 350 }
    ]
  },
  {
    id: 5,
    trace_id: 'trace-kg-10082-q03',
    created_at: '2026-09-24 13:58:19',
    time: '13:58:19',
    user_id: 1005,
    username: '赵峰',
    dept_name: '人力资源中心',
    role_name: '招聘专员',
    client_endpoint: 'Web 问答工作台',
    query: '集团离职补偿金核算细则与核心期权回购标准方案',
    recalled_count: 3,
    allowed_count: 1,
    restricted_count: 2,
    is_blocked: true,
    verdict_type: 'BLOCKED',
    verdict_badge_text: '阻断 2 (部门/角色越权)',
    tokens: 890,
    latency_ms: 390,
    silent_intercept_triggered: true,
    sha256_hash: '67483920148593aef475892c12a9bc45ef7834091a457cba385901239845efac',
    chunk_verdicts: [
      {
        chunk_id: 'Chunk-301',
        chunk_name: 'Chunk-301: 法定解除劳动合同经济补偿金基数规定',
        doc_code: 'KU-3001',
        doc_title: '员工离职管理制度.pdf',
        status: 'ALLOWED',
        checks: {
          global_public: true,
          dept_matched: true,
          role_matched: true,
          user_matched: true
        }
      },
      {
        chunk_id: 'Chunk-302',
        chunk_name: 'Chunk-302: 期权未归属权益清算与回购定价特别条款',
        doc_code: 'KU-1002',
        doc_title: '集团核心高管中长期薪酬与股权激励细则.docx',
        status: 'BLOCKED',
        checks: {
          global_public: false,
          dept_matched: true,
          dept_actual: '人力资源中心',
          dept_target: '人力资源中心',
          role_matched: false,
          role_actual: '招聘专员',
          role_target: '薪酬绩效专家/HRD',
          user_matched: false
        },
        reason: 'UNAUTHORIZED_ROLE: 当前账号角色非薪酬绩效专家或HR总监'
      }
    ],
    waterfall: [
      { step_name: '网关鉴权与会话校验', latency_ms: 11 },
      { step_name: '向量混合检索召回', latency_ms: 78 },
      { step_name: '4D-RBAC 权限判定硬过滤', latency_ms: 21 },
      { step_name: 'LLM 安全脱敏流式生成', latency_ms: 280 }
    ]
  }
]

// 1. 获取核心 KPI 卡片汇总
export const getDashboardSummaryApi = async (): Promise<ApiResponse<DashboardSummary>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 80))
    return {
      code: 200,
      message: 'success',
      data: liveMockSummary,
      trace_id: generateTraceId()
    }
  }

  return request.get('/api/v1/analytics/dashboard-summary')
}

// 2. 获取 Token 消耗与 QPS 走势
export const getTokenTrendsApi = async (
  days: number = 7
): Promise<ApiResponse<TokenTrendPoint[]>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 100))
    return {
      code: 200,
      message: 'success',
      data: liveMockTokenTrends,
      trace_id: generateTraceId()
    }
  }

  return request.get('/api/v1/analytics/trends', { params: { days } })
}

// 3. 获取响应延时区间分布
export const getLatencyDistributionApi = async (): Promise<ApiResponse<LatencyBucket[]>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 80))
    return {
      code: 200,
      message: 'success',
      data: liveMockLatencyDistribution,
      trace_id: generateTraceId()
    }
  }

  return request.get('/api/v1/analytics/latency-distribution')
}

// 4. 获取 TOP 5 双榜单 (高频提问与热门知识)
export const getTopRankingsApi = async (): Promise<ApiResponse<TopRankingsResponse>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 90))
    return {
      code: 200,
      message: 'success',
      data: liveMockTopRankings,
      trace_id: generateTraceId()
    }
  }

  return request.get('/api/v1/analytics/top-rankings')
}

// 5. 分页查询安全审计流水日志
export const getAuditLogsApi = async (
  params: PaginationParams & { status?: string; search?: string; keyword?: string }
): Promise<ApiResponse<PaginatedData<AuditLogItem>>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 120))
    let filtered = [...liveMockAuditLogs]
    if (params.status && params.status !== 'ALL') {
      if (params.status === 'BLOCKED') {
        filtered = filtered.filter((i) => i.is_blocked)
      } else if (params.status === 'ALLOWED') {
        filtered = filtered.filter((i) => !i.is_blocked && i.verdict_type !== 'FAQ_HIT')
      } else if (params.status === 'FAQ_HIT') {
        filtered = filtered.filter((i) => i.verdict_type === 'FAQ_HIT')
      }
    }
    const kw = params.search || params.keyword
    if (kw && kw.trim()) {
      const q = kw.trim().toLowerCase()
      filtered = filtered.filter(
        (i) =>
          i.trace_id.toLowerCase().includes(q) ||
          i.query.toLowerCase().includes(q) ||
          i.username.toLowerCase().includes(q) ||
          i.dept_name.toLowerCase().includes(q)
      )
    }

    const page = params.page || 1
    const pageSize = params.page_size || 10
    const start = (page - 1) * pageSize
    const paginatedItems = filtered.slice(start, start + pageSize)
    return {
      code: 200,
      message: 'success',
      data: {
        items: paginatedItems,
        total: filtered.length,
        page,
        page_size: pageSize
      },
      trace_id: generateTraceId()
    }
  }

  const queryParams: Record<string, unknown> = {
    page: params.page || 1,
    page_size: params.page_size || 10
  }
  if (params.status && params.status !== 'ALL') queryParams.status = params.status
  const kw = params.search || params.keyword
  if (kw && kw.trim()) queryParams.keyword = kw.trim()

  return request.get('/api/v1/analytics/audit-logs', { params: queryParams })
}

// 6. 获取审计证据链详情
export const getAuditLogDetailApi = async (traceId: string): Promise<ApiResponse<AuditLogItem>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 80))
    const item = liveMockAuditLogs.find((i) => i.trace_id === traceId) || liveMockAuditLogs[0]
    return {
      code: 200,
      message: 'success',
      data: item,
      trace_id: generateTraceId()
    }
  }

  return request.get(`/api/v1/analytics/audit-logs/${traceId}`)
}
