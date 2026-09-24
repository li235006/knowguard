<template>
  <!-- FE-M5: 知识盲区缺口清单 (PAGE-06 原型精准对齐) -->
  <div class="space-y-4">
    <!-- Header Tool & Filter Bar -->
    <div class="flex flex-wrap items-center justify-between gap-3 bg-white p-3.5 rounded-xl border border-[#E5E7EB] shadow-sm">
      <div class="flex items-center gap-2">
        <span class="text-xs font-semibold text-[#0F172A] flex items-center gap-1.5">
          <AlertCircle :size="14" class="text-rose-500" />
          <span>知识盲区缺口池</span>
        </span>
        <span class="text-[11px] px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 font-medium border border-rose-100">
          共 {{ evolutionStore.totalKnowledgeGaps }} 条缺口记录
        </span>
      </div>

      <div class="flex flex-wrap items-center gap-2.5">
        <!-- Sort Control -->
        <div class="inline-flex items-center gap-1 bg-slate-50 border border-slate-200 px-2 py-1 rounded-lg text-xs">
          <span class="text-slate-500 text-[11px]">排序:</span>
          <button
            type="button"
            class="px-2 py-0.5 rounded text-[11px] font-medium transition-colors"
            :class="evolutionStore.gapSortBy === 'hit_count' ? 'bg-[#0071E3] text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'"
            @click="setSortBy('hit_count')"
          >
            频次最高
          </button>
          <button
            type="button"
            class="px-2 py-0.5 rounded text-[11px] font-medium transition-colors"
            :class="evolutionStore.gapSortBy === 'created_at' ? 'bg-[#0071E3] text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'"
            @click="setSortBy('created_at')"
          >
            最新发生
          </button>
        </div>

        <!-- Status Filter Filter Tabs -->
        <div class="inline-flex p-0.5 bg-slate-100 rounded-lg text-xs font-medium">
          <button
            type="button"
            class="px-2.5 py-1 rounded-md transition-colors"
            :class="evolutionStore.gapStatusFilter === 'ALL' ? 'bg-white text-[#0071E3] shadow-sm' : 'text-slate-600 hover:text-slate-900'"
            @click="setGapFilter('ALL')"
          >
            全部
          </button>
          <button
            type="button"
            class="px-2.5 py-1 rounded-md transition-colors"
            :class="evolutionStore.gapStatusFilter === 'OPEN' ? 'bg-white text-[#0071E3] shadow-sm' : 'text-slate-600 hover:text-slate-900'"
            @click="setGapFilter('OPEN')"
          >
            待转建
          </button>
          <button
            type="button"
            class="px-2.5 py-1 rounded-md transition-colors"
            :class="evolutionStore.gapStatusFilter === 'CONVERTED' ? 'bg-white text-[#0071E3] shadow-sm' : 'text-slate-600 hover:text-slate-900'"
            @click="setGapFilter('CONVERTED')"
          >
            处理中
          </button>
          <button
            type="button"
            class="px-2.5 py-1 rounded-md transition-colors"
            :class="evolutionStore.gapStatusFilter === 'RESOLVED' ? 'bg-white text-[#0071E3] shadow-sm' : 'text-slate-600 hover:text-slate-900'"
            @click="setGapFilter('RESOLVED')"
          >
            已闭环
          </button>
          <button
            type="button"
            class="px-2.5 py-1 rounded-md transition-colors"
            :class="evolutionStore.gapStatusFilter === 'IGNORED' ? 'bg-white text-[#0071E3] shadow-sm' : 'text-slate-600 hover:text-slate-900'"
            @click="setGapFilter('IGNORED')"
          >
            已忽略
          </button>
        </div>
      </div>
    </div>

    <!-- Knowledge Gaps Table -->
    <div class="bg-white rounded-xl border border-[#E5E7EB] shadow-sm overflow-hidden flex flex-col">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs border-collapse">
          <thead>
            <tr class="bg-[#F8FAFC] text-[#64748B] border-b border-[#F1F5F9] font-medium text-[11px]">
              <th class="py-3 px-4 w-28">缺口编号</th>
              <th class="py-3 px-4 min-w-[260px]">用户未命中原始提问词</th>
              <th class="py-3 px-4 w-24 text-center">聚类频次</th>
              <th class="py-3 px-4 w-36">所属业务域</th>
              <th class="py-3 px-4 w-28">首次发生时间</th>
              <th class="py-3 px-4 w-20 text-center">严重级</th>
              <th class="py-3 px-4 w-24 text-center">闭环状态</th>
              <th class="py-3 px-4 w-44 text-right">流转操作</th>
            </tr>
          </thead>

          <tbody v-if="evolutionStore.isLoading" class="divide-y divide-[#F1F5F9]">
            <tr v-for="i in 5" :key="i" class="animate-pulse">
              <td colspan="8" class="py-4 px-4">
                <div class="h-4 bg-gray-100 rounded w-full"></div>
              </td>
            </tr>
          </tbody>

          <tbody v-else-if="evolutionStore.knowledgeGaps.length > 0" class="divide-y divide-[#F1F5F9]">
            <tr
              v-for="gap in evolutionStore.knowledgeGaps"
              :key="gap.id"
              class="hover:bg-[#F8FAFC] transition-colors"
            >
              <!-- Gap Code -->
              <td class="py-3 px-4 font-mono font-medium text-[#0071E3] text-[11px]">
                {{ gap.gap_code || `GAP-2024-${String(gap.id).padStart(3, '0')}` }}
              </td>

              <!-- Query Text -->
              <td class="py-3 px-4">
                <div class="flex items-center gap-1.5 font-medium text-[#0F172A] leading-snug">
                  <span>“{{ gap.query_text }}”</span>
                </div>
                <div v-if="gap.reason" class="text-[10px] text-slate-400 mt-0.5">
                  成因: {{ gap.reason }}
                </div>
              </td>

              <!-- Hit Count -->
              <td class="py-3 px-4 text-center">
                <span class="font-mono font-semibold text-[#0071E3] bg-blue-50 px-2 py-0.5 rounded-full text-[11px]">
                  {{ gap.hit_count }} 次
                </span>
              </td>

              <!-- Domain -->
              <td class="py-3 px-4 text-[#475569]">
                <span class="text-[11px] font-medium">
                  {{ gap.domain || '通用业务域' }}
                </span>
              </td>

              <!-- First Seen -->
              <td class="py-3 px-4 text-[#94A3B8] font-mono text-[11px]">
                {{ formatTime(gap.first_seen_at || gap.created_at) }}
              </td>

              <!-- Severity -->
              <td class="py-3 px-4 text-center">
                <span
                  class="px-2 py-0.5 rounded text-[10px] font-mono font-bold"
                  :class="getSeverityClass(gap.severity || (gap.hit_count >= 15 ? 'P1' : (gap.hit_count >= 8 ? 'P2' : 'P3')))"
                >
                  {{ gap.severity || (gap.hit_count >= 15 ? 'P1' : (gap.hit_count >= 8 ? 'P2' : 'P3')) }}
                </span>
              </td>

              <!-- Status -->
              <td class="py-3 px-4 text-center">
                <span
                  class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium"
                  :class="getStatusBadgeClass(gap.status)"
                >
                  {{ getStatusText(gap.status) }}
                </span>
              </td>

              <!-- Action -->
              <td class="py-3 px-4 text-right whitespace-nowrap">
                <div class="inline-flex items-center justify-end gap-1.5">
                  <!-- Case 1: OPEN (待转建) -->
                  <template v-if="gap.status === 'OPEN'">
                    <button
                      type="button"
                      class="px-2 py-1 text-[11px] font-medium text-white bg-[#0071E3] hover:bg-[#0077ED] rounded transition-colors shadow-2xs"
                      @click="evolutionStore.openGapModal(gap)"
                    >
                      转建工单
                    </button>
                    <button
                      type="button"
                      :disabled="actionLoadingId === gap.id"
                      class="px-2 py-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 hover:bg-emerald-100 rounded border border-emerald-200 transition-colors disabled:opacity-50"
                      title="标记此问题已闭环"
                      @click="handleResolve(gap)"
                    >
                      解决
                    </button>
                    <button
                      type="button"
                      :disabled="actionLoadingId === gap.id"
                      class="px-2 py-1 text-[11px] font-medium text-slate-500 bg-slate-100 hover:bg-slate-200 rounded transition-colors disabled:opacity-50"
                      title="忽略此缺口提问"
                      @click="handleIgnore(gap)"
                    >
                      忽略
                    </button>
                  </template>

                  <!-- Case 2: CONVERTED (处理中) -->
                  <template v-else-if="gap.status === 'CONVERTED'">
                    <button
                      type="button"
                      class="px-2 py-1 text-[11px] font-medium text-blue-600 hover:text-blue-800 transition-colors"
                      @click="evolutionStore.openGapModal(gap)"
                    >
                      查看工单
                    </button>
                    <button
                      type="button"
                      :disabled="actionLoadingId === gap.id"
                      class="px-2 py-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 hover:bg-emerald-100 rounded border border-emerald-200 transition-colors disabled:opacity-50"
                      @click="handleResolve(gap)"
                    >
                      完成闭环
                    </button>
                  </template>

                  <!-- Case 3: RESOLVED (已解决) -->
                  <template v-else-if="gap.status === 'RESOLVED'">
                    <span class="text-[11px] text-emerald-600 font-medium inline-flex items-center gap-1">
                      <Check :size="12" />
                      <span>已闭环</span>
                    </span>
                  </template>

                  <!-- Case 4: IGNORED (已忽略) -->
                  <template v-else-if="gap.status === 'IGNORED' || gap.status === 'DISMISSED'">
                    <span class="text-[11px] text-slate-400 font-medium">已归档忽略</span>
                  </template>
                </div>
              </td>
            </tr>
          </tbody>

          <!-- Empty State -->
          <tbody v-else>
            <tr>
              <td colspan="8" class="py-16 text-center text-[#94A3B8]">
                <div class="flex flex-col items-center gap-2">
                  <div class="w-12 h-12 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center">
                    <CheckCircle2 :size="24" />
                  </div>
                  <span class="font-medium text-slate-600">当前分类无知识缺口记录</span>
                  <span class="text-slate-400 text-[11px]">所有未命中提问均已完成工单闭环或转建为官方 FAQ</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div
        v-if="evolutionStore.totalKnowledgeGaps > evolutionStore.gapsPageSize"
        class="p-3 border-t border-[#F1F5F9] bg-[#FAFAFA]/60 flex items-center justify-between text-xs text-[#64748B]"
      >
        <div>
          共 <span class="font-medium text-[#0F172A]">{{ evolutionStore.totalKnowledgeGaps }}</span> 个缺口问题
        </div>
        <div class="flex items-center gap-2">
          <button
            type="button"
            :disabled="evolutionStore.gapsPage <= 1"
            class="px-2.5 py-1 border border-[#E5E7EB] rounded bg-white hover:bg-gray-50 disabled:opacity-40 transition-colors"
            @click="changePage(evolutionStore.gapsPage - 1)"
          >
            上一页
          </button>
          <span class="px-2 font-mono text-[#0F172A]">第 {{ evolutionStore.gapsPage }} 页</span>
          <button
            type="button"
            :disabled="evolutionStore.gapsPage * evolutionStore.gapsPageSize >= evolutionStore.totalKnowledgeGaps"
            class="px-2.5 py-1 border border-[#E5E7EB] rounded bg-white hover:bg-gray-50 disabled:opacity-40 transition-colors"
            @click="changePage(evolutionStore.gapsPage + 1)"
          >
            下一页
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 知识盲区缺口池组件
 * 模块: FE-M5 (PAGE-06)
 */

