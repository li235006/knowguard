<template>
  <!-- FE-M2: 打字机 Markdown 渲染组件 -->
  <div class="markdown-body text-xs text-[#0F172A] leading-relaxed whitespace-pre-wrap select-text">
    <div v-html="formattedHtml"></div>
    <span
      v-if="isStreaming"
      class="inline-block w-1.5 h-3.5 ml-0.5 bg-[#0071E3] animate-pulse align-middle"
    ></span>
  </div>
</template>

<script setup lang="ts">
/**
 * Markdown 打字机流式渲染组件
 * 模块: FE-M2 (PAGE-02)
 */

import { computed } from 'vue'

const props = defineProps<{
  content: string
  isStreaming?: boolean
}>()

const escapeHtml = (str: string): string => {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

const formattedHtml = computed(() => {
  if (!props.content) return ''

  let text = escapeHtml(props.content)

  // 1. 加粗 **text**
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-[#0F172A]">$1</strong>')

  // 2. 行内代码 `code`
  text = text.replace(/`([^`]+)`/g, '<code class="px-1 py-0.5 bg-gray-100 text-blue-600 rounded text-[11px] font-mono">$1</code>')

  // 3. 无序列表项 - item 或 • item
  text = text.replace(/^[\s]*[-•]\s+(.+)$/gm, '<div class="flex items-start gap-1.5 my-0.5"><span class="text-[#0071E3] mt-0.5">•</span><span>$1</span></div>')

  // 4. 数字序号 1. item
  text = text.replace(/^[\s]*(\d+)\.\s+(.+)$/gm, '<div class="flex items-start gap-1.5 my-1 font-medium"><span class="text-[#0071E3]">$1.</span><span>$2</span></div>')

  return text
})
</script>
