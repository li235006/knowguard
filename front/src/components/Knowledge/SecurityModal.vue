<template>
  <!-- FE-M4: 四维一体化 4D-RBAC 权限配置弹窗 (PAGE-04 原型对齐) -->
  <div
    v-if="visible"
    class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-200"
  >
    <div class="bg-white rounded-2xl p-6 max-w-lg w-full shadow-2xl border border-gray-100 flex flex-col gap-4 text-xs">
      <!-- Header -->
      <div class="flex items-center justify-between border-b border-[#F1F5F9] pb-3">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center border border-indigo-100">
            <Shield :size="16" />
          </div>
          <div>
            <h3 class="text-sm font-semibold text-[#0F172A]">4D-RBAC 知识权限策略配置</h3>
            <p class="text-[11px] text-[#64748B] font-mono mt-0.5">
              Unit ID: KU-{{ unit?.id }} · {{ unit?.title }}
            </p>
          </div>
        </div>
        <button
          type="button"
          class="text-[#94A3B8] hover:text-[#0F172A] p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
          @click="emit('close')"
        >
          <X :size="16" />
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="py-8 flex flex-col items-center justify-center gap-2 text-[#64748B]">
        <Loader2 :size="20" class="animate-spin text-[#0071E3]" />
        <span>正在加载访问控制策略...</span>
      </div>

      <!-- Policy Form -->
      <div v-else class="space-y-4">
        <!-- Global Policy Radio -->
        <div class="bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl p-3.5 space-y-2.5">
          <div class="font-medium text-[#0F172A]">访问控制模式</div>
          <div class="grid grid-cols-2 gap-3">
            <label
              class="flex items-center gap-2 p-2.5 rounded-lg border cursor-pointer transition-colors"
              :class="policyForm.is_global ? 'bg-blue-50/50 border-[#0071E3] text-[#0071E3]' : 'bg-white border-[#E2E8F0] text-[#475569] hover:bg-gray-50'"
            >
              <input
                type="radio"
                name="is_global"
                :value="true"
                v-model="policyForm.is_global"
                class="sr-only"
              />
              <Globe :size="14" />
              <div class="flex flex-col">
                <span class="font-semibold text-xs">全员公开访问</span>
                <span class="text-[10px] opacity-75">全企业所有在册员工可检索</span>
              </div>
            </label>

            <label
              class="flex items-center gap-2 p-2.5 rounded-lg border cursor-pointer transition-colors"
              :class="!policyForm.is_global ? 'bg-indigo-50/50 border-indigo-500 text-indigo-700' : 'bg-white border-[#E2E8F0] text-[#475569] hover:bg-gray-50'"
            >
              <input
                type="radio"
                name="is_global"
                :value="false"
                v-model="policyForm.is_global"
                class="sr-only"
              />
              <Lock :size="14" />
              <div class="flex flex-col">
                <span class="font-semibold text-xs">4D 定向授权</span>
                <span class="text-[10px] opacity-75">限制指定部门与角色</span>
              </div>
            </label>
          </div>
        </div>

        <!-- Conditional RBAC Controls -->
        <div v-if="!policyForm.is_global" class="space-y-3 p-3 bg-indigo-50/20 border border-indigo-100 rounded-xl">
          <!-- Department Scope -->
          <div class="space-y-1.5">
            <label class="font-medium text-[#475569]">授权可访问部门</label>
            <div class="flex flex-wrap gap-2">
              <label
                v-for="dept in availableDepts"
                :key="dept.id"
                class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs cursor-pointer select-none transition-colors"
                :class="policyForm.department_ids.includes(dept.id) ? 'bg-[#0071E3] text-white border-[#0071E3]' : 'bg-white text-[#475569] border-[#E2E8F0] hover:bg-gray-50'"
              >
                <input
                  type="checkbox"
                  :value="dept.id"
                  v-model="policyForm.department_ids"
                  class="sr-only"
                />
                <span>{{ dept.name }}</span>
              </label>
            </div>
          </div>

          <!-- Role Scope -->
          <div class="space-y-1.5">
            <label class="font-medium text-[#475569]">授权可访问系统角色</label>
            <div class="flex flex-wrap gap-2">
              <label
                v-for="role in availableRoles"
                :key="role.id"
                class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs cursor-pointer select-none transition-colors"
                :class="policyForm.role_ids.includes(role.id) ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-white text-[#475569] border-[#E2E8F0] hover:bg-gray-50'"
              >
                <input
                  type="checkbox"
                  :value="role.id"
                  v-model="policyForm.role_ids"
                  class="sr-only"
                />
                <span>{{ role.name }}</span>
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- Modal Footer -->
      <div class="flex items-center justify-end gap-2.5 pt-3 border-t border-[#F1F5F9]">
        <button
          type="button"
          :disabled="saving"
          class="px-3.5 py-1.5 rounded-lg text-[#64748B] hover:bg-gray-100 font-medium transition-colors"
          @click="emit('close')"
        >
          取消
        </button>
        <button
          type="button"
          :disabled="saving || loading"
          class="px-4 py-1.5 rounded-lg bg-[#0071E3] hover:bg-[#0077ED] text-white font-medium shadow-sm inline-flex items-center gap-1.5 transition-colors disabled:opacity-50"
          @click="savePolicy"
        >
          <Loader2 v-if="saving" :size="13" class="animate-spin" />
          <span>{{ saving ? '正在保存...' : '保存策略并同步' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 四维权限一体化配置弹窗组件
 * 模块: FE-M4 / M3: Guard (PAGE-04 原型对齐)
 */

import { ref, reactive, watch } from 'vue'
import { Shield, X, Globe, Lock, Loader2 } from 'lucide-vue-next'
import type { KnowledgeUnit, PermissionPolicyConfig } from '@/types/knowledge'
import { getUnitPolicyApi, updateUnitPolicyApi } from '@/api/knowledge'

const props = defineProps<{
  unit: KnowledgeUnit | null
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'saved'): void
}>()

const loading = ref<boolean>(false)
const saving = ref<boolean>(false)

const policyForm = reactive<PermissionPolicyConfig>({
  unit_id: 0,
  is_global: true,
  department_ids: [],
  role_ids: [],
  user_ids: []
})

const availableDepts = [
  { id: 2, name: '集团财务部' },
  { id: 3, name: '研发与技术中心' },
  { id: 4, name: '人力资源与组织部' },
  { id: 5, name: '安全合规与法务审计部' }
]

const availableRoles = [
  { id: 1, name: '超级管理员' },
  { id: 2, name: '安全审计员' },
  { id: 3, name: '知识专员' },
  { id: 4, name: '部门主管' },
  { id: 5, name: '普通员工' }
]

watch(
  () => [props.visible, props.unit],
  async ([isVisible, unitVal]) => {
    if (isVisible && unitVal) {
      const u = unitVal as KnowledgeUnit
      policyForm.unit_id = u.id
      loading.value = true
      try {
        const res = await getUnitPolicyApi(u.id)
        if (res.data) {
          policyForm.is_global = res.data.is_global
          policyForm.department_ids = [...res.data.department_ids]
          policyForm.role_ids = [...res.data.role_ids]
          policyForm.user_ids = [...res.data.user_ids]
        }
      } catch (err) {
        console.error('加载策略失败:', err)
      } finally {
        loading.value = false
      }
    }
  }
)

const savePolicy = async () => {
  if (!props.unit) return
  saving.value = true
  try {
    await updateUnitPolicyApi(props.unit.id, policyForm)
    emit('saved')
    emit('close')
  } catch (err) {
    alert(err instanceof Error ? err.message : '更新策略失败')
  } finally {
    saving.value = false
  }
}
</script>