import { ref } from 'vue'
import { AlertCircle, CheckCircle2, Check } from 'lucide-vue-next'
import { useEvolutionStore } from '@/stores/evolution'
import type { KnowledgeGap } from '@/types/evolution'

const evolutionStore = useEvolutionStore()

const emit = defineEmits<{
  (e: 'toast', msg: string, type?: 'success' | 'error'): void
}>()

const actionLoadingId = ref<number | null>(null)

const setGapFilter = (status: string) => {
  evolutionStore.gapStatusFilter = status
  evolutionStore.fetchKnowledgeGaps(1)
}

const setSortBy = (sortBy: 'hit_count' | 'created_at') => {
  evolutionStore.gapSortBy = sortBy
  evolutionStore.fetchKnowledgeGaps(1)
}

const changePage = (page: number) => {
  evolutionStore.fetchKnowledgeGaps(page)
}

const handleResolve = async (gap: KnowledgeGap) => {
  actionLoadingId.value = gap.id
  try {
    await evolutionStore.resolveKnowledgeGap(gap.id)
    emit('toast', `知识缺口 [${gap.query_text}] 已成功标记为解决闭环`, 'success')
  } catch (err) {
    emit('toast', err instanceof Error ? err.message : '标记解决失败', 'error')
  } finally {
    actionLoadingId.value = null
  }
}

