<template>
  <!-- FE-M5: 高频候选 FAQ 列表与聚类审核 (PAGE-06) -->
  <div class="space-y-4">
    <!-- Header Tool & Filter Bar -->
    <div class="flex flex-wrap items-center justify-between gap-3 bg-white p-3.5 rounded-xl border border-[#E5E7EB] shadow-sm">
      <div class="flex items-center gap-2">
        <span class="text-xs font-semibold text-[#0F172A] flex items-center gap-1.5">
          <Sparkles :size="14" class="text-[#0071E3]" />
          <span>语义聚类候选队列</span>
        </span>
        <span class="text-[11px] px-2 py-0.5 rounded-full bg-blue-50 text-[#0071E3] font-medium border border-blue-100">
          共 {{ evolutionStore.totalCandidates }} 条待审
        </span>
      </div>

      <div class="flex items-center gap-2">
        <!-- Status Filter Filter Tabs -->
        <div class="inline-flex p-0.5 bg-slate-100 rounded-lg text-xs font-medium">
          <button
            type="button"
            class="px-2.5 py-1 rounded-md transition-colors"
            :class="evolutionStore.candidateStatusFilter === 'PENDING' ? 'bg-white text-[#0071E3] shadow-sm' : 'text-slate-600 hover:text-slate-900'"
            @click="setStatusFilter('PENDING')"
          >
            待审核
          </button>
          <button
            type="button"
            class="px-2.5 py-1 rounded-md transition-colors"
            :class="evolutionStore.candidateStatusFilter === 'ACCEPTED' ? 'bg-white text-[#0071E3] shadow-sm' : 'text-slate-600 hover:text-slate-900'"
            @click="setStatusFilter('ACCEPTED')"
          >
            已采纳
          </button>
          <button
            type="button"
            class="px-2.5 py-1 rounded-md transition-colors"
            :class="evolutionStore.candidateStatusFilter === 'REJECTED' ? 'bg-white text-[#0071E3] shadow-sm' : 'text-slate-600 hover:text-slate-900'"
            @click="setStatusFilter('REJECTED')"
          >
            已驳回
          </button>
        </div>

        <!-- Trigger Cluster Mining Button -->
        <button
          type="button"
          class="px-3 py-1.5 bg-[#0071E3] hover:bg-[#0077ED] text-white rounded-lg text-xs font-medium inline-flex items-center gap-1.5 transition-colors shadow-sm disabled:opacity-50"
          :disabled="evolutionStore.isMining"
          @click="handleTriggerMining"
        >
          <RotateCw :size="13" :class="{ 'animate-spin': evolutionStore.isMining }" />
          <span>{{ evolutionStore.isMining ? '正在聚类挖掘...' : '执行提问语义聚类' }}</span>
        </button>
      </div>
    </div>

    <!-- Candidate Cards Grid -->
    <div v-if="evolutionStore.isLoading" class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div v-for="i in 4" :key="i" class="bg-white rounded-xl border border-gray-100 p-5 shadow-sm animate-pulse space-y-3">
        <div class="h-4 bg-gray-100 rounded w-1/3"></div>
        <div class="h-5 bg-gray-100 rounded w-4/5"></div>
        <div class="h-16 bg-gray-50 rounded"></div>
      </div>
    </div>

    <div v-else-if="evolutionStore.candidates.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div
        v-for="candidate in evolutionStore.candidates"
        :key="candidate.id"
        class="bg-white rounded-xl border border-[#E5E7EB] hover:border-[#0071E3]/40 p-4 shadow-sm hover:shadow-md transition-all flex flex-col justify-between gap-3 group"
      >
        <div class="space-y-2.5">
          <!-- Card Top Meta -->
          <div class="flex items-center justify-between gap-2 border-b border-[#F1F5F9] pb-2 text-[11px]">
            <div class="flex items-center gap-1.5">
              <span class="font-mono text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                {{ candidate.cluster_id }}
              </span>
              <span class="font-medium text-[#0071E3] bg-blue-50 px-2 py-0.5 rounded-full border border-blue-100 flex items-center gap-1">
                <Flame :size="11" class="text-orange-500 shrink-0" />
                <span>提问频次 {{ candidate.cluster_count }} 次</span>
              </span>
            </div>

            <div class="flex items-center gap-2">
              <span
                class="px-2 py-0.5 rounded-full font-medium"
                :class="candidate.confidence_score >= 0.9 ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-700 border border-amber-200'"
              >
                置信度 {{ Math.round(candidate.confidence_score * 100) }}%
              </span>
              <span
                v-if="candidate.status !== 'PENDING'"
                class="px-1.5 py-0.5 rounded text-[10px] font-medium"
                :class="candidate.status === 'ACCEPTED' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'"
              >
                {{ candidate.status === 'ACCEPTED' ? '已采纳' : '已驳回' }}
              </span>
            </div>
          </div>

          <!-- Suggested Question -->
          <div>
            <div class="text-[11px] font-semibold text-slate-400 mb-0.5">推荐标准问题</div>
            <h4 class="text-xs font-semibold text-[#0F172A] leading-snug">
              {{ candidate.suggested_question }}
            </h4>
          </div>

          <!-- Suggested Answer -->
          <div>
            <div class="text-[11px] font-semibold text-slate-400 mb-0.5">归纳回答建议</div>
            <p class="text-xs text-[#475569] leading-relaxed bg-[#F8FAFC] p-2.5 rounded-lg border border-slate-100 line-clamp-3">
              {{ candidate.suggested_answer }}
            </p>
          </div>

          <!-- Clustered Queries Badges -->
          <div v-if="candidate.similar_queries && candidate.similar_queries.length > 0">
            <div class="text-[10px] font-medium text-slate-400 mb-1">包含历史类似提问 ({{ candidate.similar_queries.length }})</div>
            <div class="flex flex-wrap gap-1">
              <span
                v-for="(sq, idx) in candidate.similar_queries.slice(0, 3)"
                :key="idx"
                class="text-[10px] px-2 py-0.5 rounded bg-slate-100 text-slate-600 max-w-[200px] truncate"
              >
                {{ sq }}
              </span>
              <span
                v-if="candidate.similar_queries.length > 3"
                class="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-400"
              >
                +{{ candidate.similar_queries.length - 3 }}
              </span>
            </div>
          </div>
        </div>

        <!-- Action Footer -->
        <div class="flex items-center justify-between pt-2 border-t border-[#F1F5F9] mt-1 text-xs">
          <span class="text-[10px] text-slate-400">
            {{ candidate.created_at || '刚刚挖掘' }}
          </span>

          <div v-if="candidate.status === 'PENDING'" class="flex items-center gap-1.5">
            <button
              type="button"
              class="px-2.5 py-1 text-xs text-rose-600 hover:bg-rose-50 rounded-lg transition-colors font-medium border border-rose-200"
              @click="handleReject(candidate)"
            >
              驳回
            </button>
            <button
              type="button"
              class="px-2.5 py-1 text-xs text-[#0071E3] hover:bg-blue-50 rounded-lg transition-colors font-medium border border-blue-200 inline-flex items-center gap-1"
              @click="evolutionStore.openEditDrawer(candidate)"
            >
              <Edit3 :size="12" />
              <span>润色采纳</span>
            </button>
            <button
              type="button"
              class="px-3 py-1 text-xs bg-[#0071E3] hover:bg-[#0077ED] text-white rounded-lg transition-colors font-medium shadow-sm inline-flex items-center gap-1"
              @click="handleQuickApprove(candidate)"
            >
              <Check :size="12" />
              <span>快速采纳</span>
            </button>
          </div>
          <div v-else class="text-[11px] text-slate-400 font-medium">
            已完成审核归档
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-else
      class="bg-white rounded-xl border border-[#E5E7EB] p-12 text-center text-slate-400 space-y-3"
    >
      <div class="w-12 h-12 rounded-full bg-blue-50 text-[#0071E3] flex items-center justify-center mx-auto">
        <Sparkles :size="24" />
      </div>
      <div class="text-xs font-semibold text-slate-700">暂无待审核的高频候选 FAQ</div>
      <p class="text-[11px] text-slate-400 max-w-sm mx-auto">
        系统会基于员工对话问答历史定期进行语义嵌入聚类分析，亦可点击上方按钮立即发起聚类挖掘。
      </p>
      <button
        type="button"
        class="px-3 py-1.5 bg-[#0071E3] text-white rounded-lg text-xs font-medium inline-flex items-center gap-1.5 shadow-sm"
        @click="handleTriggerMining"
      >
        <RotateCw :size="12" />
        <span>立即触发语义聚类挖掘</span>
      </button>
    </div>

    <!-- Pagination Controls -->
    <div
      v-if="evolutionStore.totalCandidates > evolutionStore.candidatesPageSize"
      class="flex items-center justify-between bg-white px-4 py-2.5 rounded-xl border border-[#E5E7EB] text-xs text-slate-600"
    >
      <span>共 {{ evolutionStore.totalCandidates }} 条记录</span>
      <div class="flex items-center gap-2">
        <button
          type="button"
          :disabled="evolutionStore.candidatesPage <= 1"
          class="px-2.5 py-1 border border-slate-200 rounded hover:bg-slate-50 disabled:opacity-40 transition-colors"
          @click="changePage(evolutionStore.candidatesPage - 1)"
        >
          上一页
        </button>
        <span class="font-mono text-slate-800">第 {{ evolutionStore.candidatesPage }} 页</span>
        <button
          type="button"
          :disabled="evolutionStore.candidatesPage * evolutionStore.candidatesPageSize >= evolutionStore.totalCandidates"
          class="px-2.5 py-1 border border-slate-200 rounded hover:bg-slate-50 disabled:opacity-40 transition-colors"
          @click="changePage(evolutionStore.candidatesPage + 1)"
        >
          下一页
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 候选 FAQ 聚类推荐卡片队列组件
 * 模块: FE-M5 (PAGE-06)
 */

