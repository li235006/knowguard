<template>
  <!-- PAGE-04: 四维数据权限一体化配置弹窗 (4D-RBAC Security Modal) -->
  <div
    v-if="visible"
    class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-200"
    @click.self="emit('close')"
  >
    <div
      class="bg-white rounded-2xl w-full max-w-[840px] shadow-2xl border border-gray-100 flex flex-col overflow-hidden text-xs"
    >
      <!-- Modal Header -->
      <div class="px-6 py-3.5 border-b border-[#F1F5F9] flex items-center justify-between bg-white">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-lg bg-[#EFF6FF] text-[#0071E3] flex items-center justify-center border border-[#BFDBFE]">
            <ShieldCheck :size="18" />
          </div>
          <div class="flex flex-col">
            <div class="flex items-center gap-2">
              <h2 class="text-sm font-semibold text-[#0F172A] tracking-tight">四维数据权限一体化配置</h2>
              <span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono bg-gray-100 text-gray-700 font-medium">
                KU-{{ unit?.id }} · {{ unit?.title }}
              </span>
            </div>
            <p class="text-[11px] text-[#64748B] mt-0.5">
              4D-RBAC 动态鉴权矩阵 · 细粒度数据隔离与前台静默脱敏
            </p>
          </div>
        </div>

        <button
          type="button"
          class="w-7 h-7 rounded-lg bg-gray-100 hover:bg-gray-200 flex items-center justify-center text-gray-500 hover:text-gray-800 transition-colors"
          @click="emit('close')"
        >
          <X :size="14" />
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="py-24 flex flex-col items-center justify-center gap-3 text-xs text-[#64748B]">
        <Loader2 :size="24" class="animate-spin text-[#0071E3]" />
        <span>正在读取 4D 权限策略与组织架构数据...</span>
      </div>

      <!-- Modal Body -->
      <div v-else class="p-5 space-y-3.5 bg-white">
        <!-- Dimension 0: Global Public Switch -->
        <div
          class="rounded-xl border p-3 flex items-center justify-between transition-colors"
          :class="policyForm.is_global ? 'bg-[#EFF6FF]/60 border-[#BFDBFE]' : 'bg-[#F9FAFB] border-[#E5E7EB]'"
        >
          <div class="flex items-center gap-2.5">
            <div
              class="w-7 h-7 rounded-lg flex items-center justify-center"
              :class="policyForm.is_global ? 'bg-[#0071E3] text-white' : 'bg-gray-200 text-gray-600'"
            >
              <Globe :size="15" />
            </div>
            <div class="flex flex-col">
              <div class="flex items-center gap-2">
                <span class="font-semibold text-xs text-[#0F172A]">全局全员公开 (Public Access)</span>
                <span
                  class="px-1.5 py-0.2 rounded text-[10px] font-medium"
                  :class="policyForm.is_global ? 'bg-emerald-100 text-emerald-800' : 'bg-gray-200 text-gray-600'"
                >
                  {{ policyForm.is_global ? '公开模式' : '精准隔离模式' }}
                </span>
              </div>
              <span class="text-[11px] text-[#64748B] mt-0.5">
                开启后全员在册员工可查，忽略下方细粒度配置；关闭则启用四维权限（部门/角色/工号）精准隔离
              </span>
            </div>
          </div>

          <!-- Switch Toggle Button -->
          <div class="flex items-center gap-2">
            <span class="text-[11px] font-medium select-none" :class="policyForm.is_global ? 'text-[#0071E3]' : 'text-gray-500'">
              {{ policyForm.is_global ? '全员公开 (已开启)' : '受限访问 (已关闭)' }}
            </span>
            <label class="relative inline-flex items-center cursor-pointer select-none">
              <input
                type="checkbox"
                v-model="policyForm.is_global"
                class="sr-only peer"
                @change="onGlobalToggle"
              />
              <div
                class="w-9 h-5 bg-gray-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-[#0071E3]"
              ></div>
            </label>
          </div>
        </div>

        <!-- 3-Column Permissions Grid (PAGE-04 原型对齐) -->
        <div class="relative">
          <!-- Global Mask Overlay if Public Access is Enabled -->
          <div
            v-if="policyForm.is_global"
            class="absolute inset-0 bg-white/75 backdrop-blur-[1px] z-10 rounded-xl border border-dashed border-[#BFDBFE] flex flex-col items-center justify-center gap-2 select-none"
          >
            <div class="w-8 h-8 rounded-full bg-blue-100 text-[#0071E3] flex items-center justify-center">
              <Globe :size="16" />
            </div>
            <p class="font-medium text-xs text-[#0F172A]">全局全员公开模式生效中</p>
            <p class="text-[11px] text-[#64748B]">全企业所有员工均享有自然检索权限，关闭上方开关即可自定义四维细粒度授权策略</p>
            <button
              type="button"
              class="mt-1 px-3 py-1 rounded-lg bg-white border border-[#E5E7EB] hover:bg-gray-50 text-[11px] text-[#0071E3] font-medium shadow-sm transition-colors"
              @click="policyForm.is_global = false; onGlobalToggle()"
            >
              切换为细粒度授权模式
            </button>
          </div>

          <!-- 3-Column Container -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-3 h-[300px]">
            <!-- Column 1: 部门架构范围 -->
            <div class="bg-white rounded-xl border border-[#E5E7EB] p-3 flex flex-col h-full min-w-0">
              <!-- Col 1 Header -->
              <div class="flex items-center justify-between pb-2 border-b border-[#F1F5F9] shrink-0">
                <div class="flex items-center gap-1.5">
                  <Building2 :size="14" class="text-[#0071E3]" />
                  <span class="font-semibold text-xs text-[#0F172A]">部门架构范围</span>
                </div>
                <label class="flex items-center gap-1 cursor-pointer select-none text-[11px] text-[#0071E3]">
                  <input
                    type="checkbox"
                    v-model="cascadeSubDepts"
                    class="rounded border-gray-300 text-[#0071E3] focus:ring-0"
                  />
                  <span>包含子部门</span>
                </label>
              </div>

              <!-- Dept Tree List -->
              <div class="flex-1 overflow-y-auto mt-2 space-y-1 pr-1">
                <div
                  v-for="dept in flattenedDepts"
                  :key="dept.id"
                  class="flex items-center justify-between px-2 py-1.5 rounded-lg text-xs hover:bg-[#F8FAFC] transition-colors cursor-pointer"
                  :class="policyForm.department_ids.includes(dept.id) ? 'bg-blue-50 text-[#0071E3] font-medium' : 'text-[#334155]'"
                  :style="{ paddingLeft: `${dept.depth * 14 + 8}px` }"
                  @click="toggleDept(dept)"
                >
                  <div class="flex items-center gap-1.5 truncate">
                    <Folder :size="12" :class="policyForm.department_ids.includes(dept.id) ? 'text-[#0071E3]' : 'text-gray-400'" />
                    <span class="truncate">{{ dept.name }}</span>
                  </div>
                  <input
                    type="checkbox"
                    :checked="policyForm.department_ids.includes(dept.id)"
                    class="rounded border-gray-300 text-[#0071E3] focus:ring-0 shrink-0 pointer-events-none"
                  />
                </div>
              </div>

              <!-- Col 1 Footer Summary -->
              <div class="pt-2 border-t border-[#F1F5F9] text-[11px] text-[#64748B] flex justify-between shrink-0">
                <span>已授权部门:</span>
                <span class="font-mono font-medium text-[#0071E3]">{{ policyForm.department_ids.length }} 个</span>
              </div>
            </div>

            <!-- Column 2: 角色策略白名单 -->
            <div class="bg-white rounded-xl border border-[#E5E7EB] p-3 flex flex-col h-full min-w-0">
              <!-- Col 2 Header -->
              <div class="flex items-center justify-between pb-2 border-b border-[#F1F5F9] shrink-0">
                <div class="flex items-center gap-1.5">
                  <Shield :size="14" class="text-amber-600" />
                  <span class="font-semibold text-xs text-[#0F172A]">角色策略白名单</span>
                </div>
                <span class="text-[11px] text-[#64748B] font-mono">
                  {{ policyForm.role_ids.length }} 个角色
                </span>
              </div>

              <!-- Selected Role Tags Area -->
              <div class="flex-1 overflow-y-auto mt-2 space-y-1.5 pr-1">
                <div
                  v-if="policyForm.role_ids.length === 0"
                  class="h-full flex items-center justify-center text-center text-gray-400 text-[11px] p-4"
                >
                  暂未授权任何角色，请在下方选择添加
                </div>

                <div
                  v-for="role in selectedRoles"
                  :key="role.id"
                  class="flex items-center justify-between px-2.5 py-1.5 rounded-lg border border-[#FDE68A] bg-[#FFFBEB] text-[#B45309] text-xs font-medium"
                >
                  <span class="truncate">{{ role.role_name }}</span>
                  <button
                    type="button"
                    class="text-[#B45309] hover:text-red-600 p-0.5 ml-1 transition-colors"
                    title="移除该角色授权"
                    @click="removeRole(role.id)"
                  >
                    <X :size="12" />
                  </button>
                </div>
              </div>

              <!-- Add Role Selector Box -->
              <div class="pt-2 border-t border-[#F1F5F9] shrink-0">
                <div class="relative">
                  <select
                    class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-2.5 py-1.5 text-xs text-[#475569] focus:outline-none focus:border-[#0071E3] cursor-pointer"
                    @change="onAddRoleSelect"
                  >
                    <option value="" disabled selected>+ 选择或添加授权角色...</option>
                    <option
                      v-for="role in unselectedRoles"
                      :key="role.id"
                      :value="role.id"
                    >
                      + {{ role.role_name }} ({{ role.role_code }})
                    </option>
                  </select>
                </div>
              </div>
            </div>

            <!-- Column 3: 指定个人白名单 (工号白名单) -->
            <div class="bg-white rounded-xl border border-[#E5E7EB] p-3 flex flex-col h-full min-w-0">
              <!-- Col 3 Header -->
              <div class="flex items-center justify-between pb-2 border-b border-[#F1F5F9] shrink-0">
                <div class="flex items-center gap-1.5">
                  <UserCheck :size="14" class="text-purple-600" />
                  <span class="font-semibold text-xs text-[#0F172A]">指定个人白名单</span>
                </div>
                <span class="text-[11px] text-[#64748B] font-mono">
                  {{ policyForm.user_ids.length }} 位特权直属
                </span>
              </div>

              <!-- Selected User Chips Area -->
              <div class="flex-1 overflow-y-auto mt-2 space-y-1.5 pr-1">
                <div
                  v-if="policyForm.user_ids.length === 0"
                  class="h-full flex items-center justify-center text-center text-gray-400 text-[11px] p-4"
                >
                  暂无独立工号特权，可通过下方搜索员工加入白名单
                </div>

                <div
                  v-for="user in selectedUsers"
                  :key="user.id"
                  class="flex items-center justify-between px-2.5 py-1.5 rounded-lg border border-purple-200 bg-[#FAF5FF] text-[#7E22CE] text-xs font-medium"
                >
                  <div class="flex items-center gap-2 truncate">
                    <div class="w-5 h-5 rounded-full bg-purple-200 text-[#7E22CE] flex items-center justify-center text-[10px] font-bold shrink-0">
                      {{ user.real_name.charAt(0) }}
                    </div>
                    <span class="truncate">{{ user.real_name }} ({{ user.username }})</span>
                  </div>
                  <button
                    type="button"
                    class="text-[#7E22CE] hover:text-red-600 p-0.5 ml-1 transition-colors shrink-0"
                    title="移除该员工白名单"
                    @click="removeUser(user.id)"
                  >
                    <X :size="12" />
                  </button>
                </div>
              </div>

              <!-- Add User Search Box -->
              <div class="pt-2 border-t border-[#F1F5F9] shrink-0 relative">
                <div class="relative">
                  <Search :size="12" class="absolute left-2.5 top-2.5 text-[#94A3B8]" />
                  <input
                    v-model="userSearchQuery"
                    type="text"
                    placeholder="搜索工号、姓名添加..."
                    class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg pl-7 pr-3 py-1.5 text-xs text-[#0F172A] placeholder-[#94A3B8] focus:outline-none focus:border-[#0071E3]"
                    @focus="showUserDropdown = true"
                  />
                </div>

                <!-- Autocomplete Dropdown -->
                <div
                  v-if="showUserDropdown && filteredCandidateUsers.length > 0"
                  class="absolute bottom-full mb-1 left-0 right-0 bg-white border border-[#E5E7EB] rounded-xl shadow-xl max-h-36 overflow-y-auto z-20 p-1"
                >
                  <div
                    v-for="cand in filteredCandidateUsers"
                    :key="cand.id"
                    class="flex items-center justify-between px-2.5 py-1.5 rounded-lg hover:bg-purple-50 cursor-pointer transition-colors"
                    @click="addUser(cand.id)"
                  >
                    <div class="flex items-center gap-2">
                      <span class="font-medium text-[#0F172A]">{{ cand.real_name }}</span>
                      <span class="text-[10px] text-gray-400 font-mono">{{ cand.username }} · {{ cand.dept_name }}</span>
                    </div>
                    <Plus :size="12" class="text-purple-600" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Policy Logic Banner (OR 充分条件说明) -->
        <div class="rounded-xl border border-[#BFDBFE] bg-[#EFF6FF] p-2.5 flex items-center gap-2.5 text-[11px] text-[#1E40AF]">
          <Info :size="16" class="text-[#0071E3] shrink-0" />
          <p class="leading-relaxed">
            <span class="font-semibold">生效机制：</span>
            四维实体采用逻辑充分条件（OR 规则），员工命中任意一维即可放行。未命中员工在前台提问时将触发静默未命中模式，杜绝信息泄露与阶层隔阂。
          </p>
        </div>
      </div>

      <!-- Modal Footer -->
      <div class="px-6 py-3 border-t border-[#F1F5F9] bg-[#FAFAFA] flex items-center justify-between">
        <!-- Left: Reset to Default Private Button -->
        <button
          type="button"
          :disabled="saving"
          class="text-xs text-[#64748B] hover:text-[#0F172A] transition-colors hover:underline"
          @click="resetToPrivateDefault"
        >
          恢复私有默认
        </button>

        <!-- Right: Actions -->
        <div class="flex items-center gap-2.5">
          <button
            type="button"
            :disabled="saving"
            class="px-4 py-1.5 rounded-lg text-xs font-medium text-[#475569] hover:bg-gray-200/70 transition-colors"
            @click="emit('close')"
          >
            取消
          </button>
          <button
            type="button"
            :disabled="saving || loading"
            class="px-5 py-1.5 rounded-lg bg-[#0071E3] hover:bg-[#0077ED] text-white text-xs font-medium shadow-sm transition-all inline-flex items-center gap-1.5 disabled:opacity-50 active:scale-[0.98]"
            @click="savePolicy"
          >
            <Loader2 v-if="saving" :size="13" class="animate-spin" />
            <span>{{ saving ? '正在同步...' : '保存并同步索引 (⌘S)' }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 四维数据权限一体化配置弹窗组件
 * 模块: FE-M4 / M3: Guard (PAGE-04 原型对齐)
 */

import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import {
  ShieldCheck,
  Shield,
  Building2,
  UserCheck,
  Globe,
  Folder,
  X,
  Plus,
  Search,
  Info,
  Loader2
} from 'lucide-vue-next'
import type { KnowledgeUnit, PermissionPolicyConfig } from '@/types/knowledge'
import type { DepartmentNode, RoleItem, UserItem } from '@/types/system'
import { getUnitPolicyApi, updateUnitPolicyApi } from '@/api/knowledge'
import { getDepartmentTreeApi, getRolesListApi, getUsersListApi } from '@/api/system'

const props = defineProps<{
  unit: KnowledgeUnit | null
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'saved', policy: PermissionPolicyConfig): void
}>()

// 状态管理
const loading = ref<boolean>(false)
const saving = ref<boolean>(false)
const cascadeSubDepts = ref<boolean>(true)
const userSearchQuery = ref<string>('')
const showUserDropdown = ref<boolean>(false)

// 4D 策略表单 (镜像对齐 backend/app/schemas/guard.py)
const policyForm = reactive<PermissionPolicyConfig>({
  unit_id: 0,
  is_global: false,
  is_public: false,
  department_ids: [],
  role_ids: [],
  user_ids: []
})

// 系统实体字典
const rawDepartmentTree = ref<DepartmentNode[]>([])
const allRoles = ref<RoleItem[]>([])
const allUsers = ref<UserItem[]>([])

interface FlattenedDept {
  id: number
  name: string
  parent_id: number | null
  depth: number
  childIds: number[]
}

// 扁平化部门树结构（带缩进深度和级联子 ID）
const flattenedDepts = computed<FlattenedDept[]>(() => {
  const result: FlattenedDept[] = []

  const collectChildIds = (node: DepartmentNode): number[] => {
    let ids: number[] = [node.id]
    if (node.children && node.children.length > 0) {
      for (const c of node.children) {
        ids = ids.concat(collectChildIds(c))
      }
    }
    return ids
  }

  const traverse = (nodes: DepartmentNode[], depth: number) => {
    for (const node of nodes) {
      result.push({
        id: node.id,
        name: node.name,
        parent_id: node.parent_id ?? null,
        depth,
        childIds: collectChildIds(node)
      })
      if (node.children && node.children.length > 0) {
        traverse(node.children, depth + 1)
      }
    }
  }

  traverse(rawDepartmentTree.value, 0)
  return result
})

// 角色选中与未选中列表
const selectedRoles = computed(() => {
  return allRoles.value.filter((r) => policyForm.role_ids.includes(r.id))
})

const unselectedRoles = computed(() => {
  return allRoles.value.filter((r) => !policyForm.role_ids.includes(r.id))
})

// 用户白名单与候选搜索
const selectedUsers = computed(() => {
  return allUsers.value.filter((u) => policyForm.user_ids.includes(u.id))
})

const filteredCandidateUsers = computed(() => {
  const unselected = allUsers.value.filter((u) => !policyForm.user_ids.includes(u.id))
  if (!userSearchQuery.value.trim()) {
    return unselected.slice(0, 8)
  }
  const q = userSearchQuery.value.trim().toLowerCase()
  return unselected.filter(
    (u) =>
      u.real_name.toLowerCase().includes(q) ||
      u.username.toLowerCase().includes(q) ||
      (u.dept_name && u.dept_name.toLowerCase().includes(q))
  ).slice(0, 10)
})

// 加载基础组织与策略数据
const loadAllData = async (unitId: number) => {
  loading.value = true
  try {
    const [policyRes, deptRes, roleRes, userRes] = await Promise.all([
      getUnitPolicyApi(unitId),
      getDepartmentTreeApi(),
      getRolesListApi(),
      getUsersListApi({ page: 1, page_size: 100 })
    ])

    if (deptRes.data) rawDepartmentTree.value = deptRes.data
    if (roleRes.data) allRoles.value = roleRes.data
    if (userRes.data?.items) allUsers.value = userRes.data.items

    if (policyRes.data) {
      const p = policyRes.data
      const isGlobal = Boolean(p.is_global || p.is_public)
      policyForm.unit_id = unitId
      policyForm.is_global = isGlobal
      policyForm.is_public = isGlobal
      policyForm.department_ids = [...(p.department_ids || [])]
      policyForm.role_ids = [...(p.role_ids || [])]
      policyForm.user_ids = [...(p.user_ids || [])]
    }
  } catch (err) {
    console.error('加载4D策略失败:', err)
  } finally {
    loading.value = false
  }
}

watch(
  () => [props.visible, props.unit],
  ([isVisible, unitVal]) => {
    if (isVisible && unitVal) {
      userSearchQuery.value = ''
      showUserDropdown.value = false
      loadAllData((unitVal as KnowledgeUnit).id)
    }
  },
  { immediate: true }
)

// 交互操作逻辑
const onGlobalToggle = () => {
  policyForm.is_public = policyForm.is_global
}

const toggleDept = (dept: FlattenedDept) => {
  const isSelected = policyForm.department_ids.includes(dept.id)
  const targetIds = cascadeSubDepts.value ? dept.childIds : [dept.id]

  if (isSelected) {
    policyForm.department_ids = policyForm.department_ids.filter((id) => !targetIds.includes(id))
  } else {
    const newSet = new Set([...policyForm.department_ids, ...targetIds])
    policyForm.department_ids = Array.from(newSet)
  }
}

const onAddRoleSelect = (event: Event) => {
  const target = event.target as HTMLSelectElement
  const roleId = Number(target.value)
  if (roleId && !policyForm.role_ids.includes(roleId)) {
    policyForm.role_ids.push(roleId)
  }
  target.value = ''
}

const removeRole = (roleId: number) => {
  policyForm.role_ids = policyForm.role_ids.filter((id) => id !== roleId)
}

const addUser = (userId: number) => {
  if (!policyForm.user_ids.includes(userId)) {
    policyForm.user_ids.push(userId)
  }
  userSearchQuery.value = ''
  showUserDropdown.value = false
}

const removeUser = (userId: number) => {
  policyForm.user_ids = policyForm.user_ids.filter((id) => id !== userId)
}

const resetToPrivateDefault = () => {
  policyForm.is_global = false
  policyForm.is_public = false
  policyForm.department_ids = []
  policyForm.role_ids = []
  policyForm.user_ids = []
}

// 保存并同步策略 (PUT /api/v1/guard/units/{id}/policy)
const savePolicy = async () => {
  if (!props.unit) return
  saving.value = true
  try {
    const payload: PermissionPolicyConfig = {
      unit_id: props.unit.id,
      is_global: policyForm.is_global,
      is_public: policyForm.is_global,
      department_ids: policyForm.is_global ? [] : policyForm.department_ids,
      role_ids: policyForm.is_global ? [] : policyForm.role_ids,
      user_ids: policyForm.is_global ? [] : policyForm.user_ids
    }

    const res = await updateUnitPolicyApi(props.unit.id, payload)
    if (res.code === 200 || res.data) {
      emit('saved', payload)
      emit('close')
    } else {
      throw new Error(res.message || '保存策略失败')
    }
  } catch (err) {
    alert(err instanceof Error ? err.message : '更新4D权限策略失败')
  } finally {
    saving.value = false
  }
}

// 快捷键支持 (⌘S 保存, ESC 关闭)
const handleKeydown = (e: KeyboardEvent) => {
  if (!props.visible) return
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 's') {
    e.preventDefault()
    savePolicy()
  } else if (e.key === 'Escape') {
    emit('close')
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>
