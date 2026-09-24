<template>
  <!-- FE-M6: Token 消耗与峰值 QPS ECharts 趋势图 (PAGE-07 原型 1:1) -->
  <div class="bg-white rounded-xl border border-[#E5E7EB] p-4 shadow-sm flex flex-col justify-between">
    <!-- Header -->
    <div class="flex items-center justify-between pb-3 border-b border-[#F1F5F9]">
      <div class="flex items-center gap-2">
        <h3 class="text-xs font-semibold text-[#0F172A]">Token 消耗与峰值 QPS</h3>
        <span class="text-[10px] text-slate-400 font-normal">时段算力监控</span>
      </div>
      <div class="flex items-center gap-3 text-[11px] text-[#64748B]">
        <div class="flex items-center gap-1.5">
          <span class="w-2.5 h-2.5 rounded-sm bg-[#0071E3]"></span>
          <span>Prompt</span>
        </div>
        <div class="flex items-center gap-1.5">
          <span class="w-2.5 h-2.5 rounded-sm bg-[#60A5FA]"></span>
          <span>Comp</span>
        </div>
        <div class="flex items-center gap-1.5">
          <span class="w-2 h-2 rounded-full bg-[#F59E0B]"></span>
          <span>QPS</span>
        </div>
      </div>
    </div>

    <!-- Chart Container -->
    <div ref="chartRef" class="w-full h-56 mt-2"></div>
  </div>
</template>

<script setup lang="ts">
/**
 * Token 消耗与 QPS 走势图组件
 * 模块: FE-M6 (PAGE-07 原型 1:1)
 */

import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import { useAnalyticsStore } from '@/stores/analytics'

const analyticsStore = useAnalyticsStore()
const chartRef = ref<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts | null = null

const initChart = () => {
  if (!chartRef.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const defaultEmptyTrends = [
    { time: '00:00', prompt_tokens: 0, completion_tokens: 0, qps: 0 },
    { time: '04:00', prompt_tokens: 0, completion_tokens: 0, qps: 0 },
    { time: '08:00', prompt_tokens: 0, completion_tokens: 0, qps: 0 },
    { time: '12:00', prompt_tokens: 0, completion_tokens: 0, qps: 0 },
    { time: '16:00', prompt_tokens: 0, completion_tokens: 0, qps: 0 },
    { time: '20:00', prompt_tokens: 0, completion_tokens: 0, qps: 0 },
    { time: '24:00', prompt_tokens: 0, completion_tokens: 0, qps: 0 }
  ]

  const trends: any[] = analyticsStore.tokenTrends.length > 0 ? analyticsStore.tokenTrends : defaultEmptyTrends

  const xData = trends.map((t: any) => t.time || (t.date ? t.date.substring(5) : '00:00'))
  const promptData = trends.map((t: any) => Math.round((t.prompt_tokens || 0) / 1000))
  const compData = trends.map((t: any) => Math.round((t.completion_tokens || 0) / 1000))
  const qpsData = trends.map((t: any) => t.qps ?? (t.pv ? Math.round(t.pv / 60) : 0))

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#FFFFFF',
      borderColor: '#E2E8F0',
      borderWidth: 1,
      textStyle: {
        color: '#0F172A',
        fontSize: 11
      },
      formatter: (params: any) => {
        if (!Array.isArray(params)) return ''
        let res = `<div class="font-semibold text-xs mb-1">${params[0].axisValue}</div>`
        params.forEach((item: any) => {
          const unit = item.seriesName === '峰值 QPS' ? '次/秒' : 'k Tokens'
          res += `<div class="flex items-center justify-between gap-4 text-[11px] leading-5">
            <span style="color:${item.color}">${item.seriesName}:</span>
            <span class="font-mono font-medium">${item.value} ${unit}</span>
          </div>`
        })
        return res
      }
    },
    grid: {
      top: 25,
      left: 35,
      right: 35,
      bottom: 25
    },
    xAxis: {
      type: 'category',
      data: xData,
      axisLine: { lineStyle: { color: '#E2E8F0' } },
      axisTick: { show: false },
      axisLabel: { color: '#64748B', fontSize: 10 }
    },
    yAxis: [
      {
        type: 'value',
        name: '(k)',
        nameTextStyle: { color: '#94A3B8', fontSize: 10 },
        splitLine: { lineStyle: { color: '#F1F5F9', type: 'dashed' } },
        axisLabel: { color: '#64748B', fontSize: 10 }
      },
      {
        type: 'value',
        name: 'QPS',
        nameTextStyle: { color: '#94A3B8', fontSize: 10 },
        splitLine: { show: false },
        axisLabel: { color: '#64748B', fontSize: 10 }
      }
    ],
    series: [
      {
        name: 'Prompt Token',
        type: 'bar',
        stack: 'tokens',
        barWidth: 18,
        data: promptData,
        itemStyle: {
          color: '#0071E3',
          borderRadius: [0, 0, 0, 0]
        }
      },
      {
        name: 'Comp Token',
        type: 'bar',
        stack: 'tokens',
        barWidth: 18,
        data: compData,
        itemStyle: {
          color: '#93C5FD',
          borderRadius: [3, 3, 0, 0]
        }
      },
      {
        name: '峰值 QPS',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        data: qpsData,
        showSymbol: false,
        lineStyle: {
          color: '#F59E0B',
          width: 2.5
        },
        itemStyle: {
          color: '#F59E0B'
        }
      }
    ]
  }

  chartInstance.setOption(option)
}

const handleResize = () => {
  chartInstance?.resize()
}

watch(
  () => analyticsStore.tokenTrends,
  () => {
    initChart()
  },
  { deep: true }
)

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  chartInstance = null
})
</script>
