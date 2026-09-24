<template>
  <!-- FE-M6: 端到端响应耗时分布组件 (PAGE-07 原型 1:1) -->
  <div class="bg-white rounded-xl border border-[#E5E7EB] p-4 shadow-sm flex flex-col justify-between">
    <!-- Header -->
    <div class="flex items-center justify-between pb-3 border-b border-[#F1F5F9]">
      <div class="flex items-center gap-2">
        <h3 class="text-xs font-semibold text-[#0F172A]">端到端响应耗时分布</h3>
      </div>
      <span class="text-[11px] font-mono font-medium text-[#0071E3] bg-blue-50 px-2 py-0.5 rounded-full border border-blue-100">
        平均 {{ analyticsStore.summary.avg_latency_ms || 0 }}ms
      </span>
    </div>

    <!-- Distribution List -->
    <div class="space-y-3 mt-3 flex-1 flex flex-col justify-around">
      <div
        v-for="(item, idx) in distributionList"
        :key="idx"
        class="space-y-1"
      >
        <div class="flex items-center justify-between text-xs">
          <span class="text-[#475569] font-medium text-[11px]">{{ item.label }}</span>
          <span class="font-mono font-semibold text-[#0F172A] text-[11px]">{{ item.percent }}%</span>
        </div>
        <div class="w-full h-2 rounded-full bg-slate-100 overflow-hidden flex">
          <div
            class="h-full rounded-full transition-all duration-500"
            :class="getBarColor(idx)"
            :style="{ width: `${item.percent}%` }"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 响应延时分布组件
 * 模块: FE-M6 (PAGE-07 原型 1:1)
 */

import { computed } from 'vue'
import { useAnalyticsStore } from '@/stores/analytics'
import type { LatencyBucket } from '@/types/analytics'

const analyticsStore = useAnalyticsStore()

const defaultEmptyDistribution: LatencyBucket[] = [
  { label: '< 50ms (FAQ直出)', percent: 0 },
  { label: '50-200ms (小切片)', percent: 0 },
  { label: '200-500ms (多跳)', percent: 0 },
  { label: '500ms-1s (重排)', percent: 0 },
  { label: '> 1s (长上下文)', percent: 0 }
]

const distributionList = computed<LatencyBucket[]>(() => {
  return analyticsStore.latencyDistribution.length > 0
    ? analyticsStore.latencyDistribution
    : defaultEmptyDistribution
})

const getBarColor = (index: number): string => {
  switch (index) {
    case 0:
      return 'bg-emerald-500'
    case 1:
      return 'bg-[#0071E3]'
    case 2:
      return 'bg-indigo-500'
    case 3:
      return 'bg-amber-500'
    case 4:
    default:
      return 'bg-rose-500'
  }
}
</script>
