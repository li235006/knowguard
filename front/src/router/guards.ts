/**
 * 路由全局前置守卫与双 Token 拦截器存根
 */

import type { Router } from 'vue-router'

export const setupRouterGuards = (router: Router): void => {
  router.beforeEach((to, from, next) => {
    // 路由鉴权拦截存根
    next()
  })
}
