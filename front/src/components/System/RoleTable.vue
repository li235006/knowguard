<template>
  <!-- FE-M3: 角色列表表格组件 (PAGE-05-B) -->
  <div class="flex-1 bg-white rounded-xl border border-[#E5E7EB] shadow-sm flex flex-col h-full min-w-0 overflow-hidden">
    <!-- Header Filter Bar -->
    <div class="p-3.5 border-b border-[#F1F5F9] flex items-center justify-between gap-3">
      <div class="relative w-64">
        <Search :size="14" class="absolute left-3 top-2.5 text-[#94A3B8]" />
        <input
          v-model="searchKeyword"
          type="text"
          placeholder="搜索角色名称或编码..."
          class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg pl-9 pr-3 py-1.5 text-xs text-[#0F172A] placeholder-[#94A3B8] focus:outline-none focus:border-[#0071E3]"
        />
      </div>

      <button
        type="button"
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#0071E3] text-white text-xs font-medium hover:bg-[#0077ED] transition-colors shadow-sm"
        @click="showCreateModal = true"
        v-permission="'system:role:assign'"
      >
        <ShieldPlus :size="13" />
        <span>新建自定义角色</span>
      </button>
    </div>

    <!-- Table Body -->
    <div class="flex-1 overflow-x-auto overflow-y-auto">
      <table class="w-full text-left border-collapse text-xs">
        <thead>
          <tr class="bg-[#F8FAFC] text-[#64748B] border-b border-[#E5E7EB] font-medium select-none">
            <th class="py-2.5 px-4">角色名称</th>
            <th class="py-2.5 px-4">角色唯一编码</th>
            <th class="py-2.5 px-4">角色职责说明</th>
            <th class="py-2.5 px-4">已绑定成员</th>
            <th class="py-2.5 px-4">授权权限总览</th>
            <th class="py-2.5 px-4 text-right">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-[#F1F5F9]">
          <tr
            v-for="role in filteredRoles"
            :key="role.id"
            class="hover:bg-[#F8FAFC]/80 transition-colors"
            :class="selectedRoleId === role.id ? 'bg-[#EFF6FF]/40' : ''"
          >
            <!-- Role Name -->
            <td class="py-3 px-4 font-semibold text-[#0F172A]">
              <div class="flex items-center gap-2">
                <ShieldCheck :size="15" class="text-[#0071E3]" />
                <span>{{ role.role_name }}</span>
              </div>
            </td>

            <!-- Role Code -->
            <td class="py-3 px-4 font-mono text-[11px] text-[#475569]">
              <span class="px-2 py-0.5 rounded bg-gray-100 border border-gray-200">
                {{ role.role_code }}
              </span>
            </td>

            <!-- Description -->
            <td class="py-3 px-4 text-[#64748B] max-w-xs truncate" :title="role.description">
              {{ role.description || '-' }}
            </td>

            <!-- User Count -->
            <td class="py-3 px-4">
              <span class="text-xs font-semibold text-[#0F172A]">{{ role.user_count || 0 }}</span>
              <span class="text-[10px] text-[#94A3B8] ml-1">人</span>
            </td>

            <!-- Permissions Preview -->
            <td class="py-3 px-4">
              <div class="flex flex-wrap gap-1 max-w-xs">
                <span
                  v-if="role.permissions.includes('*')"
                  class="px-2 py-0.5 rounded text-[10px] font-medium bg-red-50 text-red-600 border border-red-200"
                >
                  * 全部超管通配权限
                </span>
                <template v-else>
                  <span
                    v-for="perm in role.permissions.slice(0, 3)"
                    :key="perm"
                    class="px-1.5 py-0.5 rounded text-[10px] bg-gray-100 text-gray-700"
                  >
                    {{ perm }}
                  </span>
                  <span
                    v-if="role.permissions.length > 3"
                    class="px-1 py-0.5 rounded text-[10px] text-gray-400 bg-gray-50"
                  >
                    +{{ role.permissions.length - 3 }}
                  </span>
                </template>
              </div>
            </td>

            <!-- Action -->
            <td class="py-3 px-4 text-right">
              <button
                type="button"
                class="px-2.5 py-1 text-xs font-medium rounded-md transition-colors"
                :class="
                  selectedRoleId === role.id
                    ? 'bg-[#0071E3] text-white'
                    : 'bg-[#EFF6FF] text-[#0071E3] hover:bg-[#DBEAFE]'
                "
                @click="emit('configure-permissions', role)"
                v-permission="'system:role:assign'"
              >
                配置权限
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create Role Modal Dialog -->
    <div
      v-if="showCreateModal"
      class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4"
    >
      <div class="bg-white rounded-xl max-w-md w-full p-6 shadow-xl border border-gray-100 flex flex-col gap-4">
        <div class="flex items-center justify-between border-b pb-3">
          <h3 class="font-semibold text-sm text-[#0F172A]">新建自定义角色</h3>
          <button type="button" class="text-gray-400 hover:text-gray-600" @click="showCreateModal = false">
            <X :size="16" />
          </button>
        </div>

        <div class="flex flex-col gap-3 text-xs">
          <div class="flex flex-col gap-1">
            <label class="font-medium text-[#475569]">角色名称 *</label>
            <input
              v-model="newRoleForm.role_name"
              type="text"
              placeholder="例如: 安全合规审查员"
              class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-3 py-2 text-xs text-[#0F172A] focus:outline-none focus:border-[#0071E3]"
            />
          </div>

          <div class="flex flex-col gap-1">
            <label class="font-medium text-[#475569]">角色标识码 (建议大写下划线) *</label>
            <input
              v-model="newRoleForm.role_code"
              type="text"
              placeholder="例如: ROLE_SECURITY_REVIEWER"
              class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-3 py-2 text-xs text-[#0F172A] focus:outline-none focus:border-[#0071E3]"
            />
          </div>

          <div class="flex flex-col gap-1">
            <label class="font-medium text-[#475569]">职责描述</label>
            <textarea
              v-model="newRoleForm.description"
              rows="3"
              placeholder="描述该角色的数据范围与授权职责..."
              class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-3 py-2 text-xs text-[#0F172A] focus:outline-none focus:border-[#0071E3]"
            ></textarea>
          </div>
        </div>

        <div class="flex items-center justify-end gap-2 pt-2 border-t">
          <button
            type="button"
            class="px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            @click="showCreateModal = false"
          >
            取消
          </button>
          <button
            type="button"
            class="px-3 py-1.5 text-xs bg-[#0071E3] hover:bg-[#0077ED] text-white rounded-lg font-medium transition-colors disabled:opacity-50"
            :disabled="!newRoleForm.role_name.trim() || !newRoleForm.role_code.trim()"
            @click="submitCreateRole"
          >
            确认创建
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 角色管理表格组件
 * 模块: FE-M3 (PAGE-05-B)
 */

import { ref, reactive, computed } from 'vue'
import { Search, ShieldPlus, ShieldCheck, X } from 'lucide-vue-next'
import type { RoleItem } from '@/types/system'
import { createRoleApi } from '@/api/system'

const props = defineProps<{
  roles: RoleItem[]
  selectedRoleId: number | null
}>()

const emit = defineEmits<{
  (e: 'configure-permissions', role: RoleItem): void
  (e: 'refresh'): void
}>()

const searchKeyword = ref('')
const showCreateModal = ref(false)

const newRoleForm = reactive({
  role_name: '',
  role_code: '',
  description: ''
})

const filteredRoles = computed(() => {
  if (!searchKeyword.value.trim()) return props.roles
  const q = searchKeyword.value.trim().toLowerCase()
  return props.roles.filter(
    (r) =>
      r.role_name.toLowerCase().includes(q) ||
      r.role_code.toLowerCase().includes(q) ||
      (r.description && r.description.toLowerCase().includes(q))
  )
})

const submitCreateRole = async () => {
  try {
    await createRoleApi({
      role_name: newRoleForm.role_name.trim(),
      role_code: newRoleForm.role_code.trim().toUpperCase(),
      description: newRoleForm.description.trim(),
      permissions: ['knowledge:view']
    })
    showCreateModal.value = false
    emit('refresh')
  } catch (err) {
    alert(err instanceof Error ? err.message : '创建角色失败')
  }
}
</script>

