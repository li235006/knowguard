<template>
  <!-- FE-M2: 历史会话侧边栏抽屉 (PAGE-02 原型对齐与会话 CRUD) -->
  <aside
    class="w-64 h-screen bg-white border-r border-[#E5E7EB] flex flex-col justify-between p-3 select-none shrink-0"
  >
    <!-- Top Section -->
    <div class="flex flex-col gap-3.5 overflow-hidden flex-1">
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
        class="h-9 w-full bg-[#0071E3] hover:bg-[#0077ED] active:scale-[0.98] text-white text-xs font-semibold rounded-lg flex items-center justify-center gap-2 transition-all shadow-sm cursor-pointer"
        @click="emit('new-chat')"
      >
        <Plus :size="14" />
        <span>新建智能问答</span>
      </button>

      <!-- Recent Conversations Section -->
      <div class="flex flex-col gap-1 flex-1 overflow-y-auto pr-0.5">
        <div class="flex items-center justify-between px-2 py-1 text-[11px] font-semibold text-[#94A3B8]">
          <span>近期问答会话</span>
          <span class="font-mono text-[10px]">{{ conversations.length }}</span>
        </div>

        <!-- Conversation Item List -->
        <div
          v-for="conv in conversations"
          :key="conv.id"
          class="flex items-center justify-between px-2.5 py-2 rounded-lg text-xs cursor-pointer transition-colors group relative"
          :class="
            activeId === conv.id
              ? 'bg-[#EFF6FF] text-[#0071E3] font-medium'
              : 'text-[#475569] hover:bg-[#F8FAFC] hover:text-[#0F172A]'
          "
          @click="onSelect(conv.id)"
        >
          <!-- Left: Icon & Title -->
          <div class="flex items-center gap-2 overflow-hidden flex-1 mr-2 min-w-0">
            <MessageSquare
              :size="14"
              :class="activeId === conv.id ? 'text-[#0071E3]' : 'text-[#64748B] group-hover:text-[#0F172A]'"
              class="shrink-0"
            />

            <!-- Editing Title Input -->
            <input
              v-if="editingId === conv.id"
              ref="editInputRef"
              v-model="editingTitle"
              type="text"
              class="w-full bg-white border border-[#0071E3] rounded px-1.5 py-0.5 text-xs text-[#0F172A] focus:outline-none"
              @click.stop
              @keyup.enter="commitRename(conv.id)"
              @blur="commitRename(conv.id)"
              @keyup.esc="cancelRename"
            />

            <!-- Normal Title Display -->
            <span v-else class="truncate text-xs">{{ conv.title }}</span>
          </div>

          <!-- Right: Timestamp & Hover Action Buttons -->
          <div class="flex items-center shrink-0">
            <!-- Timestamp (Visible by default, hidden on group-hover if active) -->
            <span
              v-if="editingId !== conv.id"
              class="text-[10px] text-[#94A3B8] font-mono group-hover:hidden"
            >
              {{ conv.created_at }}
            </span>

            <!-- Action Buttons (Visible on group hover) -->
            <div
              v-if="editingId !== conv.id"
              class="hidden group-hover:flex items-center gap-1"
            >
              <!-- Rename Button -->
              <button
                type="button"
                class="p-1 rounded text-gray-400 hover:text-[#0071E3] hover:bg-white transition-colors"
                title="重命名会话"
                @click.stop="startRename(conv)"
              >
                <Pencil :size="12" />
              </button>

              <!-- Delete Button -->
              <button
                type="button"
                class="p-1 rounded text-gray-400 hover:text-rose-600 hover:bg-white transition-colors"
                title="删除会话"
                @click.stop="openDeleteConfirm(conv.id)"
              >
                <Trash2 :size="12" />
              </button>
            </div>
          </div>
        </div>

        <!-- Empty Conversation State -->
        <div v-if="conversations.length === 0" class="py-8 text-center text-[11px] text-[#94A3B8]">
          暂无历史问答，点击上方新建
        </div>
      </div>
    </div>

    <!-- Bottom Section: Link to Admin & User Profile -->
    <div class="flex flex-col gap-2 pt-2 border-t border-[#F1F5F9] shrink-0">
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

    <!-- Delete Conversation Confirmation Dialog -->
    <div
      v-if="convIdToDelete"
      class="fixed inset-0 bg-black/30 backdrop-blur-[2px] z-50 flex items-center justify-center p-4 animate-in fade-in duration-150"
      @click.self="convIdToDelete = null"
    >
      <div class="bg-white rounded-xl max-w-xs w-full p-4 shadow-xl border border-gray-100 flex flex-col gap-3">
        <div class="flex items-center gap-2 text-rose-600 font-semibold text-xs">
          <Trash2 :size="16" />
          <span>删除历史会话</span>
        </div>
        <p class="text-xs text-[#64748B] leading-relaxed">
          确认删除该会话记录？删除后历史问答消息与追问上下文将无法恢复。
        </p>
        <div class="flex items-center justify-end gap-2 pt-2 border-t border-[#F1F5F9]">
          <button
            type="button"
            class="px-3 py-1 text-xs text-[#64748B] hover:bg-gray-100 rounded-lg transition-colors font-medium"
            @click="convIdToDelete = null"
          >
            取消
          </button>
          <button
            type="button"
            class="px-3 py-1 text-xs bg-rose-600 hover:bg-rose-700 text-white rounded-lg transition-colors font-medium shadow-sm"
            @click="confirmDelete"
          >
            确认删除
          </button>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
/**
 * 历史会话侧边栏抽屉组件
 * 模块: FE-M2 / P1-3 (PAGE-02 原型对齐与会话 CRUD)
 */

import { ref, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import {
  Shield,
  Plus,
  MessageSquare,
  LayoutDashboard,
  ArrowUpRight,
  LogOut,
  Trash2,
  Pencil
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
  (e: 'delete-chat', id: string): void
  (e: 'rename-chat', id: string, newTitle: string): void
}>()

const router = useRouter()
const authStore = useAuthStore()

// 重命名控制
const editingId = ref<string | null>(null)
const editingTitle = ref<string>('')
const editInputRef = ref<HTMLInputElement | null>(null)

// 删除确认控制
const convIdToDelete = ref<string | null>(null)

const userInitial = computed(() => {
  const name = authStore.user?.real_name || authStore.user?.username || 'U'
  return name.charAt(0)
})

const onSelect = (id: string) => {
  if (editingId.value !== id) {
    emit('select-chat', id)
  }
}

const startRename = (conv: ConversationItem) => {
  editingId.value = conv.id
  editingTitle.value = conv.title
  nextTick(() => {
    editInputRef.value?.focus()
    editInputRef.value?.select()
  })
}

const commitRename = (id: string) => {
  if (editingId.value === id) {
    if (editingTitle.value.trim()) {
      emit('rename-chat', id, editingTitle.value.trim())
    }
    editingId.value = null
  }
}

const cancelRename = () => {
  editingId.value = null
}

const openDeleteConfirm = (id: string) => {
  convIdToDelete.value = id
}

const confirmDelete = () => {
  if (convIdToDelete.value) {
    emit('delete-chat', convIdToDelete.value)
    convIdToDelete.value = null
  }
}

const handleLogout = async () => {
  await authStore.logout()
  router.push('/login')
}
</script>
