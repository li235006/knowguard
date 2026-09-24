<template>
  <!-- FE-M0: 顶栏导航与面包屑组件 -->
  <header
    class="h-14 w-full bg-white/90 backdrop-blur-apple border-b border-[#E5E7EB] px-6 flex items-center justify-between select-none shrink-0"
  >
    <!-- Left: Breadcrumb / Section Title -->
    <div class="flex items-center gap-2 text-xs text-[#64748B]">
      <span class="font-medium text-[#0F172A]">{{ currentTitle }}</span>
      <span v-if="subTitle" class="text-[#CBD5E1]">/</span>
      <span v-if="subTitle" class="text-[#64748B]">{{ subTitle }}</span>
    </div>

    <!-- Right: Engine Status & Identity Badge -->
    <div class="flex items-center gap-3">
      <!-- Guard Security Engine Status Badge -->
      <div
        class="hidden sm:flex items-center gap-1.5 px-2.5 py-1 bg-[#F0FDF4] border border-[#BBF7D0] rounded-full text-[11px] text-[#16A34A] font-medium"
      >
        <span class="w-1.5 h-1.5 rounded-full bg-[#16A34A] animate-pulse"></span>
        <span>4D-RBAC 动态鉴权护栏在线</span>
      </div>

      <!-- Current Employee Badge -->
      <div v-if="authStore.user" class="flex items-center gap-1.5 px-2.5 py-1 bg-gray-50 border border-gray-200 rounded-lg text-xs text-[#475569]">
        <span class="font-mono text-[#0071E3] font-bold">{{ authStore.user.employee_id }}</span>
        <span>{{ authStore.user.real_name }}</span>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
/**
 * 顶栏导航与面包屑组件
 * 模块: FE-M0
 */

import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()

const currentTitle = computed(() => {
  if (route.path.startsWith('/admin/knowledge')) return '知识资产中心'
  if (route.path.startsWith('/admin/evolution')) return '自进化运营中心'
  if (route.path.startsWith('/admin/analytics')) return '运营与安全大盘'
  if (route.path.startsWith('/admin/system')) return '组织与系统设置'
  return (route.meta.title as string) || '管理控制台'
})

const subTitle = computed(() => {
  if (route.path.includes('/system/departments')) return '组织架构与员工'
  if (route.path.includes('/system/roles')) return '角色与功能权限'
  if (route.path.includes('/knowledge/units')) return '知识资产台账'
  return null
})
</script>
