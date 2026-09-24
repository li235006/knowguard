<template>
  <!-- FE-M5: 知识缺口一键转建工单抽屉/弹窗 (PAGE-06 原型 1:1 对齐) -->
  <div v-if="evolutionStore.showGapModal" class="fixed inset-0 z-50 overflow-hidden">
    <!-- Backdrop -->
    <div
      class="absolute inset-0 bg-black/40 backdrop-blur-sm transition-opacity"
      @click="closeModal"
    />

    <div class="fixed inset-y-0 right-0 max-w-full flex pl-10">
      <div class="w-screen max-w-xl bg-white shadow-2xl flex flex-col justify-between border-l border-[#E5E7EB] animate-in slide-in-from-right duration-300">
        <!-- Header -->
        <div class="p-4 border-b border-[#F1F5F9] flex items-center justify-between shrink-0 bg-[#F8FAFC]">
          <div class="flex items-center gap-2">
            <h3 class="font-semibold text-sm text-[#0F172A]">转建知识补全工单</h3>
            <span class="text-[11px] px-2 py-0.5 rounded bg-blue-50 text-[#0071E3] font-mono">
              {{ currentGap?.gap_code || 'GAP-2024-001' }}
            </span>
          </div>
          <button
            type="button"
            class="text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-100 transition-colors"
            @click="closeModal"
          >
            <X :size="16" />
          </button>
        </div>

        <!-- Body -->
        <div class="flex-1 overflow-y-auto p-5 space-y-4 text-xs">
          <!-- Summary Header Box -->
          <div class="bg-[#F8FAFC] border border-[#E5E7EB] rounded-xl p-3.5 space-y-1.5">
            <div class="font-semibold text-xs text-[#0F172A]">
              未命中提问词：{{ currentGap?.query_text }}
            </div>
            <div class="text-[11px] text-[#64748B] flex flex-wrap items-center gap-3">
              <span>频次: <strong class="text-[#0F172A]">{{ currentGap?.hit_count }}次</strong></span>
              <span>影响部门: <strong class="text-[#0F172A]">{{ currentGap?.department_name || '相关业务部门' }}</strong></span>
              <span>严重级: <strong class="text-rose-600">{{ currentGap?.severity || 'P1' }}</strong></span>
            </div>
          </div>

          <!-- Form Fields -->
          <div class="space-y-3.5">
            <!-- Ticket Title -->
            <div class="flex flex-col gap-1">
              <label class="font-medium text-[#475569]">工单标题 *</label>
              <input
                v-model="ticketForm.title"
                type="text"
                placeholder="例如: 【知识缺口补全】东南亚关税税率与清关应急方案"
                class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-3 py-2 text-xs text-[#0F172A] focus:outline-none focus:border-[#0071E3] font-medium"
              />
            </div>

            <!-- Domain -->
            <div class="flex flex-col gap-1">
              <label class="font-medium text-[#475569]">涉及业务域</label>
              <input
                v-model="ticketForm.domain"
                type="text"
                placeholder="跨境电商与供应链 (已自动识别)"
                class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-3 py-2 text-xs text-[#0F172A] focus:outline-none focus:border-[#0071E3]"
              />
            </div>

            <!-- Assignee -->
            <div class="flex flex-col gap-1">
              <label class="font-medium text-[#475569]">指定责任人 *</label>
              <div class="relative">
                <input
                  v-model="ticketForm.assignee"
                  type="text"
                  placeholder="陈明 · 跨境物流专员 (工号 10034 · 跨境电商部)"
                  class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg pl-8 pr-3 py-2 text-xs text-[#0F172A] focus:outline-none focus:border-[#0071E3]"
                />
                <User :size="13" class="absolute left-2.5 top-2.5 text-[#94A3B8]" />
              </div>
            </div>

            <!-- Deadline -->
            <div class="flex flex-col gap-1">
              <label class="font-medium text-[#475569]">截止交付时间</label>
              <div class="relative">
                <input
                  v-model="ticketForm.deadline"
                  type="text"
                  placeholder="2026-09-30 (7日内完成编制)"
                  class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg pl-8 pr-3 py-2 text-xs text-[#0F172A] focus:outline-none focus:border-[#0071E3]"
                />
                <Calendar :size="13" class="absolute left-2.5 top-2.5 text-[#94A3B8]" />
              </div>
            </div>

            <!-- Notes -->
            <div class="flex flex-col gap-1">
              <label class="font-medium text-[#475569]">补全说明与资料要求</label>
              <textarea
                v-model="ticketForm.notes"
                rows="4"
                placeholder="请补充海关最新 HS Code 对应征税比例及港口滞港费核算准则，并以 Markdown/Word 格式上传至《跨境业务库》。"
                class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-3 py-2 text-xs text-[#0F172A] leading-relaxed focus:outline-none focus:border-[#0071E3]"
              ></textarea>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="p-4 border-t border-[#F1F5F9] bg-[#F8FAFC] flex items-center justify-between shrink-0">
          <button
            type="button"
            class="px-4 py-2 text-xs text-gray-600 hover:bg-gray-100 rounded-lg transition-colors font-medium"
            @click="closeModal"
          >
            取消
          </button>
          <div class="flex items-center gap-2">
            <button
              v-if="currentGap?.status === 'CONVERTED'"
              type="button"
              :disabled="isSubmitting"
              class="px-3.5 py-2 text-xs bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 inline-flex items-center gap-1.5 shadow-sm"
              @click="markResolved"
            >
              <Check :size="13" />
              <span>标记闭环完成</span>
            </button>
            <button
              type="button"
              :disabled="!ticketForm.title.trim() || !ticketForm.assignee.trim() || isSubmitting"
              class="px-5 py-2 text-xs bg-[#0071E3] hover:bg-[#0077ED] text-white rounded-lg font-medium transition-colors disabled:opacity-50 inline-flex items-center gap-1.5 shadow-sm"
              @click="submitTicket"
            >
              <Send :size="13" />
              <span>{{ isSubmitting ? '下发中...' : (currentGap?.status === 'CONVERTED' ? '更新并重新下发' : `立即下发工单 (通知${ticketForm.assignee.split('·')[0].trim() || '责任人'})`) }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 知识缺口转建工单弹窗/抽屉组件
 * 模块: FE-M5 (PAGE-06 原型 1:1)
 */

import { ref, reactive, computed, watch } from 'vue'
import { X, User, Calendar, Send, Check } from 'lucide-vue-next'
import { useEvolutionStore } from '@/stores/evolution'

const evolutionStore = useEvolutionStore()

const emit = defineEmits<{
  (e: 'toast', msg: string, type?: 'success' | 'error'): void
}>()

const isSubmitting = ref(false)

const currentGap = computed(() => evolutionStore.selectedGapForTicket)

const ticketForm = reactive({
  title: '',
  domain: '',
  assignee: '陈明 · 跨境物流专员 (工号 10034 · 跨境电商部)',
  deadline: '2026-09-30 (7日内完成编制)',
  notes: '请补充海关最新 HS Code 对应征税比例及港口滞港费核算准则，并以 Markdown/Word 格式上传至《跨境业务库》。'
})

watch(
  () => evolutionStore.selectedGapForTicket,
  (newGap) => {
    if (newGap) {
      ticketForm.title = `【知识缺口补全】${newGap.query_text}`
      ticketForm.domain = newGap.domain || '跨境电商与供应链 (已自动识别)'
      ticketForm.assignee = '陈明 · 跨境物流专员 (工号 10034 · 跨境电商部)'
      ticketForm.deadline = '2026-09-30 (7日内完成编制)'
      ticketForm.notes = `针对频繁未命中的用户提问“${newGap.query_text}”，请相关责任人梳理标准规范并上传至知识库沉淀。`
    }
  },
  { immediate: true }
)

const closeModal = () => {
  evolutionStore.showGapModal = false
  evolutionStore.selectedGapForTicket = null
}

const submitTicket = async () => {
  if (!currentGap.value) return
  if (!ticketForm.title.trim()) return

  isSubmitting.value = true
  try {
    await evolutionStore.convertKnowledgeGap(currentGap.value.id, {
      title: ticketForm.title.trim(),
      domain: ticketForm.domain.trim(),
      assignee: ticketForm.assignee.trim(),
      deadline: ticketForm.deadline.trim(),
      notes: ticketForm.notes.trim()
    })
    emit('toast', `知识补全工单 [${ticketForm.title}] 下发成功，已邮件通知责任人`, 'success')
    closeModal()
  } catch (err) {
    emit('toast', err instanceof Error ? err.message : '工单下发失败', 'error')
  } finally {
    isSubmitting.value = false
  }
}

const markResolved = async () => {
  if (!currentGap.value) return
  isSubmitting.value = true
  try {
    await evolutionStore.resolveKnowledgeGap(currentGap.value.id)
    emit('toast', `知识缺口 [${currentGap.value.query_text}] 已成功标记为闭环`, 'success')
    closeModal()
  } catch (err) {
    emit('toast', err instanceof Error ? err.message : '标记闭环失败', 'error')
  } finally {
    isSubmitting.value = false
  }
}
</script>
