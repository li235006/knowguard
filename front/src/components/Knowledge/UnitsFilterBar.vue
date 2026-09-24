<template>
  <!-- FE-M4: 知识资产多维筛选栏 (PAGE-03 原型精确对齐) -->
  <div class="w-full bg-white rounded-xl border border-[#E5E7EB] p-3 shadow-sm flex flex-wrap items-center justify-between gap-3">
    <!-- Left Filter Controls -->
    <div class="flex flex-wrap items-center gap-2.5 flex-1 min-w-[280px]">
      <!-- Search Input -->
      <div class="relative w-64">
        <Search :size="14" class="absolute left-3 top-2.5 text-[#94A3B8]" />
        <input
          :value="search"
          type="text"
          placeholder="搜索文档名称、Unit ID 或权限..."
          class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg pl-9 pr-7 py-1.5 text-xs text-[#0F172A] placeholder-[#94A3B8] focus:outline-none focus:border-[#0071E3] focus:bg-white transition-colors"
          @input="onSearchInput"
          @keyup.enter="onSearchEnter"
        />
        <button
          v-if="search"
          type="button"
          class="absolute right-2 top-2.5 text-[#94A3B8] hover:text-[#475569]"
          @click="onClearSearch"
        >
          <X :size="13" />
        </button>
      </div>

      <!-- Format Filter Dropdown -->
      <div class="relative">
        <select
          :value="format"
          class="appearance-none bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg pl-3 pr-8 py-1.5 text-xs text-[#334155] focus:outline-none focus:border-[#0071E3] cursor-pointer hover:bg-white transition-colors font-medium"
          @change="onFormatChange"
        >
          <option value="ALL">格式: 全部</option>
          <option value="PDF">PDF 文档</option>
          <option value="MD">Markdown (.md)</option>
          <option value="DOCX">Word (.docx)</option>
          <option value="TXT">纯文本 (.txt)</option>
        </select>
        <ChevronDown :size="13" class="absolute right-2.5 top-2.5 text-[#94A3B8] pointer-events-none" />
      </div>

      <!-- Category Filter Dropdown -->
      <div class="relative">
        <select
          :value="category"
          class="appearance-none bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg pl-3 pr-8 py-1.5 text-xs text-[#334155] focus:outline-none focus:border-[#0071E3] cursor-pointer hover:bg-white transition-colors font-medium"
          @change="onCategoryChange"
        >
          <option value="ALL">分类: 全部分类</option>
          <option value="TECH">研发与技术 (TECH)</option>
          <option value="FINANCE">财务行政 (FINANCE)</option>
          <option value="HR">人力资源 (HR)</option>
          <option value="SECURITY">安全合规 (SECURITY)</option>
          <option value="LEGAL">法务审查 (LEGAL)</option>
        </select>
        <ChevronDown :size="13" class="absolute right-2.5 top-2.5 text-[#94A3B8] pointer-events-none" />
      </div>

      <!-- Status Filter Dropdown -->
      <div class="relative">
        <select
          :value="status"
          class="appearance-none bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg pl-3 pr-8 py-1.5 text-xs text-[#334155] focus:outline-none focus:border-[#0071E3] cursor-pointer hover:bg-white transition-colors font-medium"
          @change="onStatusChange"
        >
          <option value="ALL">状态: 全部状态</option>
          <option value="INDEXED">已就绪 (INDEXED)</option>
          <option value="PARSING">解析中 (PARSING)</option>
          <option value="DISABLED">已停用 (DISABLED)</option>
          <option value="FAILED">解析失败 (FAILED)</option>
        </select>
        <ChevronDown :size="13" class="absolute right-2.5 top-2.5 text-[#94A3B8] pointer-events-none" />
      </div>

      <!-- Reset Filters Button -->
      <button
        v-if="hasActiveFilter"
        type="button"
        class="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs text-[#64748B] hover:text-[#0F172A] hover:bg-gray-100 transition-colors"
        title="重置全部筛选条件"
        @click="onReset"
      >
        <RotateCcw :size="12" />
        <span>重置筛选</span>
      </button>
    </div>

    <!-- Right Action Buttons -->
    <div class="flex items-center gap-2">
      <!-- Refresh Button -->
      <button
        type="button"
        class="inline-flex items-center justify-center w-8 h-8 rounded-lg border border-[#E5E7EB] bg-white text-[#64748B] hover:text-[#0F172A] hover:bg-[#F8FAFC] transition-colors"
        :class="{ 'opacity-60 cursor-not-allowed': loading }"
        :disabled="loading"
        title="刷新列表"
        @click="emit('refresh')"
      >
        <RefreshCw :size="13" :class="{ 'animate-spin': loading }" />
      </button>

      <!-- Upload Document Trigger Button -->
      <button
        type="button"
        class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-[#0071E3] hover:bg-[#0077ED] active:scale-[0.98] text-white text-xs font-medium shadow-sm transition-all"
        @click="emit('open-upload')"
      >
        <Plus :size="14" />
        <span>导入新文档</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 知识资产多维筛选栏组件
 * 模块: FE-M4 (PAGE-03 原型对齐)
 */

import { computed } from 'vue'
import {
  Search,
  X,
  ChevronDown,
  RotateCcw,
  RefreshCw,
  Plus
} from 'lucide-vue-next'

const props = withDefaults(
  defineProps<{
    search?: string
    format?: string
    category?: string
    status?: string
    loading?: boolean
  }>(),
  {
    search: '',
    format: 'ALL',
    category: 'ALL',
    status: 'ALL',
    loading: false
  }
)

const emit = defineEmits<{
  (e: 'update:search', val: string): void
  (e: 'update:format', val: string): void
  (e: 'update:category', val: string): void
  (e: 'update:status', val: string): void
  (e: 'search', val: string): void
  (e: 'reset'): void
  (e: 'refresh'): void
  (e: 'open-upload'): void
}>()

const hasActiveFilter = computed(() => {
  return (
    (props.search && props.search.trim().length > 0) ||
    props.format !== 'ALL' ||
    props.category !== 'ALL' ||
    props.status !== 'ALL'
  )
})

const onSearchInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  emit('update:search', target.value)
  emit('search', target.value)
}

const onSearchEnter = () => {
  emit('search', props.search)
}

const onClearSearch = () => {
  emit('update:search', '')
  emit('search', '')
}

const onFormatChange = (event: Event) => {
  const target = event.target as HTMLSelectElement
  emit('update:format', target.value)
}

const onCategoryChange = (event: Event) => {
  const target = event.target as HTMLSelectElement
  emit('update:category', target.value)
}

const onStatusChange = (event: Event) => {
  const target = event.target as HTMLSelectElement
  emit('update:status', target.value)
}

const onReset = () => {
  emit('reset')
}
</script>
