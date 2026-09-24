/**
 * 运营监控大盘与全链路审计流水 API 存根
 * 模块: FE-M6 / M6: Analytics
 */

import request from '@/utils/request'
import type { ApiResponse, PaginatedData, PaginationParams } from '@/types/common'
import type { DashboardSummary, TrendPoint, TopRankingItem, AuditLogItem } from '@/types/analytics'

export const getDashboardSummaryApi = async (): Promise<ApiResponse<DashboardSummary>> => {
  return request.get('/api/v1/analytics/dashboard-summary')
}

export const getTrendsApi = async (): Promise<ApiResponse<TrendPoint[]>> => {
  return request.get('/api/v1/analytics/trends')
}

export const getTopRankingsApi = async (): Promise<ApiResponse<TopRankingItem[]>> => {
  return request.get('/api/v1/analytics/top-rankings')
}

export const getAuditLogsApi = async (params: PaginationParams): Promise<ApiResponse<PaginatedData<AuditLogItem>>> => {
  return request.get('/api/v1/analytics/audit-logs', { params })
}