import { Sparkles, Flame, Edit3, Check, RotateCw } from 'lucide-vue-next'
import { useEvolutionStore } from '@/stores/evolution'
import type { FaqCandidate } from '@/types/evolution'

const evolutionStore = useEvolutionStore()

const emit = defineEmits<{
  (e: 'toast', msg: string, type?: 'success' | 'error'): void
}>()

const setStatusFilter = (status: string) => {
  evolutionStore.candidateStatusFilter = status
  evolutionStore.fetchCandidates(1)
}

const changePage = (page: number) => {
  evolutionStore.fetchCandidates(page)
}

const handleTriggerMining = async () => {
  try {
    const res = await evolutionStore.triggerMining()
    emit('toast', `语义聚类挖掘已完成，新挖掘到 ${res?.mined_clusters || 2} 个高频提问候选簇`, 'success')
  } catch (err) {
    emit('toast', err instanceof Error ? err.message : '聚类挖掘失败', 'error')
  }
}

const handleQuickApprove = async (candidate: FaqCandidate) => {
  try {
    await evolutionStore.approveCandidate(candidate.id, {
      standard_question: candidate.suggested_question,
      standard_answer: candidate.suggested_answer,
      category: '通用',
      similar_questions: candidate.similar_queries || [],
      is_cached: true
    })
    emit('toast', `候选 FAQ [${candidate.suggested_question}] 已成功采纳并上架`, 'success')
  } catch (err) {
    emit('toast', err instanceof Error ? err.message : '采纳候选失败', 'error')
  }
}

const handleReject = async (candidate: FaqCandidate) => {
  if (!confirm(`确认驳回该候选问题：“${candidate.suggested_question}”？`)) return
  try {
    await evolutionStore.rejectCandidate(candidate.id, { reason: '运营人工复核不具备沉淀为全局标准问答条件' })
    emit('toast', `已驳回候选问题：[${candidate.suggested_question}]`, 'success')
  } catch (err) {
    emit('toast', err instanceof Error ? err.message : '驳回失败', 'error')
  }
}
</script>
