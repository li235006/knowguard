/**
 * 统一认证与当前用户状态仓库 (Auth Store)
 * 模块: FE-M1 / P0-1
 * 职责: 持久化 access_token，完整维护 user_id, username, real_name, employee_id, dept_id, dept_name, role_code 身份上下文
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { LoginRequest, UserContext } from '@/types/auth'
import { loginApi, getCurrentUserApi, logoutApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  // 从 localStorage 恢复初始状态
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  
  const initialUser: UserContext | null = (() => {
    try {
      const stored = localStorage.getItem('user_context')
      return stored ? JSON.parse(stored) : null
    } catch {
      return null
    }
  })()
  const user = ref<UserContext | null>(initialUser)

  const isAuthenticated = computed(() => !!token.value)

  // 设置与持久化 Token
  const setToken = (accessToken: string, newRefreshToken?: string) => {
    token.value = accessToken
    localStorage.setItem('access_token', accessToken)
    if (newRefreshToken) {
      refreshToken.value = newRefreshToken
      localStorage.setItem('refresh_token', newRefreshToken)
    }
  }

  // 设置与持久化 UserContext (完整维护身份上下文字段)
  const setUser = (newUser: UserContext) => {
    user.value = newUser
    localStorage.setItem('user_context', JSON.stringify(newUser))
  }

  // 清空状态与缓存
  const clearAuth = () => {
    token.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_context')
  }

  // 登录全流程对接：调用 POST /api/v1/auth/login 与 GET /api/v1/auth/me 并持久化
  const login = async (credentials: LoginRequest): Promise<UserContext> => {
    const tokenRes = await loginApi(credentials)
    const tokenData = tokenRes.data
    if (!tokenData?.access_token) {
      throw new Error(tokenRes.message || '登录凭证签发失败')
    }

    setToken(tokenData.access_token, tokenData.refresh_token)

    // 登录成功后立即拉取当前身份上下文
    const userRes = await getCurrentUserApi()
    if (!userRes.data) {
      throw new Error('获取用户身份上下文失败')
    }

    setUser(userRes.data)
    return userRes.data
  }

  // 主动刷新拉取当前用户身份上下文
  const fetchCurrentUser = async (): Promise<UserContext | null> => {
    if (!token.value) {
      clearAuth()
      return null
    }

    try {
      const res = await getCurrentUserApi()
      if (res.data) {
        setUser(res.data)
        return res.data
      }
      return null
    } catch (err) {
      clearAuth()
      throw err
    }
  }

  // 退出登录
  const logout = async (): Promise<void> => {
    try {
      await logoutApi()
    } catch {
      // 忽略后端注销异常，前端强制清空会话
    } finally {
      clearAuth()
    }
  }

  // 权限判定辅助方法
  const hasPermission = (permissionCode: string): boolean => {
    if (!user.value) return false
    if (user.value.is_superuser) return true
    const perms = user.value.permissions || []
    if (perms.includes('*')) return true
    return perms.includes(permissionCode)
  }

  const hasAnyPermission = (permissionCodes: string[]): boolean => {
    if (!user.value) return false
    if (user.value.is_superuser) return true
    const perms = user.value.permissions || []
    if (perms.includes('*')) return true
    return permissionCodes.some((code) => perms.includes(code))
  }

  return {
    token,
    refreshToken,
    user,
    isAuthenticated,
    setToken,
    setUser,
    clearAuth,
    login,
    fetchCurrentUser,
    logout,
    hasPermission,
    hasAnyPermission
  }
})
