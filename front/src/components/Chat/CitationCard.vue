<template>
  <!-- FE-M2: 知识溯源卡片组件 (PAGE-02 原型对齐) -->
  <div
    class="w-full bg-[#F8FAFC] hover:bg-[#F1F5F9] rounded-lg border border-[#E5E7EB] p-2.5 transition-all text-xs flex flex-col gap-1.5 select-none"
  >
    <div class="flex items-center justify-between gap-2">
      <!-- Left: Icon & Document Title -->
      <div class="flex items-center gap-2 overflow-hidden flex-1">
        <FileText :size="14" class="text-[#0071E3] shrink-0" />
        <span class="font-medium text-[#334155] truncate" :title="citation.unit_title">
          {{ citation.unit_title }}
        </span>
      </div>

      <!-- Right: Confidence Tag & External Link -->
      <div class="flex items-center gap-2 shrink-0">
        <span
          class="px-2 py-0.5 rounded text-[10px] font-medium bg-[#F0FDF4] text-[#16A34A] border border-[#BBF7D0]"
        >
          企业官方标准 · 置信度 {{ Math.round(citation.score * 100) }}%
        </span>
        <button
          type="button"
          class="p-0.5 text-[#94A3B8] hover:text-[#0071E3] transition-colors"
          title="查看原知识文档"
          @click="showSnippet = !showSnippet"
        >
          <ExternalLink :size="12" />
        </button>
      </div>
    </div>

    <!-- Snippet Quotation Preview -->
    <div
      v-if="citation.snippet"
      class="text-[11px] text-[#64748B] bg-white/70 rounded p-2 border border-[#F1F5F9] leading-relaxed cursor-pointer"
      @click="showSnippet = !showSnippet"
    >
      <span class="text-[#94A3B8] mr-1">“</span>
      <span>{{ showSnippet ? citation.snippet : truncatedSnippet }}</span>
      <span class="text-[#94A3B8] ml-1">”</span>
      <span v-if="citation.snippet.length > 80" class="text-[#0071E3] ml-1 text-[10px] hover:underline">
        {{ showSnippet ? '收起' : '展开引文' }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 知识溯源卡片组件
 * 模块: FE-M2 (PAGE-02)
 */

import { ref, computed } from 'vue'
import { FileText, ExternalLink } from 'lucide-vue-next'
import type { CitationItem } from '@/types/chat'

const props = defineProps<{
  citation: CitationItem
}>()

const showSnippet = ref(false)

const truncatedSnippet = computed(() => {
  if (!props.citation.snippet) return ''
  return props.citation.snippet.length > 80
    ? props.citation.snippet.slice(0, 80) + '...'
    : props.citation.snippet
})
</script>
