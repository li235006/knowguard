<template>
  <!-- FE-M5: FAQ 润色对比编辑与发布抽屉 (PAGE-06) -->
  <div v-if="evolutionStore.showEditDrawer" class="fixed inset-0 z-50 overflow-hidden">
    <!-- Backdrop -->
    <div
      class="absolute inset-0 bg-black/40 backdrop-blur-sm transition-opacity"
      @click="closeDrawer"
    />

    <div class="fixed inset-y-0 right-0 max-w-full flex pl-10">
      <div class="w-screen max-w-2xl bg-white shadow-2xl flex flex-col justify-between border-l border-[#E5E7EB] animate-in slide-in-from-right duration-300">
        <!-- Drawer Header -->
        <div class="p-4 border-b border-[#F1F5F9] flex items-center justify-between shrink-0 bg-[#F8FAFC]">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-lg bg-blue-50 text-[#0071E3] flex items-center justify-center border border-blue-100">
              <Sparkles :size="16" />
            </div>
            <div>
              <h3 class="font-semibold text-sm text-[#0F172A]">审核与润色采纳 FAQ</h3>
              <p class="text-[11px] text-[#64748B]">左右对比原始提问聚合簇与提炼后的官方标准问答</p>
            </div>
          </div>
          <button
            type="button"
            class="text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-100 transition-colors"
            @click="closeDrawer"
          >
            <X :size="16" />
          </button>
        </div>

        <!-- Drawer Body -->
        <div class="flex-1 overflow-y-auto p-5 space-y-5 text-xs">
          <!-- Comparison Box: Left (Cluster Raw) vs Right (Standardized Edit) -->
          <div class="space-y-3">
            <!-- Left: Cluster Insight Card -->
            <div class="bg-[#F8FAFC] rounded-xl border border-[#E2E8F0] p-4 space-y-3">
              <div class="flex items-center justify-between text-[11px] border-b border-slate-200/60 pb-2">
                <div class="flex items-center gap-2">
                  <span class="font-semibold text-slate-700">语义聚类簇原始信息</span>
                  <span class="font-mono text-slate-500 bg-white px-1.5 py-0.5 rounded border border-slate-200">
                    {{ currentCandidate?.cluster_id }}
                  </span>
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-[#0071E3] font-medium bg-blue-50 px-2 py-0.5 rounded-full border border-blue-100">
                    聚合提问 {{ currentCandidate?.cluster_count || 1 }} 次
                  </span>
                  <span class="text-emerald-700 font-medium bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                    置信度 {{ Math.round((currentCandidate?.confidence_score || 0.9) * 100) }}%
                  </span>
                </div>
              </div>

              <!-- Cluster sample queries -->
              <div>
                <div class="text-[11px] font-medium text-slate-500 mb-1.5">聚类包含的历史用户原始提问:</div>
                <div class="flex flex-wrap gap-1.5">
                  <span
                    v-for="(sq, sIdx) in (currentCandidate?.similar_queries || [])"
                    :key="sIdx"
                    class="text-[11px] px-2 py-1 rounded-lg bg-white border border-slate-200 text-slate-700 shadow-2xs font-mono"
                  >
                    “{{ sq }}”
                  </span>
                </div>
              </div>

              <!-- AI suggested draft -->
              <div>
                <div class="text-[11px] font-medium text-slate-500 mb-1">AI 原始归纳答案草稿:</div>
                <p class="text-[11px] text-slate-600 bg-white p-2.5 rounded-lg border border-slate-200 leading-relaxed font-mono">
                  {{ currentCandidate?.suggested_answer }}
                </p>
              </div>
            </div>

            <!-- Right: Standard Formulation Form -->
            <div class="space-y-3 pt-2">
              <div class="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
                <Edit3 :size="13" class="text-[#0071E3]" />
                <span>润色沉淀为官方标准 FAQ 规范</span>
              </div>

              <!-- Standard Question Input -->
              <div class="flex flex-col gap-1">
                <label class="font-medium text-[#475569]">标准问提法 (Standard Question) *</label>
                <input
                  v-model="editForm.standard_question"
                  type="text"
                  placeholder="请输入官方正式提问句型..."
                  class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-3 py-2 text-xs text-[#0F172A] focus:outline-none focus:border-[#0071E3] font-medium"
                />
              </div>

              <!-- Category & Cache -->
              <div class="grid grid-cols-2 gap-3">
                <div class="flex flex-col gap-1">
                  <label class="font-medium text-[#475569]">业务分类 (Category)</label>
                  <input
                    v-model="editForm.category"
                    type="text"
                    placeholder="例如: 薪酬福利 / IT运维"
                    class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-3 py-2 text-xs text-[#0F172A] focus:outline-none focus:border-[#0071E3]"
                  />
                </div>

                <div class="flex flex-col gap-1">
                  <label class="font-medium text-[#475569]">极速直出策略</label>
                  <div class="flex items-center justify-between p-2 rounded-lg bg-[#F8FAFC] border border-[#E5E7EB] h-9">
                    <span class="text-[11px] text-slate-700 font-medium flex items-center gap-1">
                      <Zap :size="12" class="text-amber-500" />
                      <span>Redis 秒级直出</span>
                    </span>
                    <label class="relative inline-flex items-center cursor-pointer select-none">
                      <input
                        v-model="editForm.is_cached"
                        type="checkbox"
                        class="sr-only peer"
                      />
                      <div
                        class="w-7 h-4 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-emerald-500"
                      ></div>
                    </label>
                  </div>
                </div>
              </div>

              <!-- Standard Answer Textarea -->
              <div class="flex flex-col gap-1">
                <label class="font-medium text-[#475569]">标准回答正文 (Standard Answer) *</label>
                <textarea
                  v-model="editForm.standard_answer"
                  rows="5"
                  placeholder="请输入经润色核实后的权威解答..."
                  class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-3 py-2 text-xs text-[#0F172A] leading-relaxed focus:outline-none focus:border-[#0071E3]"
                ></textarea>
              </div>

              <!-- Similar Questions Aliases -->
              <div class="flex flex-col gap-1">
                <label class="font-medium text-[#475569]">相似问别名扩展 (逗号或换行分隔)</label>
                <textarea
                  v-model="editForm.similarQuestionsText"
                  rows="2"
                  placeholder="例如: 年假怎么休, 请假流程, 申请带薪假"
                  class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-3 py-2 text-xs text-[#0F172A] focus:outline-none focus:border-[#0071E3]"
                ></textarea>
              </div>
            </div>
          </div>
        </div>

        <!-- Drawer Footer -->
        <div class="p-4 border-t border-[#F1F5F9] bg-[#F8FAFC] flex items-center justify-between shrink-0">
          <button
            type="button"
            class="px-4 py-2 text-xs text-rose-600 hover:bg-rose-50 rounded-lg transition-colors font-medium border border-rose-200"
            @click="handleRejectInDrawer"
          >
            驳回该候选
          </button>

          <div class="flex items-center gap-2">
            <button
              type="button"
              class="px-4 py-2 text-xs text-gray-600 hover:bg-gray-100 rounded-lg transition-colors font-medium"
              @click="closeDrawer"
            >
              取消
            </button>
            <button
              type="button"
              :disabled="!editForm.standard_question.trim() || !editForm.standard_answer.trim() || isSubmitting"
              class="px-5 py-2 text-xs bg-[#0071E3] hover:bg-[#0077ED] text-white rounded-lg font-medium transition-colors disabled:opacity-50 inline-flex items-center gap-1.5 shadow-sm"
              @click="submitApprove"
            >
              <Check :size="13" />
              <span>{{ isSubmitting ? '正在采纳发布...' : '确认采纳并发布 FAQ' }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * FAQ 润色对比编辑与发布抽屉组件
 * 模块: FE-M5 (PAGE-06)
 */

import { ref, reactive, computed, watch } from 'vue'
import { Sparkles, X, Edit3, Zap, Check } from 'lucide-vue-next'
import { useEvolutionStore } from '@/stores/evolution'

const evolutionStore = useEvolutionStore()

const emit = defineEmits<{
  (e: 'toast', msg: string, type?: 'success' | 'error'): void
}>()

const isSubmitting = ref(false)

const currentCandidate = computed(() => evolutionStore.selectedCandidateForEdit)

const editForm = reactive({
  standard_question: '',
  standard_answer: '',
  category: '通用',
  similarQuestionsText: '',
  is_cached: true
})

watch(
  () => evolutionStore.selectedCandidateForEdit,
  (newCand) => {
    if (newCand) {
      editForm.standard_question = newCand.suggested_question || ''
      editForm.standard_answer = newCand.suggested_answer || ''
      editForm.category = '通用'
      editForm.similarQuestionsText = (newCand.similar_queries || []).join(', ')
      editForm.is_cached = true
    }
  },
  { immediate: true }
)

const closeDrawer = () => {
  evolutionStore.showEditDrawer = false
  evolutionStore.selectedCandidateForEdit = null
}

const submitApprove = async () => {
  if (!currentCandidate.value) return
  if (!editForm.standard_question.trim() || !editForm.standard_answer.trim()) return

  isSubmitting.value = true
  const simList = editForm.similarQuestionsText
    .split(/[,，\n]/)
    .map((s) => s.trim())
    .filter(Boolean)

  try {
    await evolutionStore.approveCandidate(currentCandidate.value.id, {
      standard_question: editForm.standard_question.trim(),
      standard_answer: editForm.standard_answer.trim(),
      category: editForm.category.trim() || '通用',
      similar_questions: simList,
      is_cached: editForm.is_cached
    })
    emit('toast', `FAQ [${editForm.standard_question}] 润色采纳成功，并已同步注入缓存`, 'success')
    closeDrawer()
  } catch (err) {
    emit('toast', err instanceof Error ? err.message : '采纳发布失败', 'error')
  } finally {
    isSubmitting.value = false
  }
}

const handleRejectInDrawer = async () => {
  if (!currentCandidate.value) return
  if (!confirm(`确认驳回候选问题：“${currentCandidate.value.suggested_question}”？`)) return
  try {
    await evolutionStore.rejectCandidate(currentCandidate.value.id, { reason: '人工审核驳回' })
    emit('toast', '候选 FAQ 已驳回', 'success')
    closeDrawer()
  } catch (err) {
    emit('toast', err instanceof Error ? err.message : '驳回失败', 'error')
  }
}
</script>
