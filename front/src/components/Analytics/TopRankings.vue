<template>
  <!-- FE-M6: 高频提问与引用 TOP 5 双榜单 (PAGE-07 原型 1:1) -->
  <div class="bg-white rounded-xl border border-[#E5E7EB] p-4 shadow-sm flex flex-col justify-between">
    <!-- Header with Tab Switcher -->
    <div class="flex items-center justify-between pb-3 border-b border-[#F1F5F9]">
      <div class="flex items-center gap-1 bg-slate-100 p-0.5 rounded-lg text-xs font-medium">
        <button
          type="button"
          class="px-2.5 py-1 rounded-md transition-colors"
          :class="activeTab === 'queries' ? 'bg-white text-[#0071E3] shadow-xs' : 'text-slate-600 hover:text-slate-900'"
          @click="activeTab = 'queries'"
        >
          高频提问 TOP 5
        </button>
        <button
          type="button"
          class="px-2.5 py-1 rounded-md transition-colors"
          :class="activeTab === 'knowledge' ? 'bg-white text-[#0071E3] shadow-xs' : 'text-slate-600 hover:text-slate-900'"
          @click="activeTab = 'knowledge'"
        >
          热门引用知识
        </button>
      </div>

      <span class="text-[10px] text-[#0071E3] bg-blue-50 px-1.5 py-0.5 rounded border border-blue-100 font-mono font-medium">
        PRD 5.6.2
      </span>
    </div>

    <!-- Ranking List Body -->
    <div class="space-y-2 mt-3 flex-1 flex flex-col justify-around">
      <!-- Tab 1: Queries -->
      <template v-if="activeTab === 'queries'">
        <div
          v-for="item in topQueries"
          :key="item.rank"
          class="flex items-center justify-between gap-2.5 hover:bg-slate-50 px-2 py-1.5 rounded-lg transition-colors"
        >
          <div class="flex items-center gap-2 min-w-0 flex-1">
            <span
              class="w-4 h-4 rounded text-[10px] font-mono font-bold flex items-center justify-center shrink-0"
              :class="getRankBadgeClass(item.rank)"
            >
              {{ item.rank }}
            </span>
            <span class="text-xs text-[#0F172A] font-medium truncate" :title="item.query">
              {{ item.query }}
            </span>
          </div>
          <span class="text-[11px] font-mono text-[#64748B] shrink-0 font-medium">
            {{ item.count }}次
          </span>
        </div>
      </template>

      <!-- Tab 2: Knowledge Documents -->
      <template v-else>
        <div
          v-for="item in topKnowledge"
          :key="item.rank"
          class="flex items-center justify-between gap-2.5 hover:bg-slate-50 px-2 py-1.5 rounded-lg transition-colors"
        >
          <div class="flex items-center gap-2 min-w-0 flex-1">
            <span
              class="w-4 h-4 rounded text-[10px] font-mono font-bold flex items-center justify-center shrink-0"
              :class="getRankBadgeClass(item.rank)"
            >
              {{ item.rank }}
            </span>
            <span class="text-xs text-[#0F172A] font-medium truncate" :title="item.title">
              {{ item.title }}
            </span>
          </div>
          <span class="text-[11px] font-mono text-[#64748B] shrink-0 font-medium">
            {{ item.count }}次
          </span>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * TOP 5 双榜单组件
 * 模块: FE-M6 (PAGE-07 原型 1:1)
 */

import { ref, computed } from 'vue'
import { useAnalyticsStore } from '@/stores/analytics'
import type { TopQueryItem, TopKnowledgeItem } from '@/types/analytics'

const analyticsStore = useAnalyticsStore()
const activeTab = ref<'queries' | 'knowledge'>('queries')

const fallbackQueries: TopQueryItem[] = [
  { rank: 1, query: '差旅与住宿报销标准及额度', count: 142 },
  { rank: 2, query: '跨境清关关税与港口延误预警', count: 118 },
  { rank: 3, query: '年假与带薪病假折算规则', count: 96 },
  { rank: 4, query: '研发内网 VPN 与堡垒机权限', count: 84 },
  { rank: 5, query: '供应商准入资质与付款账期', count: 72 }
]

const fallbackKnowledge: TopKnowledgeItem[] = [
  { rank: 1, title: '《员工差旅与住宿报销管理规范》', count: 186 },
  { rank: 2, title: '《跨境电商出口清关与税务政策指南》', count: 145 },
  { rank: 3, title: '《企业考勤管理与法定假期实施办法》', count: 129 },
  { rank: 4, title: '《研发基础架构与内网安全访问指引》', count: 112 },
  { rank: 5, title: '《供应链采购流程与供应商管理办法》', count: 98 }
]

const topQueries = computed<TopQueryItem[]>(() => {
  if (analyticsStore.topRankings.top_queries?.length > 0) {
    return analyticsStore.topRankings.top_queries.map((item: any, idx: number) => ({
      rank: item.rank || idx + 1,
      query: item.query || item.title || '',
      count: item.count ?? item.hit_count ?? 0
    }))
  }
  return fallbackQueries
})

const topKnowledge = computed<TopKnowledgeItem[]>(() => {
  if (analyticsStore.topRankings.top_knowledge?.length > 0) {
    return analyticsStore.topRankings.top_knowledge.map((item: any, idx: number) => ({
      rank: item.rank || idx + 1,
      title: item.title || item.query || '',
      count: item.count ?? item.hit_count ?? 0
    }))
  }
  return fallbackKnowledge
})

const getRankBadgeClass = (rank: number): string => {
  switch (rank) {
    case 1:
      return 'bg-amber-500 text-white shadow-2xs'
    case 2:
      return 'bg-slate-400 text-white'
    case 3:
      return 'bg-amber-700 text-white'
    default:
      return 'bg-slate-100 text-slate-600'
  }
}
</script>
