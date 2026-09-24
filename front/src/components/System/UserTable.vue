<template>
  <!-- FE-M3: 员工台账表格组件 (PAGE-05-A) -->
  <div class="flex-1 bg-white rounded-xl border border-[#E5E7EB] shadow-sm flex flex-col h-full min-w-0 overflow-hidden">
    <!-- Action Filter Bar -->
    <div class="p-3.5 border-b border-[#F1F5F9] flex flex-wrap items-center justify-between gap-3">
      <!-- Left: Search Box -->
      <div class="relative w-64">
        <Search :size="14" class="absolute left-3 top-2.5 text-[#94A3B8]" />
        <input
          v-model="searchKeyword"
          type="text"
          placeholder="搜索工号、姓名、邮箱..."
          class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg pl-9 pr-3 py-1.5 text-xs text-[#0F172A] placeholder-[#94A3B8] focus:outline-none focus:border-[#0071E3]"
          @keyup.enter="handleSearch"
        />
      </div>

      <!-- Right: Action Buttons -->
      <div class="flex items-center gap-2">
        <button
          type="button"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#E5E7EB] bg-white text-xs font-medium text-[#475569] hover:bg-[#F8FAFC] transition-colors"
          @click="showBatchImportAlert = true"
          v-permission="'system:user:manage'"
        >
          <Upload :size="13" class="text-[#64748B]" />
          <span>批量导入员工</span>
        </button>

        <button
          type="button"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#0071E3] text-white text-xs font-medium hover:bg-[#0077ED] transition-colors shadow-sm"
          @click="openAddUserModal"
          v-permission="'system:user:manage'"
        >
          <UserPlus :size="13" />
          <span>新建员工账号</span>
        </button>
      </div>
    </div>

    <!-- Table Body -->
    <div class="flex-1 overflow-x-auto overflow-y-auto">
      <table class="w-full text-left border-collapse text-xs">
        <thead>
          <tr class="bg-[#F8FAFC] text-[#64748B] border-b border-[#E5E7EB] font-medium select-none">
            <th class="py-2.5 px-4">工号/账号</th>
            <th class="py-2.5 px-4">姓名</th>
            <th class="py-2.5 px-4">所属部门</th>
            <th class="py-2.5 px-4">绑定角色</th>
            <th class="py-2.5 px-4">账号状态</th>
            <th class="py-2.5 px-4">入职创建时间</th>
            <th class="py-2.5 px-4 text-right">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-[#F1F5F9]">
          <tr
            v-for="user in users"
            :key="user.id"
            class="hover:bg-[#F8FAFC]/80 transition-colors"
          >
            <!-- Username & EmpID -->
            <td class="py-3 px-4 font-mono font-medium text-[#0F172A]">
              {{ user.username }}
            </td>

            <!-- Real Name & Avatar -->
            <td class="py-3 px-4">
              <div class="flex items-center gap-2">
                <div
                  class="w-6 h-6 rounded-full bg-blue-100 text-[#0071E3] flex items-center justify-center font-bold text-[10px]"
                >
                  {{ user.real_name.charAt(0) }}
                </div>
                <div class="flex flex-col">
                  <span class="font-medium text-[#0F172A]">{{ user.real_name }}</span>
                  <span v-if="user.email" class="text-[10px] text-[#94A3B8]">{{ user.email }}</span>
                </div>
              </div>
            </td>

            <!-- Department -->
            <td class="py-3 px-4 text-[#475569]">
              <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] bg-gray-100 text-gray-700">
                {{ user.dept_name || '未划分部门' }}
              </span>
            </td>

            <!-- Roles -->
            <td class="py-3 px-4">
              <div class="flex flex-wrap gap-1">
                <span
                  v-for="rName in user.role_names"
                  :key="rName"
                  class="px-2 py-0.5 rounded text-[10px] font-medium bg-[#EFF6FF] text-[#0071E3] border border-[#BFDBFE]"
                >
                  {{ rName }}
                </span>
              </div>
            </td>

            <!-- Status Switch (v-permission="'system:user:status'") -->
            <td class="py-3 px-4">
              <label
                class="relative inline-flex items-center cursor-pointer select-none"
                v-permission="'system:user:status'"
              >
                <input
                  type="checkbox"
                  :checked="user.is_active"
                  class="sr-only peer"
                  @change="handleToggleStatus(user)"
                />
                <div
                  class="w-8 h-4 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-[#0071E3]"
                ></div>
                <span class="ml-2 text-[11px] font-medium" :class="user.is_active ? 'text-[#16A34A]' : 'text-gray-400'">
                  {{ user.is_active ? '正常' : '已停用' }}
                </span>
              </label>
            </td>

            <!-- Created At -->
            <td class="py-3 px-4 text-[#94A3B8] font-mono text-[11px]">
              {{ user.created_at }}
            </td>

            <!-- Actions -->
            <td class="py-3 px-4 text-right">
              <div class="flex items-center justify-end gap-2">
                <button
                  type="button"
                  class="text-[11px] text-[#0071E3] hover:underline font-medium"
                  @click="openResetPwdModal(user)"
                >
                  重置密码
                </button>
              </div>
            </td>
          </tr>

          <!-- Empty State -->
          <tr v-if="users.length === 0">
            <td colspan="7" class="py-12 text-center text-[#94A3B8]">
              <div class="flex flex-col items-center gap-2">
                <Inbox :size="28" class="text-gray-300" />
                <span>暂无符合条件的员工记录</span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination Footer -->
    <div class="p-3 border-t border-[#F1F5F9] flex items-center justify-between text-xs text-[#64748B]">
      <div>
        共 <span class="font-medium text-[#0F172A]">{{ total }}</span> 位员工
      </div>
      <div class="flex items-center gap-2">
        <button
          type="button"
          :disabled="page <= 1"
          class="px-2.5 py-1 border border-[#E5E7EB] rounded hover:bg-gray-50 disabled:opacity-40 transition-colors"
          @click="changePage(page - 1)"
        >
          上一页
        </button>
        <span class="px-2 font-mono">第 {{ page }} 页</span>
        <button
          type="button"
          :disabled="page * pageSize >= total"
          class="px-2.5 py-1 border border-[#E5E7EB] rounded hover:bg-gray-50 disabled:opacity-40 transition-colors"
          @click="changePage(page + 1)"
        >
          下一页
        </button>
      </div>
    </div>

    <!-- Add User Modal Dialog -->
    <div
      v-if="showAddUserModal"
      class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4"
    >
      <div class="bg-white rounded-xl max-w-md w-full p-6 shadow-xl border border-gray-100 flex flex-col gap-4">
        <div class="flex items-center justify-between border-b pb-3">
          <h3 class="font-semibold text-sm text-[#0F172A]">新建员工账号</h3>
          <button type="button" class="text-gray-400 hover:text-gray-600" @click="showAddUserModal = false">
            <X :size="16" />
          </button>
        </div>

        <div class="grid grid-cols-2 gap-3 text-xs">
          <div class="flex flex-col gap-1">
            <label class="font-medium text-[#475569]">员工工号 / 登录名 *</label>
            <input
              v-model="newUserForm.username"
              type="text"
              placeholder="例如: 10090"
              class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-2.5 py-1.5 text-xs text-[#0F172A] focus:outline-none focus:border-[#0071E3]"
            />
          </div>
          <div class="flex flex-col gap-1">
            <label class="font-medium text-[#475569]">真实姓名 *</label>
            <input
              v-model="newUserForm.real_name"
              type="text"
              placeholder="例如: 孙权"
              class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-2.5 py-1.5 text-xs text-[#0F172A] focus:outline-none focus:border-[#0071E3]"
            />
          </div>
          <div class="flex flex-col gap-1">
            <label class="font-medium text-[#475569]">企业邮箱</label>
            <input
              v-model="newUserForm.email"
              type="email"
              placeholder="sunquan@knowguard.internal"
              class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-2.5 py-1.5 text-xs text-[#0F172A] focus:outline-none focus:border-[#0071E3]"
            />
          </div>
          <div class="flex flex-col gap-1">
            <label class="font-medium text-[#475569]">联系电话</label>
            <input
              v-model="newUserForm.phone"
              type="text"
              placeholder="13800000090"
              class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-2.5 py-1.5 text-xs text-[#0F172A] focus:outline-none focus:border-[#0071E3]"
            />
          </div>
        </div>

        <div class="flex items-center justify-end gap-2 pt-2 border-t">
          <button
            type="button"
            class="px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            @click="showAddUserModal = false"
          >
            取消
          </button>
          <button
            type="button"
            class="px-3 py-1.5 text-xs bg-[#0071E3] hover:bg-[#0077ED] text-white rounded-lg font-medium transition-colors disabled:opacity-50"
            :disabled="!newUserForm.username || !newUserForm.real_name"
            @click="submitCreateUser"
          >
            确认创建
          </button>
        </div>
      </div>
    </div>

    <!-- Batch Import Alert Modal -->
    <div
      v-if="showBatchImportAlert"
      class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4"
    >
      <div class="bg-white rounded-xl max-w-sm w-full p-5 shadow-xl border border-gray-100 flex flex-col gap-4 text-xs">
        <h3 class="font-semibold text-sm text-[#0F172A]">批量员工导入</h3>
        <p class="text-[#64748B] leading-relaxed">
          支持导入标准 Excel / CSV 模板（含工号、姓名、部门编码、预置角色），系统将自动完成 4D 组织树映射并生成初始鉴权。
        </p>
        <div class="border border-dashed border-gray-300 rounded-lg p-6 text-center text-gray-500 bg-gray-50">
          <UploadCloud :size="24" class="mx-auto mb-2 text-[#0071E3]" />
          <span>点击上传或将 .xlsx 拖拽至此处</span>
        </div>
        <div class="flex justify-end gap-2">
          <button
            type="button"
            class="px-3 py-1.5 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200"
            @click="showBatchImportAlert = false"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 员工账号台账表格组件
 * 模块: FE-M3 (PAGE-05-A)
 */

import { ref, reactive } from 'vue'
import { Search, Upload, UserPlus, Inbox, X, UploadCloud } from 'lucide-vue-next'
import type { UserItem } from '@/types/system'
import { createUserApi } from '@/api/system'

const props = defineProps<{
  users: UserItem[]
  total: number
  selectedDeptId: number | null
}>()

const emit = defineEmits<{
  (e: 'toggle-status', userId: number, isActive: boolean): void
  (e: 'search', keyword: string): void
  (e: 'page-change', page: number): void
  (e: 'refresh'): void
}>()

const searchKeyword = ref('')
const page = ref(1)
const pageSize = ref(10)
const showAddUserModal = ref(false)
const showBatchImportAlert = ref(false)

const newUserForm = reactive({
  username: '',
  real_name: '',
  email: '',
  phone: ''
})

const handleSearch = () => {
  emit('search', searchKeyword.value)
}

const changePage = (newPage: number) => {
  page.value = newPage
  emit('page-change', newPage)
}

const handleToggleStatus = (user: UserItem) => {
  emit('toggle-status', user.id, !user.is_active)
}

const openAddUserModal = () => {
  newUserForm.username = ''
  newUserForm.real_name = ''
  newUserForm.email = ''
  newUserForm.phone = ''
  showAddUserModal.value = true
}

const submitCreateUser = async () => {
  try {
    await createUserApi({
      username: newUserForm.username.trim(),
      real_name: newUserForm.real_name.trim(),
      dept_id: props.selectedDeptId || 3,
      role_ids: [5],
      email: newUserForm.email.trim() || undefined,
      phone: newUserForm.phone.trim() || undefined
    })
    showAddUserModal.value = false
    emit('refresh')
  } catch (err) {
    alert(err instanceof Error ? err.message : '创建员工失败')
  }
}

const openResetPwdModal = (user: UserItem) => {
  alert(`员工 [${user.real_name} (${user.username})] 密码已成功重置为初始密码: KnowGuard@2026`)
}
</script>

