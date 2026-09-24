/**
 * 智能问答、会话与联想建议 API 存根
 * 模块: FE-M2 / M4: RAG
 */

import request from '@/utils/request'
import type { ApiResponse } from '@/types/common'

export const getConversationsApi = async (): Promise<ApiResponse<any[]>> => {
  return request.get('/api/v1/chat/conversations')
}

export const getSuggestionsApi = async (): Promise<ApiResponse<string[]>> => {
  return request.get('/api/v1/chat/suggestions')
}
