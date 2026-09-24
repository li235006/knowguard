<template>
  <!-- FE-M0: 业务菜单侧边栏 (对齐 PAGE-05 原型) -->
  <aside
    class="w-56 h-screen bg-white border-r border-[#E5E7EB] flex flex-col justify-between p-3 select-none shrink-0"
  >
    <!-- Top Section -->
    <div class="flex flex-col gap-5">
      <!-- Sidebar Brand Header -->
      <div class="flex items-center gap-2.5 px-2 py-1">
        <div class="w-7 h-7 bg-[#0071E3] rounded-md flex items-center justify-center text-white shadow-sm">
          <Shield :size="16" />
        </div>
        <div class="flex flex-col">
          <span class="font-bold text-[13px] tracking-tight text-[#0F172A] leading-tight">KnowGuard</span>
          <span class="text-[9px] text-[#94A3B8] tracking-wider uppercase font-medium">管理控制台</span>
        </div>
      </div>

      <!-- Navigation Menu List -->
      <nav class="flex flex-col gap-1">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-xs font-medium transition-all group"
          :class="[
            isNavActive(item.path)
              ? 'bg-[#EFF6FF] text-[#0071E3] font-semibold'
              : 'text-[#475569] hover:bg-[#F8FAFC] hover:text-[#0F172A]'
          ]"
        >
          <component
            :is="item.icon"
            :size="15"
            :class="isNavActive(item.path) ? 'text-[#0071E3]' : 'text-[#64748B] group-hover:text-[#0F172A]'"
          />
          <span class="truncate">{{ item.name }}</span>
        </router-link>
      </nav>
    </div>

    <!-- Bottom Section: Work Mode Switch & User Profile Box -->
    <div class="flex flex-col gap-2 pt-2 border-t border-[#F1F5F9]">
      <!-- Quick Switch to Chat Workspace -->
      <router-link
        to="/chat"
        class="flex items-center justify-between px-2.5 py-2 rounded-lg text-xs font-medium text-[#475569] hover:bg-[#F8FAFC] transition-colors"
      >
        <div class="flex items-center gap-2 text-xs">
          <MessageSquare :size="14" class="text-[#0071E3]" />
          <span>智能问答工作台</span>
        </div>
        <ArrowUpRight :size="12" class="text-[#94A3B8]" />
      </router-link>

      <!-- User Profile Box -->
      <div class="bg-[#F8FAFC] rounded-lg border border-[#E5E7EB] p-2 flex items-center justify-between">
        <div class="flex items-center gap-2 overflow-hidden">
          <div
            class="w-7 h-7 bg-[#0071E3] rounded-full flex items-center justify-center text-white text-xs font-medium shrink-0"
          >
            {{ userInitial }}
          </div>
          <div class="flex flex-col truncate">
            <span class="text-xs font-semibold text-[#0F172A] truncate">
              {{ authStore.user?.real_name || authStore.user?.username || '未登录' }}
            </span>
            <span class="text-[10px] text-[#64748B] truncate">
              {{ authStore.user?.dept_name || authStore.user?.role_code || '游客' }}
            </span>
          </div>
        </div>

        <button
          type="button"
          title="退出登录"
          class="p-1 text-[#94A3B8] hover:text-red-500 rounded transition-colors"
          @click="handleLogout"
        >
          <LogOut :size="14" />
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
/**
 * 侧边栏导航组件
 * 模块: FE-M0 (对齐 PAGE-05-A / PAGE-05-B 原型)
 */

import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Shield,
  Activity,
  Database,
  Zap,
  Settings,
  MessageSquare,
  LogOut,
  ArrowUpRight
} from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const navItems = [
  {
    name: '运营与安全大盘',
    path: '/admin/analytics',
    icon: Activity
  },
  {
    name: '知识资产台账',
    path: '/admin/knowledge/units',
    icon: Database
  },
  {
    name: '知识自进化运营',
    path: '/admin/evolution',
    icon: Zap
  },
  {
    name: '组织与系统设置',
    path: '/admin/system/departments',
    icon: Settings
  }
]

const isNavActive = (path: string): boolean => {
  if (path === '/admin/system/departments') {
    return route.path.startsWith('/admin/system')
  }
  return route.path.startsWith(path)
}

const userInitial = computed(() => {
  const name = authStore.user?.real_name || authStore.user?.username || 'U'
  return name.charAt(0).toUpperCase()
})

const handleLogout = async () => {
  await authStore.logout()
  router.push('/login')
}
</script>
