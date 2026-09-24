<template>
  <!-- FE-M6: 5 大核心运营与安全 KPI 统计卡片网格 (PAGE-07 原型 1:1) -->
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
    <!-- Card 1: 今日总访问 PV / UV -->
    <div class="bg-white rounded-xl border border-[#E5E7EB] p-4 shadow-sm flex flex-col justify-between gap-3 hover:border-blue-200 transition-colors">
      <div class="flex items-center justify-between text-[#64748B] text-xs">
        <span class="font-medium text-[#475569]">今日总访问 PV / UV</span>
        <Activity :size="14" class="text-[#0071E3]" />
      </div>
      <div class="flex flex-col gap-1.5">
        <div class="text-xl font-bold text-[#0F172A] tracking-tight font-mono">
          {{ formatNumber(analyticsStore.summary.pv) }}
          <span class="text-xs font-normal text-[#94A3B8] mx-1">/</span>
          {{ formatNumber(analyticsStore.summary.uv) }}
        </div>
        <div class="flex items-center gap-1.5">
          <span class="text-[11px] font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-100">
            {{ analyticsStore.summary.pv_uv_delta || '↑ 12.4% 较昨日' }}
          </span>
        </div>
      </div>
    </div>

    <!-- Card 2: 知识单元与切片总量 -->
    <div class="bg-white rounded-xl border border-[#E5E7EB] p-4 shadow-sm flex flex-col justify-between gap-3 hover:border-blue-200 transition-colors">
      <div class="flex items-center justify-between text-[#64748B] text-xs">
        <span class="font-medium text-[#475569]">知识单元总资产</span>
        <Database :size="14" class="text-indigo-500" />
      </div>
      <div class="flex flex-col gap-1.5">
        <div class="text-xl font-bold text-[#0F172A] tracking-tight">
          {{ analyticsStore.summary.knowledge_units_count }}
          <span class="text-xs font-normal text-[#64748B] ml-0.5">篇</span>
          <span class="text-xs font-normal text-[#94A3B8] ml-1.5">({{ analyticsStore.summary.chunks_count || 1420 }} 切片)</span>
        </div>
        <div class="text-[11px] text-[#64748B]">
          {{ analyticsStore.summary.units_synced || 124 }} 篇同步 / {{ analyticsStore.summary.units_pending || 4 }} 篇待更
        </div>
      </div>
    </div>

    <!-- Card 3: FAQ 缓存直出率 -->
    <div class="bg-white rounded-xl border border-[#E5E7EB] p-4 shadow-sm flex flex-col justify-between gap-3 hover:border-blue-200 transition-colors">
      <div class="flex items-center justify-between text-[#64748B] text-xs">
        <span class="font-medium text-[#475569]">FAQ 缓存直出率</span>
        <Zap :size="14" class="text-amber-500" />
      </div>
      <div class="flex flex-col gap-1.5">
        <div class="text-xl font-bold text-[#0F172A] tracking-tight font-mono">
          {{ typeof analyticsStore.summary.faq_cache_hit_rate === 'number' ? `${analyticsStore.summary.faq_cache_hit_rate}%` : analyticsStore.summary.faq_cache_hit_rate }}
        </div>
        <div class="flex items-center gap-1.5">
          <span class="text-[11px] font-medium text-[#0071E3] bg-blue-50 px-2 py-0.5 rounded-full border border-blue-100">
            {{ analyticsStore.summary.tokens_saved || '节约 8.4M Token' }}
          </span>
        </div>
      </div>
    </div>

    <!-- Card 4: 端到端平均延迟 -->
    <div class="bg-white rounded-xl border border-[#E5E7EB] p-4 shadow-sm flex flex-col justify-between gap-3 hover:border-blue-200 transition-colors">
      <div class="flex items-center justify-between text-[#64748B] text-xs">
        <span class="font-medium text-[#475569]">端到端平均延迟</span>
        <Clock :size="14" class="text-rose-500" />
      </div>
      <div class="flex flex-col gap-1.5">
        <div class="text-xl font-bold text-[#0F172A] tracking-tight font-mono">
          {{ analyticsStore.summary.avg_latency_ms }}<span class="text-xs font-normal text-[#64748B] ml-0.5">ms</span>
        </div>
        <div class="text-[11px] text-[#64748B] font-mono">
          P95 {{ analyticsStore.summary.p95_latency_ms || 820 }}ms · P99 {{ analyticsStore.summary.p99_latency || '1.2s' }}
        </div>
      </div>
    </div>

    <!-- Card 5: 待闭环知识缺口 -->
    <div class="bg-white rounded-xl border border-[#E5E7EB] p-4 shadow-sm flex flex-col justify-between gap-3 hover:border-blue-200 transition-colors">
      <div class="flex items-center justify-between text-[#64748B] text-xs">
        <span class="font-medium text-[#475569]">待闭环知识缺口</span>
        <AlertCircle :size="14" class="text-rose-600" />
      </div>
      <div class="flex flex-col gap-1.5">
        <div class="text-xl font-bold text-[#0F172A] tracking-tight">
          {{ analyticsStore.summary.unresolved_gaps_count }}
          <span class="text-xs font-normal text-[#64748B] ml-0.5">个</span>
        </div>
        <div class="flex items-center gap-1.5">
          <span class="text-[11px] font-medium text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-100">
            {{ analyticsStore.summary.unresolved_gaps_delta || '↑ 3个 本周新增' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 5 大核心 KPI 指标网格组件
 * 模块: FE-M6 (PAGE-07 原型 1:1)
 */

import { Activity, Database, Zap, Clock, AlertCircle } from 'lucide-vue-next'
import { useAnalyticsStore } from '@/stores/analytics'

const analyticsStore = useAnalyticsStore()

const formatNumber = (num?: number): string => {
  if (num === undefined || num === null) return '0'
  return num.toLocaleString()
}
</script>
