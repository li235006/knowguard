/**
 * 知识自进化、FAQ 审核与缺口工单 API 存根
 * 模块: FE-M5 / M5: Evolution
 */

import request from '@/utils/request'
import type { ApiResponse, PaginatedData, PaginationParams } from '@/types/common'
import type { FaqCandidate, FaqItem, KnowledgeGap } from '@/types/evolution'

export const getFaqCandidatesApi = async (params: PaginationParams): Promise<ApiResponse<PaginatedData<FaqCandidate>>> => {
  return request.get('/api/v1/evolution/candidates', { params })
}

export const publishFaqApi = async (data: Partial<FaqItem>): Promise<ApiResponse<FaqItem>> => {
  return request.post('/api/v1/evolution/faqs/publish', data)
}

export const getKnowledgeGapsApi = async (params: PaginationParams): Promise<ApiResponse<PaginatedData<KnowledgeGap>>> => {
  return request.get('/api/v1/evolution/knowledge-gaps', { params })
}
