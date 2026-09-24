/**
 * 运营监控大盘状态仓库 (Analytics Store)
 * 模块: FE-M6 / PAGE-07
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import type {
  DashboardSummary,
  TokenTrendPoint,
  LatencyBucket,
  TopRankingsResponse,
  AuditLogItem
} from '@/types/analytics'
import {
  getDashboardSummaryApi,
  getTokenTrendsApi,
  getLatencyDistributionApi,
  getTopRankingsApi,
  getAuditLogsApi,
  getAuditLogDetailApi
} from '@/api/analytics'

export const useAnalyticsStore = defineStore('analytics', () => {
  // 5 大核心 KPI 概览指标
  const summary = ref<DashboardSummary>({
    pv: 0,
    uv: 0,
    pv_uv_delta: '0% 较昨日',
    knowledge_units_count: 0,
    chunks_count: 0,
    units_synced: 0,
    units_pending: 0,
    faq_cache_hit_rate: '0.0%',
    tokens_saved: '0 Token',
    avg_latency_ms: 0,
    p95_latency_ms: 0,
    p99_latency: '0ms',
    unresolved_gaps_count: 0,
    unresolved_gaps_delta: '0个 本周新增',
    published_faqs_count: 0
  })

  // ECharts 图表数据
  const tokenTrends = ref<TokenTrendPoint[]>([])
  const latencyDistribution = ref<LatencyBucket[]>([])

  // TOP 5 榜单数据
  const topRankings = ref<TopRankingsResponse>({
    top_queries: [],
    top_knowledge: []
  })

  // 审计流水表格数据
  const auditLogs = ref<AuditLogItem[]>([])
  const totalAuditLogs = ref<number>(0)
  const auditPage = ref<number>(1)
  const auditPageSize = ref<number>(10)
  const auditStatusFilter = ref<string>('ALL') // ALL / BLOCKED / ALLOWED / FAQ_HIT
  const auditSearchKeyword = ref<string>('')

  // 加载状态
  const isLoadingSummary = ref<boolean>(false)
  const isLoadingCharts = ref<boolean>(false)
  const isLoadingAudit = ref<boolean>(false)

  // 审计证据链抽屉
  const selectedLogForDetail = ref<AuditLogItem | null>(null)
  const showDetailDrawer = ref<boolean>(false)

  // 1. 获取 5 大核心 KPI 指标
  const fetchSummary = async () => {
    isLoadingSummary.value = true
    try {
      const res = await getDashboardSummaryApi()
      if (res && res.data) {
        summary.value = res.data
      }
    } catch {
      // 保持兜底状态
    } finally {
      isLoadingSummary.value = false
    }
  }

  // 2. 获取 ECharts 走势与延时分布
  const fetchCharts = async () => {
    isLoadingCharts.value = true
    try {
      const [trendRes, distRes] = await Promise.all([
        getTokenTrendsApi(7),
        getLatencyDistributionApi()
      ])
      if (trendRes && trendRes.data) {
        tokenTrends.value = trendRes.data
      }
      if (distRes && distRes.data) {
        latencyDistribution.value = distRes.data
      }
    } catch {
      // 保持兜底状态
    } finally {
      isLoadingCharts.value = false
    }
  }

  // 3. 获取 TOP 5 双榜单
  const fetchTopRankings = async () => {
    try {
      const res = await getTopRankingsApi()
      if (res && res.data) {
        topRankings.value = res.data
      }
    } catch {
      // 保持兜底状态
    }
  }

  // 4. 分页获取安全审计流水
  const fetchAuditLogs = async (page: number = 1) => {
    isLoadingAudit.value = true
    auditPage.value = page
    try {
      const res = await getAuditLogsApi({
        page,
        page_size: auditPageSize.value,
        status: auditStatusFilter.value,
        keyword: auditSearchKeyword.value
      })
      if (res && res.data) {
        auditLogs.value = res.data.items || []
        totalAuditLogs.value = res.data.total ?? 0
      }
    } catch {
      // 保持兜底状态
    } finally {
      isLoadingAudit.value = false
    }
  }

  // 5. 打开审计明细下钻抽屉
  const openAuditDetail = async (log: AuditLogItem) => {
    selectedLogForDetail.value = log
    showDetailDrawer.value = true
    try {
      const res = await getAuditLogDetailApi(log.trace_id)
      if (res && res.data) {
        selectedLogForDetail.value = res.data
      }
    } catch {
      // 保持当前已知信息
    }
  }

  const closeAuditDetail = () => {
    showDetailDrawer.value = false
    selectedLogForDetail.value = null
  }

  // 6. 全局一次性初次加载
  const loadAll = async () => {
    await Promise.all([
      fetchSummary(),
      fetchCharts(),
      fetchTopRankings(),
      fetchAuditLogs(1)
    ])
  }

  return {
    summary,
    tokenTrends,
    latencyDistribution,
    topRankings,
    auditLogs,
    totalAuditLogs,
    auditPage,
    auditPageSize,
    auditStatusFilter,
    auditSearchKeyword,
    isLoadingSummary,
    isLoadingCharts,
    isLoadingAudit,
    selectedLogForDetail,
    showDetailDrawer,
    fetchSummary,
    fetchCharts,
    fetchTopRankings,
    fetchAuditLogs,
    openAuditDetail,
    closeAuditDetail,
    loadAll
  }
})
