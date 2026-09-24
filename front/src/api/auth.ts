/**
 * 统一认证服务 API
 * 模块: FE-M1 / P0-1
 * 接口契约对齐: backend/app/schemas/auth.py
 * 支持真实后端 RESTful 联调与 VITE_ENABLE_MOCK=true/false 双态自由切换
 */

import request, { generateTraceId } from '@/utils/request'
import type { ApiResponse } from '@/types/common'
import type { LoginRequest, TokenResponse, RefreshTokenRequest, UserContext } from '@/types/auth'

const isMockEnabled = (): boolean => {
  return import.meta.env.VITE_ENABLE_MOCK === 'true'
}

// 预置 Mock 用户档案库 (对齐张三 10086、李四 10087、王五 10088)
const mockUserProfiles: Record<string, UserContext> = {
  '10086': {
    user_id: 1,
    username: '10086',
    real_name: '张三',
    employee_id: '10086',
    dept_id: 14,
    dept_name: '市场推广部',
    role_code: 'ROLE_COMMON_USER',
    role_codes: ['ROLE_COMMON_USER'],
    role_ids: [5],
    permissions: ['knowledge:view', 'chat:use'],
    is_superuser: false
  },
  '10087': {
    user_id: 2,
    username: '10087',
    real_name: '李四',
    employee_id: '10087',
    dept_id: 4,
    dept_name: '信息安全研发组',
    role_code: 'ROLE_KNOWLEDGE_ADMIN',
    role_codes: ['ROLE_KNOWLEDGE_ADMIN'],
    role_ids: [2],
    permissions: ['knowledge:view', 'knowledge:import', 'knowledge:reparse', 'knowledge:policy', 'system:user:status'],
    is_superuser: false
  },
  '10088': {
    user_id: 3,
    username: '10088',
    real_name: '王五',
    employee_id: '10088',
    dept_id: 9,
    dept_name: '大模型与算法工程部',
    role_code: 'ROLE_TECH_LEAD',
    role_codes: ['ROLE_TECH_LEAD'],
    role_ids: [4],
    permissions: ['knowledge:view', 'knowledge:import', 'evolution:view', 'evolution:faq:publish', 'analytics:view'],
    is_superuser: false
  },
  admin: {
    user_id: 99,
    username: 'admin',
    real_name: '超级管理员',
    employee_id: '00001',
    dept_id: 1,
    dept_name: '平台技术部',
    role_code: 'ROLE_SUPER_ADMIN',
    role_codes: ['ROLE_SUPER_ADMIN'],
    role_ids: [1],
    permissions: ['*'],
    is_superuser: true
  }
}

export const loginApi = async (data: LoginRequest): Promise<ApiResponse<TokenResponse>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 150))
    const trimmedUser = data.username.trim()
    const profile = mockUserProfiles[trimmedUser] || mockUserProfiles['10086']

    const tokenResp: TokenResponse = {
      access_token: `mock-jwt-access-${profile.employee_id}-${Date.now()}`,
      refresh_token: `mock-jwt-refresh-${profile.employee_id}-${Date.now()}`,
      token_type: 'Bearer',
      expires_in: 7200
    }

    return {
      code: 200,
      message: 'success',
      data: tokenResp,
      trace_id: generateTraceId()
    }
  }

  return request.post('/api/v1/auth/login', data)
}

export const refreshTokenApi = async (data: RefreshTokenRequest): Promise<ApiResponse<TokenResponse>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 100))
    return {
      code: 200,
      message: 'success',
      data: {
        access_token: `mock-jwt-refreshed-${Date.now()}`,
        refresh_token: data.refresh_token,
        token_type: 'Bearer',
        expires_in: 7200
      },
      trace_id: generateTraceId()
    }
  }

  return request.post('/api/v1/auth/refresh', data)
}

export const logoutApi = async (): Promise<ApiResponse<boolean>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 80))
    return {
      code: 200,
      message: 'success',
      data: true,
      trace_id: generateTraceId()
    }
  }

  return request.post('/api/v1/auth/logout')
}

export const getCurrentUserApi = async (): Promise<ApiResponse<UserContext>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 100))
    const token = localStorage.getItem('access_token') || ''
    let profile = mockUserProfiles['10086']

    if (token.includes('10087')) {
      profile = mockUserProfiles['10087']
    } else if (token.includes('10088')) {
      profile = mockUserProfiles['10088']
    } else if (token.includes('00001') || token.includes('admin')) {
      profile = mockUserProfiles['admin']
    }

    return {
      code: 200,
      message: 'success',
      data: { ...profile },
      trace_id: generateTraceId()
    }
  }

  return request.get('/api/v1/auth/me')
}
