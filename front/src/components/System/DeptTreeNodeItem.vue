<template>
  <div class="flex flex-col select-none">
    <div
      class="flex items-center justify-between px-2 py-1.5 rounded-lg text-xs cursor-pointer transition-colors group"
      :class="[
        isSelected
          ? 'bg-[#EFF6FF] text-[#0071E3] font-semibold'
          : 'text-[#475569] hover:bg-[#F8FAFC]'
      ]"
      :style="{ paddingLeft: `${node.level * 12 + 6}px` }"
      @click="emit('select', node.id)"
    >
      <div class="flex items-center gap-1.5 overflow-hidden">
        <button
          v-if="hasChildren"
          type="button"
          class="w-4 h-4 flex items-center justify-center text-gray-400 hover:text-gray-600 rounded"
          @click.stop="isExpanded = !isExpanded"
        >
          <ChevronRight
            :size="12"
            class="transition-transform duration-200"
            :class="{ 'rotate-90': isExpanded }"
          />
        </button>
        <span v-else class="w-4" />

        <Folder :size="13" :class="isSelected ? 'text-[#0071E3]' : 'text-[#94A3B8]'" />
        <span class="truncate">{{ node.name }}</span>
      </div>

      <div class="flex items-center gap-1">
        <button
          type="button"
          class="opacity-0 group-hover:opacity-100 text-[10px] text-gray-400 hover:text-[#0071E3] px-1 rounded transition-opacity"
          title="添加子部门"
          @click.stop="emit('addChild', node.id)"
          v-permission="'system:dept:manage'"
        >
          +
        </button>
        <span v-if="node.member_count !== undefined" class="text-[10px] text-[#94A3B8]">
          {{ node.member_count }}
        </span>
      </div>
    </div>

    <!-- Recursive children -->
    <div v-if="hasChildren && isExpanded" class="flex flex-col">
      <DeptTreeNodeItem
        v-for="child in node.children"
        :key="child.id"
        :node="child"
        :selected-id="selectedId"
        :search-query="searchQuery"
        @select="(id) => emit('select', id)"
        @add-child="(id) => emit('addChild', id)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ChevronRight, Folder } from 'lucide-vue-next'
import type { DepartmentNode } from '@/types/system'

const props = defineProps<{
  node: DepartmentNode
  selectedId: number | null
  searchQuery?: string
}>()

const emit = defineEmits<{
  (e: 'select', id: number): void
  (e: 'addChild', parentId: number): void
}>()

const isExpanded = ref(true)

const hasChildren = computed(() => !!props.node.children && props.node.children.length > 0)
const isSelected = computed(() => props.selectedId === props.node.id)
</script>

