<template>
  <!-- FE-M3: 员工台账表格组件 (PAGE-05-A 原型精准对齐) -->
  <div class="flex-1 bg-white rounded-xl border border-[#E5E7EB] shadow-sm flex flex-col h-full min-w-0 overflow-hidden relative">
    <!-- Top Toast Notification -->
    <div
      v-if="toastMessage"
      class="fixed top-5 right-5 z-50 flex items-center gap-2 px-4 py-2.5 rounded-xl shadow-lg border text-xs font-medium transition-all duration-300 animate-in fade-in slide-in-from-top-4"
      :class="toastType === 'success' ? 'bg-emerald-50 text-emerald-800 border-emerald-200' : 'bg-rose-50 text-rose-800 border-rose-200'"
    >
      <CheckCircle2 v-if="toastType === 'success'" :size="15" class="text-emerald-600 shrink-0" />
      <AlertCircle v-else :size="15" class="text-rose-600 shrink-0" />
      <span>{{ toastMessage }}</span>
    </div>

    <!-- Action Filter Bar -->
    <div class="p-3.5 border-b border-[#F1F5F9] flex flex-wrap items-center justify-between gap-3 shrink-0">
      <!-- Left: Search Box -->
      <div class="relative w-64">
        <Search :size="14" class="absolute left-3 top-2.5 text-[#94A3B8]" />
        <input
          v-model="searchKeyword"
          type="text"
          placeholder="搜索工号、姓名、邮箱..."
          class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg pl-9 pr-7 py-1.5 text-xs text-[#0F172A] placeholder-[#94A3B8] focus:outline-none focus:border-[#0071E3] focus:bg-white transition-colors"
          @keyup.enter="handleSearch"
        />
        <button
          v-if="searchKeyword"
          type="button"
          class="absolute right-2 top-2.5 text-[#94A3B8] hover:text-[#475569]"
          @click="clearSearch"
        >
          <X :size="13" />
        </button>
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
            <th class="py-2.5 px-4 w-32">工号/账号</th>
            <th class="py-2.5 px-4 min-w-[160px]">员工姓名</th>
            <th class="py-2.5 px-4 min-w-[140px]">所属部门</th>
            <th class="py-2.5 px-4 min-w-[180px]">绑定角色</th>
            <th class="py-2.5 px-4 w-28 text-center">账号状态</th>
            <th class="py-2.5 px-4 w-36">入职创建时间</th>
            <th class="py-2.5 px-4 w-28 text-right">操作</th>
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
              <div class="flex flex-col">
                <span>{{ user.username }}</span>
                <span v-if="user.employee_id" class="text-[10px] text-[#94A3B8]">工号: {{ user.employee_id }}</span>
              </div>
            </td>

            <!-- Real Name & Avatar -->
            <td class="py-3 px-4">
              <div class="flex items-center gap-2">
                <div
                  class="w-7 h-7 rounded-full bg-blue-100 text-[#0071E3] flex items-center justify-center font-bold text-[11px] shrink-0"
                >
                  {{ user.real_name ? user.real_name.charAt(0) : 'U' }}
                </div>
                <div class="flex flex-col min-w-0">
                  <div class="flex items-center gap-1.5">
                    <span class="font-medium text-[#0F172A]">{{ user.real_name }}</span>
                    <span
                      v-if="user.is_superuser"
                      class="text-[9px] px-1 py-0.2 rounded bg-amber-50 text-amber-600 border border-amber-200 font-medium"
                    >
                      超管
                    </span>
                  </div>
                  <span v-if="user.email" class="text-[10px] text-[#94A3B8] truncate max-w-[160px]">{{ user.email }}</span>
                </div>
              </div>
            </td>

            <!-- Department -->
            <td class="py-3 px-4 text-[#475569]">
              <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] bg-slate-100 text-slate-700 border border-slate-200 font-medium">
                {{ user.dept_name || user.department_name || '未划分部门' }}
              </span>
            </td>

            <!-- Roles -->
            <td class="py-3 px-4">
              <div class="flex flex-wrap gap-1">
                <span
                  v-for="rName in getRoleNames(user)"
                  :key="rName"
                  class="px-2 py-0.5 rounded text-[10px] font-medium bg-[#EFF6FF] text-[#0071E3] border border-[#BFDBFE]"
                >
                  {{ rName }}
                </span>
                <span
                  v-if="getRoleNames(user).length === 0"
                  class="text-[10px] text-[#94A3B8]"
                >
                  暂无绑定角色
                </span>
              </div>
            </td>

            <!-- Status Switch (v-permission="'system:user:status'") -->
            <td class="py-3 px-4 text-center">
              <div class="inline-flex items-center gap-1.5">
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
                    class="w-7 h-4 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-[#0071E3]"
                  ></div>
                </label>
                <span
                  class="text-[11px] font-medium"
                  :class="user.is_active ? 'text-[#16A34A]' : 'text-gray-400'"
                >
                  {{ user.is_active ? '正常' : '已停用' }}
                </span>
              </div>
            </td>

            <!-- Created At -->
            <td class="py-3 px-4 text-[#94A3B8] font-mono text-[11px] whitespace-nowrap">
              {{ formatDateTime(user.created_at) }}
            </td>

            <!-- Actions -->
            <td class="py-3 px-4 text-right whitespace-nowrap">
              <button
                type="button"
                class="text-[11px] text-[#0071E3] hover:underline font-medium inline-flex items-center gap-1"
                @click="openResetPwdModal(user)"
                v-permission="'system:user:manage'"
              >
                <KeyRound :size="12" />
                <span>重置密码</span>
              </button>
            </td>
          </tr>

          <!-- Empty State -->
          <tr v-if="users.length === 0">
            <td colspan="7" class="py-16 text-center text-[#94A3B8]">
              <div class="flex flex-col items-center gap-2">
                <div class="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-slate-400">
                  <Inbox :size="24" />
                </div>
                <span class="font-medium text-slate-600">未找到符合条件的员工记录</span>
                <span class="text-slate-400 text-[11px]">请尝试切换组织架构节点或更换检索关键字</span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination Footer -->
    <div class="p-3 border-t border-[#F1F5F9] bg-[#FAFAFA]/60 flex flex-wrap items-center justify-between gap-3 text-xs text-[#64748B] shrink-0">
      <div>
        共 <span class="font-medium text-[#0F172A]">{{ total }}</span> 位员工
      </div>
      <div class="flex items-center gap-2">
        <button
          type="button"
          :disabled="page <= 1"
          class="px-2.5 py-1 border border-[#E5E7EB] rounded bg-white hover:bg-gray-50 disabled:opacity-40 disabled:hover:bg-white transition-colors"
          @click="changePage(page - 1)"
        >
          上一页
        </button>
        <span class="px-2 font-mono text-[#0F172A]">第 {{ page }} / {{ totalPages || 1 }} 页</span>
        <button
          type="button"
          :disabled="page >= totalPages"
          class="px-2.5 py-1 border border-[#E5E7EB] rounded bg-white hover:bg-gray-50 disabled:opacity-40 disabled:hover:bg-white transition-colors"
          @click="changePage(page + 1)"
        >
          下一页
        </button>
      </div>
    </div>

    <!-- Add User Modal Dialog -->
    <div
      v-if="showAddUserModal"
      class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-200"
    >
      <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-gray-100 flex flex-col gap-4 text-xs">
        <div class="flex items-center justify-between border-b border-[#F1F5F9] pb-3">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-lg bg-blue-50 text-[#0071E3] flex items-center justify-center border border-blue-100">
              <UserPlus :size="16" />
            </div>
            <div>
              <h3 class="font-semibold text-sm text-[#0F172A]">新建企业员工账号</h3>
              <p class="text-[11px] text-[#64748B]">配置基本身份信息、所属部门与授权 RBAC 角色</p>
            </div>
          </div>
          <button type="button" class="text-gray-400 hover:text-gray-600 p-1 rounded-lg" @click="showAddUserModal = false">
            <X :size="16" />
          </button>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <!-- Employee ID -->
          <div class="flex flex-col gap-1">
            <label class="font-medium text-[#475569]">员工工号 *</label>
            <input
              v-model="newUserForm.employee_id"
              type="text"
              placeholder="例如: 10090"
              class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-2.5 py-1.5 text-xs text-[#0F172A] focus:outline-none focus:border-[#0071E3]"
            />
          </div>

          <!-- Username -->
          <div class="flex flex-col gap-1">
            <label class="font-medium text-[#475569]">登录账号名 *</label>
            <input
              v-model="newUserForm.username"
              type="text"
              placeholder="例如: sunquan"
              class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-2.5 py-1.5 text-xs text-[#0F172A] focus:outline-none focus:border-[#0071E3]"
            />
          </div>

          <!-- Real Name -->
          <div class="flex flex-col gap-1">
            <label class="font-medium text-[#475569]">真实姓名 *</label>
            <input
              v-model="newUserForm.real_name"
              type="text"
              placeholder="例如: 孙权"
              class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-2.5 py-1.5 text-xs text-[#0F172A] focus:outline-none focus:border-[#0071E3]"
            />
          </div>

          <!-- Initial Password -->
          <div class="flex flex-col gap-1">
            <label class="font-medium text-[#475569]">初始密码</label>
            <input
              v-model="newUserForm.password"
              type="text"
              placeholder="默认: KnowGuard@2026"
              class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-2.5 py-1.5 text-xs text-[#0F172A] focus:outline-none focus:border-[#0071E3]"
            />
          </div>

          <!-- Department Selector -->
          <div class="flex flex-col gap-1 col-span-2">
            <label class="font-medium text-[#475569]">所属部门架构节点 *</label>
            <select
              v-model="newUserForm.department_id"
              class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-2.5 py-1.5 text-xs text-[#0F172A] focus:outline-none focus:border-[#0071E3]"
            >
              <option v-for="d in flatDepartments" :key="d.id" :value="d.id">
                {{ d.name }}
              </option>
            </select>
          </div>

          <!-- Roles Multi Select -->
          <div class="flex flex-col gap-1.5 col-span-2">
            <label class="font-medium text-[#475569]">授予系统 RBAC 角色</label>
            <div class="flex flex-wrap gap-2 p-2.5 bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg max-h-28 overflow-y-auto">
              <label
                v-for="role in roles"
                :key="role.id"
                class="flex items-center gap-1.5 px-2 py-1 rounded text-xs cursor-pointer border transition-colors select-none"
                :class="
                  newUserForm.role_ids.includes(role.id)
                    ? 'bg-blue-50 border-[#0071E3] text-[#0071E3]'
                    : 'bg-white border-[#E2E8F0] text-[#475569] hover:bg-slate-50'
                "
              >
                <input
                  type="checkbox"
                  class="sr-only"
                  :checked="newUserForm.role_ids.includes(role.id)"
                  @change="toggleRoleSelection(role.id)"
                />
                <Shield :size="12" />
                <span>{{ role.role_name || role.name }}</span>
              </label>
            </div>
          </div>

          <!-- Email -->
          <div class="flex flex-col gap-1">
            <label class="font-medium text-[#475569]">企业工作邮箱</label>
            <input
              v-model="newUserForm.email"
              type="email"
              placeholder="sunquan@knowguard.internal"
              class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-2.5 py-1.5 text-xs text-[#0F172A] focus:outline-none focus:border-[#0071E3]"
            />
          </div>

          <!-- Phone -->
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

        <div class="flex items-center justify-end gap-2 pt-2 border-t border-[#F1F5F9]">
          <button
            type="button"
            :disabled="isSubmitting"
            class="px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-100 rounded-lg transition-colors font-medium"
            @click="showAddUserModal = false"
          >
            取消
          </button>
          <button
            type="button"
            class="px-3.5 py-1.5 text-xs bg-[#0071E3] hover:bg-[#0077ED] text-white rounded-lg font-medium transition-colors disabled:opacity-50 inline-flex items-center gap-1.5 shadow-sm"
            :disabled="!newUserForm.username.trim() || !newUserForm.real_name.trim() || isSubmitting"
            @click="submitCreateUser"
          >
            <Loader2 v-if="isSubmitting" :size="13" class="animate-spin" />
            <span>{{ isSubmitting ? '正在创建...' : '确认创建员工' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Reset Password Modal Dialog -->
    <div
      v-if="userToResetPwd"
      class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-200"
    >
      <div class="bg-white rounded-2xl max-w-sm w-full p-5 shadow-2xl border border-gray-100 flex flex-col gap-3.5 text-xs">
        <div class="flex items-center justify-between border-b border-[#F1F5F9] pb-3">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center border border-amber-100">
              <KeyRound :size="16" />
            </div>
            <div>
              <h3 class="font-semibold text-sm text-[#0F172A]">重置员工登录密码</h3>
              <p class="text-[11px] text-[#64748B]">重置后员工须使用新密码进行登录认证</p>
            </div>
          </div>
          <button type="button" class="text-gray-400 hover:text-gray-600 p-1" @click="userToResetPwd = null">
            <X :size="16" />
          </button>
        </div>

        <!-- Target User Meta -->
        <div class="bg-slate-50 border border-slate-200 rounded-xl p-3 flex flex-col gap-1 text-[11px]">
          <div class="flex justify-between text-slate-500">
            <span>目标员工:</span>
            <span class="font-medium text-slate-900">{{ userToResetPwd.real_name }} ({{ userToResetPwd.username }})</span>
          </div>
          <div class="flex justify-between text-slate-500">
            <span>所属部门:</span>
            <span class="font-medium text-slate-900">{{ userToResetPwd.dept_name || userToResetPwd.department_name || '未设置' }}</span>
          </div>
        </div>

        <!-- New Password Input -->
        <div class="flex flex-col gap-1.5">
          <div class="flex items-center justify-between">
            <label class="font-medium text-[#475569]">设置新密码 *</label>
            <button
              type="button"
              class="text-[10px] text-[#0071E3] hover:underline"
              @click="resetPwdInput = 'KnowGuard@2026'"
            >
              填充默认密码
            </button>
          </div>
          <input
            v-model="resetPwdInput"
            type="text"
            placeholder="请输入至少 6 位字符新密码"
            class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-3 py-2 text-xs text-[#0F172A] font-mono focus:outline-none focus:border-[#0071E3]"
          />
        </div>

        <div class="flex items-center justify-end gap-2 pt-2 border-t border-[#F1F5F9]">
          <button
            type="button"
            :disabled="isResettingPwd"
            class="px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-100 rounded-lg transition-colors font-medium"
            @click="userToResetPwd = null"
          >
            取消
          </button>
          <button
            type="button"
            :disabled="!resetPwdInput.trim() || resetPwdInput.length < 6 || isResettingPwd"
            class="px-3.5 py-1.5 text-xs bg-[#0071E3] hover:bg-[#0077ED] text-white rounded-lg font-medium transition-colors disabled:opacity-50 inline-flex items-center gap-1.5 shadow-sm"
            @click="submitResetPassword"
          >
            <Loader2 v-if="isResettingPwd" :size="13" class="animate-spin" />
            <span>{{ isResettingPwd ? '正在重置...' : '确认重置密码' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Batch Import Alert Modal -->
    <div
      v-if="showBatchImportAlert"
      class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-200"
    >
      <div class="bg-white rounded-2xl max-w-sm w-full p-5 shadow-2xl border border-gray-100 flex flex-col gap-4 text-xs">
        <h3 class="font-semibold text-sm text-[#0F172A]">批量员工导入</h3>
        <p class="text-[#64748B] leading-relaxed">
          支持导入标准 Excel / CSV 模板（含工号、姓名、部门编码、预置角色），系统将自动完成 4D 组织树映射并生成初始鉴权。
        </p>
        <div class="border-2 border-dashed border-gray-200 rounded-xl p-6 text-center text-gray-500 bg-[#F8FAFC]">
          <UploadCloud :size="24" class="mx-auto mb-2 text-[#0071E3]" />
          <span>点击上传或将 .xlsx / .csv 拖拽至此处</span>
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

import { ref, reactive, computed } from 'vue'
import {
  Search,
  Upload,
  UserPlus,
  Inbox,
  X,
  UploadCloud,
  CheckCircle2,
  AlertCircle,
  KeyRound,
  Shield,
  Loader2
} from 'lucide-vue-next'
import type { UserItem, DepartmentNode, RoleItem } from '@/types/system'
import { createUserApi, resetUserPasswordApi } from '@/api/system'

const props = withDefaults(
  defineProps<{
    users: UserItem[]
    total: number
    selectedDeptId: number | null
    departments?: DepartmentNode[]
    roles?: RoleItem[]
  }>(),
  {
    departments: () => [],
    roles: () => []
  }
)

const emit = defineEmits<{
  (e: 'toggle-status', userId: number, isActive: boolean): void
  (e: 'search', keyword: string): void
  (e: 'page-change', page: number): void
  (e: 'refresh'): void
}>()

const searchKeyword = ref('')
const page = ref(1)
const pageSize = ref(10)
const totalPages = computed(() => Math.ceil(props.total / pageSize.value) || 1)

// 弹窗状态
const showAddUserModal = ref(false)
const showBatchImportAlert = ref(false)
const userToResetPwd = ref<UserItem | null>(null)
const resetPwdInput = ref('KnowGuard@2026')
const isSubmitting = ref(false)
const isResettingPwd = ref(false)

// Toast 提示
const toastMessage = ref('')
const toastType = ref<'success' | 'error'>('success')
let toastTimer: ReturnType<typeof setTimeout> | null = null

const showToast = (msg: string, type: 'success' | 'error' = 'success') => {
  toastMessage.value = msg
  toastType.value = type
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    toastMessage.value = ''
  }, 3000)
}

// 新建员工表单
const newUserForm = reactive({
  employee_id: '',
  username: '',
  real_name: '',
  password: 'KnowGuard@2026',
  department_id: 1,
  role_ids: [] as number[],
  email: '',
  phone: ''
})

// 展平部门树便于下拉选择
interface FlatDept {
  id: number
  name: string
}

const flatDepartments = computed<FlatDept[]>(() => {
  const list: FlatDept[] = []
  const traverse = (nodes: DepartmentNode[], depth = 0) => {
    for (const node of nodes) {
      list.push({
        id: node.id,
        name: `${'— '.repeat(depth)}${node.name}`
      })
      if (node.children && node.children.length > 0) {
        traverse(node.children, depth + 1)
      }
    }
  }
  traverse(props.departments)
  return list.length > 0 ? list : [{ id: 1, name: '集团总部' }]
})

const getRoleNames = (user: UserItem): string[] => {
  if (user.role_names && user.role_names.length > 0) {
    return user.role_names
  }
  if (user.roles && user.roles.length > 0) {
    return user.roles.map((r) => r.name)
  }
  return []
}

const formatDateTime = (dtStr?: string): string => {
  if (!dtStr) return '-'
  return dtStr.replace('T', ' ').substring(0, 16)
}

const handleSearch = () => {
  page.value = 1
  emit('search', searchKeyword.value)
}

const clearSearch = () => {
  searchKeyword.value = ''
  page.value = 1
  emit('search', '')
}

const changePage = (newPage: number) => {
  page.value = newPage
  emit('page-change', newPage)
}

const handleToggleStatus = (user: UserItem) => {
  const nextStatus = !user.is_active
  emit('toggle-status', user.id, nextStatus)
  showToast(`员工账号 [${user.real_name}] 状态已设为: ${nextStatus ? '正常启用' : '冻结停用'}`)
}

const toggleRoleSelection = (roleId: number) => {
  const idx = newUserForm.role_ids.indexOf(roleId)
  if (idx !== -1) {
    newUserForm.role_ids.splice(idx, 1)
  } else {
    newUserForm.role_ids.push(roleId)
  }
}

const openAddUserModal = () => {
  newUserForm.employee_id = `10${Math.floor(100 + Math.random() * 900)}`
  newUserForm.username = ''
  newUserForm.real_name = ''
  newUserForm.password = 'KnowGuard@2026'
  newUserForm.department_id = props.selectedDeptId || (props.departments[0]?.id ?? 1)
  newUserForm.role_ids = props.roles.length > 0 ? [props.roles[0].id] : [1]
  newUserForm.email = ''
  newUserForm.phone = ''
  showAddUserModal.value = true
}

const submitCreateUser = async () => {
  if (!newUserForm.username.trim() || !newUserForm.real_name.trim()) return
  isSubmitting.value = true
  try {
    await createUserApi({
      employee_id: newUserForm.employee_id.trim() || undefined,
      username: newUserForm.username.trim(),
      real_name: newUserForm.real_name.trim(),
      password: newUserForm.password.trim() || 'KnowGuard@2026',
      department_id: newUserForm.department_id,
      role_ids: newUserForm.role_ids,
      email: newUserForm.email.trim() || undefined,
      phone: newUserForm.phone.trim() || undefined
    })
    showAddUserModal.value = false
    showToast(`员工账号 [${newUserForm.real_name}] 创建成功`)
    emit('refresh')
  } catch (err) {
    showToast(err instanceof Error ? err.message : '创建员工失败', 'error')
  } finally {
    isSubmitting.value = false
  }
}

const openResetPwdModal = (user: UserItem) => {
  userToResetPwd.value = user
  resetPwdInput.value = 'KnowGuard@2026'
}

const submitResetPassword = async () => {
  if (!userToResetPwd.value || !resetPwdInput.value.trim()) return
  isResettingPwd.value = true
  const userName = userToResetPwd.value.real_name
  const targetId = userToResetPwd.value.id
  const newPwd = resetPwdInput.value.trim()
  try {
    await resetUserPasswordApi(targetId, newPwd)
    userToResetPwd.value = null
    showToast(`员工 [${userName}] 密码重置成功，新密码已生效: ${newPwd}`)
  } catch (err) {
    showToast(err instanceof Error ? err.message : '重置密码失败', 'error')
  } finally {
    isResettingPwd.value = false
  }
}
</script>
