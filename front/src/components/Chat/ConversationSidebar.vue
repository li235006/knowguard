<template>
  <!-- FE-M2: 历史会话侧边栏抽屉 (PAGE-02 原型对齐) -->
  <aside
    class="w-60 h-screen bg-white border-r border-[#E5E7EB] flex flex-col justify-between p-3 select-none shrink-0"
  >
    <!-- Top Section -->
    <div class="flex flex-col gap-4 overflow-hidden">
      <!-- Brand Header -->
      <div class="flex items-center gap-2.5 px-2 py-1">
        <div class="w-7 h-7 bg-[#0071E3] rounded-md flex items-center justify-center text-white shadow-sm">
          <Shield :size="16" />
        </div>
        <div class="flex flex-col">
          <span class="font-bold text-[13px] tracking-tight text-[#0F172A] leading-tight">KnowGuard</span>
          <span class="text-[9px] text-[#94A3B8] tracking-wider uppercase font-medium">员工智能问答工作台</span>
        </div>
      </div>

      <!-- New Chat Button -->
      <button
        type="button"
        class="h-9 w-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-xs font-semibold rounded-lg flex items-center justify-center gap-2 transition-all shadow-sm cursor-pointer"
        @click="emit('new-chat')"
      >
        <Plus :size="14" />
        <span>新建智能问答</span>
      </button>

      <!-- Recent Conversations Section -->
      <div class="flex flex-col gap-1.5 flex-1 overflow-y-auto">
        <span class="text-[11px] font-semibold text-[#94A3B8] px-2 py-1">近期问答会话</span>

        <div
          v-for="conv in conversations"
          :key="conv.id"
          class="flex items-center justify-between px-2.5 py-2 rounded-lg text-xs cursor-pointer transition-colors group"
          :class="
            activeId === conv.id
              ? 'bg-[#EFF6FF] text-[#0071E3] font-semibold'
              : 'text-[#475569] hover:bg-[#F8FAFC] hover:text-[#0F172A]'
          "
          @click="emit('select-chat', conv.id)"
        >
          <div class="flex items-center gap-2 overflow-hidden flex-1 mr-2">
            <MessageSquare
              :size="14"
              :class="activeId === conv.id ? 'text-[#0071E3]' : 'text-[#64748B] group-hover:text-[#0F172A]'"
              class="shrink-0"
            />
            <span class="truncate">{{ conv.title }}</span>
          </div>
          <span class="text-[10px] text-[#94A3B8] shrink-0 font-mono">{{ conv.created_at }}</span>
        </div>
      </div>
    </div>

    <!-- Bottom Section: Link to Admin & User Profile -->
    <div class="flex flex-col gap-2 pt-2 border-t border-[#F1F5F9]">
      <!-- Link to Management Console -->
      <router-link
        to="/admin/knowledge/units"
        class="flex items-center justify-between px-2.5 py-2 rounded-lg text-xs font-medium text-[#475569] hover:bg-[#F8FAFC] transition-colors"
      >
        <div class="flex items-center gap-2 text-xs">
          <LayoutDashboard :size="14" class="text-[#0071E3]" />
          <span>进入管理控制台</span>
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
              {{ authStore.user?.real_name || authStore.user?.username || '用户' }}
            </span>
            <span class="text-[10px] text-[#64748B] truncate">
              工号: {{ authStore.user?.employee_id || '10086' }}
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
 * 历史会话侧边栏抽屉组件
 * 模块: FE-M2 (PAGE-02)
 */

import { computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  Shield,
  Plus,
  MessageSquare,
  LayoutDashboard,
  ArrowUpRight,
  LogOut
} from 'lucide-vue-next'
import type { ConversationItem } from '@/types/chat'
import { useAuthStore } from '@/stores/auth'

defineProps<{
  conversations: ConversationItem[]
  activeId: string
}>()

const emit = defineEmits<{
  (e: 'new-chat'): void
  (e: 'select-chat', id: string): void
}>()

const router = useRouter()
const authStore = useAuthStore()

const userInitial = computed(() => {
  const name = authStore.user?.real_name || authStore.user?.username || 'U'
  return name.charAt(0)
})

const handleLogout = async () => {
  await authStore.logout()
  router.push('/login')
}
</script>
