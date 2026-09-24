<template>
  <!-- FE-M3: 部门 8 级递归树形组件 (PAGE-05-A) -->
  <div class="w-72 bg-white rounded-xl border border-[#E5E7EB] shadow-sm flex flex-col h-full shrink-0 overflow-hidden">
    <!-- Tree Header -->
    <div class="p-3 border-b border-[#F1F5F9] flex flex-col gap-2.5">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-1.5 font-semibold text-xs text-[#0F172A]">
          <Building2 :size="15" class="text-[#0071E3]" />
          <span>组织架构树</span>
        </div>
        <div class="flex items-center gap-1">
          <button
            type="button"
            class="text-[11px] px-2 py-0.5 rounded text-[#0071E3] hover:bg-[#EFF6FF] font-medium transition-colors"
            @click="openAddRootModal"
            v-permission="'system:dept:manage'"
          >
            + 根部门
          </button>
        </div>
      </div>

      <!-- Search Input -->
      <div class="relative">
        <Search :size="13" class="absolute left-2.5 top-2.5 text-[#94A3B8]" />
        <input
          v-model="searchKeyword"
          type="text"
          placeholder="搜索部门名称..."
          class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg pl-8 pr-3 py-1.5 text-xs text-[#0F172A] placeholder-[#94A3B8] focus:outline-none focus:border-[#0071E3]"
        />
      </div>
    </div>

    <!-- Tree Node List -->
    <div class="flex-1 overflow-y-auto p-2 flex flex-col gap-0.5">
      <!-- "All Members" Node -->
      <div
        class="flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs cursor-pointer transition-colors"
        :class="
          selectedDeptId === null
            ? 'bg-[#EFF6FF] text-[#0071E3] font-semibold'
            : 'text-[#475569] hover:bg-[#F8FAFC]'
        "
        @click="handleSelect(null)"
      >
        <div class="flex items-center gap-2">
          <Layers :size="14" :class="selectedDeptId === null ? 'text-[#0071E3]' : 'text-[#64748B]'" />
          <span>全员组织 (全部员工)</span>
        </div>
        <span class="text-[10px] text-[#94A3B8] bg-[#F1F5F9] px-1.5 py-0.5 rounded-full">
          {{ totalCount }}
        </span>
      </div>

      <!-- Recursive Tree Nodes -->
      <div v-for="node in filteredNodes" :key="node.id">
        <DeptTreeNodeItem
          :node="node"
          :selected-id="selectedDeptId"
          :search-query="searchKeyword"
          @select="handleSelect"
          @add-child="openAddChildModal"
        />
      </div>
    </div>

    <!-- Add Department Dialog Modal -->
    <div
      v-if="showModal"
      class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4"
    >
      <div class="bg-white rounded-xl max-w-sm w-full p-5 shadow-xl border border-gray-100 flex flex-col gap-4">
        <div class="flex items-center justify-between border-b pb-3">
          <h3 class="font-semibold text-sm text-[#0F172A]">
            {{ modalParentId ? '新增下级部门' : '新增一级根部门' }}
          </h3>
          <button type="button" class="text-gray-400 hover:text-gray-600" @click="showModal = false">
            <X :size="16" />
          </button>
        </div>

        <div class="flex flex-col gap-2">
          <label class="text-xs font-medium text-[#475569]">部门名称</label>
          <input
            v-model="deptNameInput"
            type="text"
            placeholder="例如: 智能算法与工程部"
            class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-3 py-2 text-xs text-[#0F172A] focus:outline-none focus:border-[#0071E3]"
            @keyup.enter="submitAddDept"
          />
        </div>

        <div class="flex items-center justify-end gap-2 pt-2">
          <button
            type="button"
            class="px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            @click="showModal = false"
          >
            取消
          </button>
          <button
            type="button"
            class="px-3 py-1.5 text-xs bg-[#0071E3] hover:bg-[#0077ED] text-white rounded-lg font-medium transition-colors disabled:opacity-50"
            :disabled="!deptNameInput.trim()"
            @click="submitAddDept"
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
 * 部门树组件 (支持 8 级递归展开)
 * 模块: FE-M3 (PAGE-05-A)
 */

import { ref, computed } from 'vue'
import { Building2, Search, Layers, X } from 'lucide-vue-next'
import type { DepartmentNode } from '@/types/system'
import { createDepartmentApi } from '@/api/system'
import DeptTreeNodeItem from './DeptTreeNodeItem.vue'

const props = defineProps<{
  nodes: DepartmentNode[]
  selectedDeptId: number | null
}>()

const emit = defineEmits<{
  (e: 'select', deptId: number | null): void
  (e: 'refresh'): void
}>()

const searchKeyword = ref('')
const showModal = ref(false)
const modalParentId = ref<number | null>(null)
const deptNameInput = ref('')

const totalCount = computed(() => {
  return props.nodes.reduce((acc, curr) => acc + (curr.member_count || 0), 0)
})

const filteredNodes = computed<DepartmentNode[]>(() => {
  if (!searchKeyword.value.trim()) return props.nodes
  const kw = searchKeyword.value.trim().toLowerCase()

  const filterTree = (list: DepartmentNode[]): DepartmentNode[] => {
    const result: DepartmentNode[] = []
    for (const node of list) {
      const matchesSelf = node.name.toLowerCase().includes(kw)
      const filteredChildren = node.children ? filterTree(node.children) : []
      if (matchesSelf || filteredChildren.length > 0) {
        result.push({
          ...node,
          children: filteredChildren
        })
      }
    }
    return result
  }

  return filterTree(props.nodes)
})

const handleSelect = (deptId: number | null) => {
  emit('select', deptId)
}

const openAddRootModal = () => {
  modalParentId.value = null
  deptNameInput.value = ''
  showModal.value = true
}

const openAddChildModal = (parentId: number) => {
  modalParentId.value = parentId
  deptNameInput.value = ''
  showModal.value = true
}

const submitAddDept = async () => {
  if (!deptNameInput.value.trim()) return
  try {
    await createDepartmentApi({
      name: deptNameInput.value.trim(),
      parent_id: modalParentId.value
    })
    showModal.value = false
    emit('refresh')
  } catch (err) {
    alert(err instanceof Error ? err.message : '创建部门失败')
  }
}
</script>

