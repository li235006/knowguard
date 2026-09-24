/**
 * Vue Router 路由中心配置存根
 * 覆盖全部 8 套终审原型路由
 */

import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { setupRouterGuards } from './guards'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: { title: '用户登录', public: true }
  },
  {
    path: '/chat',
    name: 'ChatWorkspace',
    component: () => import('@/views/chat/ChatWorkspace.vue'),
    meta: { title: '智能问答工作台', requiresAuth: true }
  },
  {
    path: '/admin',
    name: 'AdminLayout',
    component: () => import('@/components/Layout/AdminLayout.vue'),
    redirect: '/admin/knowledge/units',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'knowledge/units',
        name: 'KnowledgeUnits',
        component: () => import('@/views/knowledge/KnowledgeUnits.vue'),
        meta: { title: '知识资产台账' }
      },
      {
        path: 'evolution',
        name: 'KnowledgeEvolution',
        component: () => import('@/views/evolution/KnowledgeEvolution.vue'),
        meta: { title: '知识自进化' }
      },
      {
        path: 'analytics',
        name: 'OperationsAnalytics',
        component: () => import('@/views/analytics/OperationsAnalytics.vue'),
        meta: { title: '运营与安全大盘' }
      },
      {
        path: 'system/departments',
        name: 'DeptUserManage',
        component: () => import('@/views/system/DeptUserManage.vue'),
        meta: { title: '部门与员工' }
      },
      {
        path: 'system/roles',
        name: 'RoleManage',
        component: () => import('@/views/system/RoleManage.vue'),
        meta: { title: '角色权限' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/login'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

setupRouterGuards(router)

export default router
