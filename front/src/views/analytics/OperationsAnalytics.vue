<template>
  <!-- PAGE-07: 运营大盘与全链路安全审计视图 (1:1 像素级对齐原型图) -->
  <div class="space-y-5">
    <!-- Top Global Toast Notification -->
    <div
      v-if="toastMessage"
      class="fixed top-5 right-5 z-50 flex items-center gap-2 px-4 py-2.5 rounded-xl shadow-lg border text-xs font-medium transition-all duration-300 animate-in fade-in slide-in-from-top-4"
      :class="toastType === 'success' ? 'bg-emerald-50 text-emerald-800 border-emerald-200' : 'bg-rose-50 text-rose-800 border-rose-200'"
    >
      <CheckCircle2 v-if="toastType === 'success'" :size="15" class="text-emerald-600 shrink-0" />
      <AlertCircle v-else :size="15" class="text-rose-600 shrink-0" />
      <span>{{ toastMessage }}</span>
    </div>

    <!-- Top Action Breadcrumb Header -->
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div class="flex items-center gap-2 text-xs">
        <span class="text-[#64748B]">管理控制台</span>
        <span class="text-[#CBD5E1]">/</span>
        <span class="font-semibold text-[#0F172A]">运营与安全大盘</span>
      </div>

      <div class="flex items-center gap-2.5">
        <button
          type="button"
          class="px-3 py-1.5 bg-white hover:bg-slate-50 text-[#475569] border border-[#E5E7EB] rounded-lg text-xs font-medium inline-flex items-center gap-1.5 transition-colors shadow-2xs"
          @click="refreshData"
        >
          <RefreshCw :size="12" :class="{ 'animate-spin': isRefreshing }" />
          <span>刷新大盘</span>
        </button>
        <router-link
          to="/chat"
          class="px-3 py-1.5 bg-white hover:bg-slate-50 text-[#0071E3] border border-[#BFDBFE] rounded-lg text-xs font-medium inline-flex items-center gap-1.5 transition-colors shadow-2xs"
        >
          <ExternalLink :size="13" />
          <span>返回问答工作台</span>
        </router-link>
      </div>
    </div>

    <!-- Section 1: 5 大 KPI 指标卡片网格 -->
    <KpiCardGrid />

    <!-- Section 2: 3 列分析大盘 (Token趋势、耗时分布、TOP5榜单) -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <!-- Col 1: Token 消耗与峰值 QPS -->
      <TrendChart />

      <!-- Col 2: 端到端响应耗时分布 -->
      <LatencyBarChart />

      <!-- Col 3: 高频提问与引用 TOP 5 -->
      <TopRankings />
    </div>

    <!-- Section 3: 全链路安全审计流水表格 -->
    <AuditLogTable @toast="showToast" />

    <!-- Drawer: 拦截证据链与 Trace 溯源下钻抽屉 -->
    <AuditDetailDrawer @toast="showToast" />
  </div>
</template>

<script setup lang="ts">
/**
 * 运营大盘与全链路安全审计视图
 * 原型对应: PAGE-07 (operations_analytics.pen)
 * 模块: FE-M6
 */

import { ref, onMounted } from 'vue'
import { CheckCircle2, AlertCircle, RefreshCw, ExternalLink } from 'lucide-vue-next'
import { useAnalyticsStore } from '@/stores/analytics'
import KpiCardGrid from '@/components/Analytics/KpiCardGrid.vue'
import TrendChart from '@/components/Analytics/TrendChart.vue'
import LatencyBarChart from '@/components/Analytics/LatencyBarChart.vue'
import TopRankings from '@/components/Analytics/TopRankings.vue'
import AuditLogTable from '@/components/Analytics/AuditLogTable.vue'
import AuditDetailDrawer from '@/components/Analytics/AuditDetailDrawer.vue'

const analyticsStore = useAnalyticsStore()

const isRefreshing = ref(false)
const toastMessage = ref('')
const toastType = ref<'success' | 'error'>('success')
let toastTimer: any = null

const showToast = (msg: string, type: 'success' | 'error' = 'success') => {
  toastMessage.value = msg
  toastType.value = type
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    toastMessage.value = ''
  }, 3200)
}

const refreshData = async () => {
  isRefreshing.value = true
  try {
    await analyticsStore.loadAll()
    showToast('运营与安全大盘数据已更新至最新状态', 'success')
  } catch {
    showToast('刷新大盘数据失败', 'error')
  } finally {
    isRefreshing.value = false
  }
}

onMounted(() => {
  analyticsStore.loadAll()
})
</script>
