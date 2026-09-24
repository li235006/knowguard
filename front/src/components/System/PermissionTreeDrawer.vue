<template>
  <!-- FE-M3: 三级 RBAC 权限授权抽屉组件 (PAGE-05-B) -->
  <div
    v-if="isOpen && role"
    class="w-[440px] bg-white border-l border-[#E5E7EB] shadow-2xl flex flex-col h-full shrink-0 z-20 select-none animate-slide-in"
  >
    <!-- Drawer Header -->
    <div class="h-12 border-b border-[#E5E7EB] px-4 flex items-center justify-between shrink-0 bg-white">
      <div class="flex items-center gap-2 overflow-hidden">
        <span class="font-bold text-xs text-[#0F172A] truncate">权限配置: {{ role.role_name }}</span>
        <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#EFF6FF] text-[#0071E3] border border-[#BFDBFE] shrink-0">
          {{ role.role_code }}
        </span>
      </div>
      <button
        type="button"
        class="p-1 text-[#94A3B8] hover:text-[#0F172A] rounded transition-colors"
        @click="emit('close')"
      >
        <X :size="16" />
      </button>
    </div>

    <!-- Drawer Body -->
    <div class="flex-1 overflow-y-auto p-3.5 flex flex-col gap-3">
      <!-- Role Meta Card -->
      <div class="bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg p-3 flex flex-col gap-1 text-xs">
        <div class="font-semibold text-[#0F172A] flex items-center gap-1.5">
          <Users :size="13" class="text-[#0071E3]" />
          <span>当前已授权 {{ role.user_count || 1 }} 位用户：系统管理员、知识主管等</span>
        </div>
        <p class="text-[11px] text-[#64748B] leading-relaxed">
          修改下方的功能树将立即对已绑定的所有账号生效，支持按钮级细粒度指令控制。
        </p>
      </div>

      <!-- Tree Section Title & Batch Bar -->
      <div class="flex items-center justify-between">
        <span class="font-bold text-[11px] text-[#0F172A]">
          三级 RBAC 功能权限授权树 (菜单 ➔ 路由 ➔ 按钮)
        </span>
        <div class="flex items-center gap-2 text-[11px]">
          <button
            type="button"
            class="text-[#0071E3] hover:underline"
            @click="selectAll"
          >
            全选
          </button>
          <span class="text-[#CBD5E1]">|</span>
          <button
            type="button"
            class="text-[#64748B] hover:text-red-500"
            @click="clearAll"
          >
            清空
          </button>
        </div>
      </div>

      <!-- 3-Tier Tree Card -->
      <div class="border border-[#E5E7EB] rounded-lg p-2.5 flex flex-col gap-2.5 bg-white">
        <!-- Loop Menu Level (Tier 1) -->
        <div
          v-for="menuNode in permissionTree"
          :key="menuNode.id"
          class="border-b border-[#F1F5F9] last:border-b-0 pb-2.5 last:pb-0 flex flex-col gap-1.5"
        >
          <!-- Menu Header -->
          <label class="flex items-center gap-2 cursor-pointer font-semibold text-xs text-[#0F172A]">
            <input
              type="checkbox"
              :checked="isMenuChecked(menuNode)"
              class="w-3.5 h-3.5 text-[#0071E3] rounded border-gray-300 focus:ring-[#0071E3]"
              @change="toggleMenu(menuNode)"
            />
            <span class="flex items-center gap-1.5">
              <Folder :size="13" class="text-[#0071E3]" />
              {{ menuNode.title }}
            </span>
          </label>

          <!-- Loop Route Level (Tier 2) -->
          <div
            v-for="routeNode in menuNode.children"
            :key="routeNode.id"
            class="pl-5 flex flex-col gap-1"
          >
            <label class="flex items-center gap-2 cursor-pointer text-xs font-medium text-[#334155]">
              <input
                type="checkbox"
                :checked="selectedCodes.has(routeNode.code)"
                class="w-3.5 h-3.5 text-[#0071E3] rounded border-gray-300 focus:ring-[#0071E3]"
                @change="toggleNode(routeNode.code)"
              />
              <span class="flex items-center gap-1.5">
                <FileCode :size="12" class="text-amber-500" />
                {{ routeNode.title }}
              </span>
            </label>

            <!-- Loop Button Level (Tier 3) -->
            <div
              v-if="routeNode.children && routeNode.children.length > 0"
              class="pl-5 grid grid-cols-1 gap-1 pt-0.5"
            >
              <label
                v-for="btnNode in routeNode.children"
                :key="btnNode.id"
                class="flex items-center gap-2 cursor-pointer text-[11px] text-[#64748B] hover:text-[#0F172A]"
              >
                <input
                  type="checkbox"
                  :checked="selectedCodes.has(btnNode.code)"
                  class="w-3 h-3 text-[#0071E3] rounded border-gray-300 focus:ring-[#0071E3]"
                  @change="toggleNode(btnNode.code)"
                />
                <span :class="btnNode.title.includes('高危') ? 'text-red-500 font-medium' : ''">
                  {{ btnNode.title }}
                </span>
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Drawer Footer -->
    <div class="h-14 border-t border-[#E5E7EB] px-4 flex items-center justify-between shrink-0 bg-[#F8FAFC]">
      <span class="text-[11px] text-[#64748B]">
        已选中 <span class="font-mono font-bold text-[#0071E3]">{{ selectedCodes.size }}</span> 项权限
      </span>
      <div class="flex items-center gap-2">
        <button
          type="button"
          class="px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-200 rounded-lg transition-colors"
          @click="emit('close')"
        >
          取消
        </button>
        <button
          type="button"
          :disabled="isSaving"
          class="px-3.5 py-1.5 text-xs bg-[#0071E3] hover:bg-[#0077ED] text-white font-medium rounded-lg transition-colors flex items-center gap-1.5 shadow-sm"
          @click="savePermissions"
        >
          <Check :size="13" />
          <span>{{ isSaving ? '保存中...' : '保存权限配置' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 角色功能权限授权抽屉组件 (三级 RBAC 树)
 * 模块: FE-M3 (PAGE-05-B)
 */

import { ref, watch } from 'vue'
import { X, Users, Folder, FileCode, Check } from 'lucide-vue-next'
import type { RoleItem, PermissionNode } from '@/types/system'

const props = defineProps<{
  isOpen: boolean
  role: RoleItem | null
  permissionTree: PermissionNode[]
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', roleId: number, permissions: string[]): void
}>()

const selectedCodes = ref<Set<string>>(new Set())
const isSaving = ref(false)

watch(
  () => props.role,
  (newRole) => {
    if (newRole) {
      if (newRole.permissions.includes('*')) {
        // 全选所有权限
        const all = getAllCodes(props.permissionTree)
        selectedCodes.value = new Set(all)
      } else {
        selectedCodes.value = new Set(newRole.permissions)
      }
    }
  },
  { immediate: true }
)

const getAllCodes = (nodes: PermissionNode[]): string[] => {
  let codes: string[] = []
  for (const n of nodes) {
    codes.push(n.code)
    if (n.children) {
      codes = codes.concat(getAllCodes(n.children))
    }
  }
  return codes
}

const isMenuChecked = (menuNode: PermissionNode): boolean => {
  if (!menuNode.children || menuNode.children.length === 0) {
    return selectedCodes.value.has(menuNode.code)
  }
  return menuNode.children.every((c) => selectedCodes.value.has(c.code))
}

const toggleMenu = (menuNode: PermissionNode) => {
  const isChecked = isMenuChecked(menuNode)
  const childCodes = getAllCodes([menuNode])
  if (isChecked) {
    childCodes.forEach((c) => selectedCodes.value.delete(c))
  } else {
    childCodes.forEach((c) => selectedCodes.value.add(c))
  }
  selectedCodes.value = new Set(selectedCodes.value)
}

const toggleNode = (code: string) => {
  if (selectedCodes.value.has(code)) {
    selectedCodes.value.delete(code)
  } else {
    selectedCodes.value.add(code)
  }
  selectedCodes.value = new Set(selectedCodes.value)
}

const selectAll = () => {
  selectedCodes.value = new Set(getAllCodes(props.permissionTree))
}

const clearAll = () => {
  selectedCodes.value = new Set()
}

const savePermissions = async () => {
  if (!props.role) return
  isSaving.value = true
  try {
    emit('save', props.role.id, Array.from(selectedCodes.value))
  } finally {
    isSaving.value = false
  }
}
</script>

