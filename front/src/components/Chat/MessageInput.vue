<template>
  <!-- FE-M2: 输入框与快捷发送组件 (PAGE-02 原型对齐) -->
  <div class="w-full max-w-3xl mx-auto px-4 pb-6 flex flex-col gap-2.5 select-none">
    <!-- Smart Suggestions Row (猜你想问) -->
    <div
      v-if="suggestions && suggestions.length > 0"
      class="flex items-center gap-2 overflow-x-auto py-1 scrollbar-none text-xs"
    >
      <div class="flex items-center gap-1 text-[#0071E3] font-semibold shrink-0">
        <Sparkles :size="13" />
        <span>猜你想问：</span>
      </div>

      <button
        v-for="sug in suggestions"
        :key="sug"
        type="button"
        class="shrink-0 px-3 py-1 rounded-full bg-white border border-[#E5E7EB] hover:border-[#0071E3] hover:text-[#0071E3] text-[#475569] transition-all shadow-xs"
        @click="handleSelectSuggestion(sug)"
      >
        {{ sug }}
      </button>
    </div>

    <!-- Input Box Card -->
    <div
      class="bg-white rounded-2xl border border-[#E5E7EB] shadow-[0_4px_20px_rgba(15,23,42,0.04)] focus-within:border-[#0071E3] focus-within:ring-2 focus-within:ring-[#0071E3]/20 transition-all p-3 flex flex-col gap-2"
    >
      <textarea
        ref="textareaRef"
        v-model="inputQuery"
        rows="2"
        placeholder="向 KnowGuard 提问任何企业知识、规章政策或业务流程... (Shift + Enter 换行，Enter 发送)"
        class="w-full bg-transparent text-xs text-[#0F172A] placeholder-[#94A3B8] focus:outline-none resize-none leading-relaxed"
        @keydown="handleKeyDown"
      ></textarea>

      <!-- Input Toolbar -->
      <div class="flex items-center justify-end pt-1 border-t border-[#F8FAFC]">
        <div class="flex items-center gap-2">
          <!-- Stop Button -->
          <button
            v-if="isGenerating"
            type="button"
            class="px-2.5 py-1.5 rounded-lg bg-red-50 hover:bg-red-100 text-red-600 text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer"
            @click="emit('stop')"
          >
            <Square :size="12" class="fill-current" />
            <span>停止生成</span>
          </button>

          <!-- Send Button -->
          <button
            v-else
            type="button"
            :disabled="!inputQuery.trim()"
            class="w-8 h-8 rounded-lg bg-[#0071E3] hover:bg-[#0077ED] disabled:opacity-40 text-white flex items-center justify-center transition-all shadow-sm cursor-pointer"
            @click="handleSubmit"
          >
            <ArrowUp :size="16" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 提问输入框与联想建议组件
 * 模块: FE-M2 (PAGE-02)
 */

import { ref } from 'vue'
import { Sparkles, ArrowUp, Square } from 'lucide-vue-next'

const props = defineProps<{
  suggestions: string[]
  isGenerating: boolean
}>()

const emit = defineEmits<{
  (e: 'send', query: string): void
  (e: 'stop'): void
}>()

const inputQuery = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)

const handleSubmit = () => {
  if (!inputQuery.value.trim() || props.isGenerating) return
  emit('send', inputQuery.value.trim())
  inputQuery.value = ''
}

const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSubmit()
  }
}

const handleSelectSuggestion = (sug: string) => {
  emit('send', sug)
}
</script>
