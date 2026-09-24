/**
 * 统一认证与当前用户状态仓库 (Auth Store)
 * 模块: FE-M1
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { UserContext } from '@/types/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(null)
  const user = ref<UserContext | null>(null)

  const setToken = (newToken: string) => {
    token.value = newToken
  }

  const setUser = (newUser: UserContext) => {
    user.value = newUser
  }

  const clearAuth = () => {
    token.value = null
    user.value = null
  }

  return { token, user, setToken, setUser, clearAuth }
})