const handleIgnore = async (gap: KnowledgeGap) => {
  actionLoadingId.value = gap.id
  try {
    await evolutionStore.ignoreKnowledgeGap(gap.id)
    emit('toast', `知识缺口 [${gap.query_text}] 已成功忽略并归档`, 'success')
  } catch (err) {
    emit('toast', err instanceof Error ? err.message : '忽略失败', 'error')
  } finally {
    actionLoadingId.value = null
  }
}

const formatTime = (timeStr?: string): string => {
  if (!timeStr) return '09-24 10:00'
  try {
    return timeStr.replace('T', ' ').substring(5, 16)
  } catch {
    return timeStr
  }
}

const getSeverityClass = (sev: string): string => {
  switch (sev) {
    case 'P1':
      return 'bg-rose-100 text-rose-700 border border-rose-200'
    case 'P2':
      return 'bg-amber-100 text-amber-800 border border-amber-200'
    default:
      return 'bg-slate-100 text-slate-700 border border-slate-200'
  }
}

const getStatusBadgeClass = (status: string): string => {
  switch (status) {
    case 'CONVERTED':
      return 'bg-blue-50 text-[#0071E3] border border-blue-200'
    case 'RESOLVED':
      return 'bg-emerald-50 text-emerald-700 border border-emerald-200'
    case 'IGNORED':
    case 'DISMISSED':
      return 'bg-slate-100 text-slate-500 border border-slate-200'
    case 'OPEN':
    default:
      return 'bg-amber-50 text-amber-700 border border-amber-200'
  }
}

const getStatusText = (status: string): string => {
  switch (status) {
    case 'CONVERTED':
      return '处理中'
    case 'RESOLVED':
      return '已闭环'
    case 'IGNORED':
      return '已忽略'
    case 'DISMISSED':
      return '已沉淀FAQ'
    case 'OPEN':
    default:
      return '待转建'
  }
}
</script>
