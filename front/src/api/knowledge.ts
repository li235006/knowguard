/**
 * 知识资产维护、切片与四维权限 API 存根
 * 模块: FE-M4 / M2: Ingestion & M3: Guard
 */

import request from '@/utils/request'
import type { ApiResponse, PaginatedData, PaginationParams } from '@/types/common'
import type { KnowledgeUnit, ChunkItem, PermissionPolicyConfig } from '@/types/knowledge'

export const getKnowledgeUnitsApi = async (params: PaginationParams): Promise<ApiResponse<PaginatedData<KnowledgeUnit>>> => {
  return request.get('/api/v1/knowledge/units', { params })
}

export const getUnitChunksApi = async (unitId: number): Promise<ApiResponse<ChunkItem[]>> => {
  return request.get(`/api/v1/knowledge/units/${unitId}/chunks`)
}

export const getUnitPolicyApi = async (unitId: number): Promise<ApiResponse<PermissionPolicyConfig>> => {
  return request.get(`/api/v1/guard/policies/${unitId}`)
}

export const updateUnitPolicyApi = async (unitId: number, data: PermissionPolicyConfig): Promise<ApiResponse<boolean>> => {
  return request.put(`/api/v1/guard/policies/${unitId}`, data)
}
