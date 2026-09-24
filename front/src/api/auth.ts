/**
 * 统一认证服务 API 存根
 * 模块: FE-M1 / M1: IAM
 */

import request from '@/utils/request'
import type { ApiResponse } from '@/types/common'
import type { LoginRequest, TokenResponse, UserContext } from '@/types/auth'

export const loginApi = async (data: LoginRequest): Promise<ApiResponse<TokenResponse>> => {
  return request.post('/api/v1/auth/login', data)
}

export const refreshTokenApi = async (): Promise<ApiResponse<TokenResponse>> => {
  return request.post('/api/v1/auth/refresh')
}

export const logoutApi = async (): Promise<ApiResponse<boolean>> => {
  return request.post('/api/v1/auth/logout')
}

export const getCurrentUserApi = async (): Promise<ApiResponse<UserContext>> => {
  return request.get('/api/v1/auth/me')
}
