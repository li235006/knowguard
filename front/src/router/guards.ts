/**
 * 路由全局前置守卫与身份鉴权拦截器
 * 模块: FE-M1 / P0-1
 * 职责:
 *  - 未登录拦截并重定向至 /login (携带 redirect 参数)
 *  - 已登录状态下根据 Pinia 状态自动拉取 GET /api/v1/auth/me 刷新身份上下文
 *  - 防死锁与动态标题管理
 */

import type { Router } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

export const setupRouterGuards = (router: Router): void => {
  router.beforeEach(async (to, _from, next) => {
    // 动态同步网页标题
    const appTitle = import.meta.env.VITE_APP_TITLE || 'KnowGuard 智能知识库管理平台'
    const pageTitle = to.meta.title as string | undefined
    document.title = pageTitle ? `${pageTitle} · ${appTitle}` : appTitle

    const authStore = useAuthStore()
    const token = authStore.token || localStorage.getItem('access_token')

    // 1. 访问登录页面
    if (to.path === '/login') {
      if (token) {
        // 已登录访问登录页，直接重定向至知识资产控制台
        return next({ path: '/admin/knowledge/units' })
      }
      return next()
    }

    // 2. 公开白名单路由
    if (to.meta.public) {
      return next()
    }

    // 3. 受保护路由鉴权判断 (后台管理 /admin 或 问答工作台 /chat 或 requiresAuth)
    const isProtected = to.meta.requiresAuth || to.path.startsWith('/admin') || to.path.startsWith('/chat')

    if (isProtected) {
      if (!token) {
        // 未登录拦截至登录页
        return next({
          path: '/login',
          query: { redirect: to.fullPath }
        })
      }

      // 4. 已登录但 Pinia 状态中无用户信息，自动拉取 /me 刷新上下文
      if (!authStore.user) {
        try {
          await authStore.fetchCurrentUser()
          return next()
        } catch {
          // Token 过期或拉取失败，清空本地存储后跳转登录页，杜绝死锁
          authStore.clearAuth()
          return next({
            path: '/login',
            query: { redirect: to.fullPath }
          })
        }
      }

      return next()
    }

    // 默认放行
    next()
  })
}
