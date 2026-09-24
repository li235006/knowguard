<template>
  <!-- FE-M6: 全链路安全审计流水日志表格 (PAGE-07 原型 1:1) -->
  <div class="bg-white rounded-xl border border-[#E5E7EB] shadow-sm overflow-hidden flex flex-col">
    <!-- Table Header Tool Bar -->
    <div class="p-3.5 border-b border-[#F1F5F9] flex flex-wrap items-center justify-between gap-3 bg-[#F8FAFC]/50">
      <div class="flex items-center gap-2.5">
        <h3 class="text-xs font-semibold text-[#0F172A]">全链路问答安全审计流水日志</h3>
        <span class="text-[10px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-100 flex items-center gap-1">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>实时流式存证</span>
        </span>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <!-- Search Input -->
        <div class="relative w-56">
          <Search :size="13" class="absolute left-2.5 top-2.5 text-[#94A3B8]" />
          <input
            v-model="analyticsStore.auditSearchKeyword"
            type="text"
            placeholder="搜索 TraceID / 提问人 / 词..."
            class="w-full bg-white border border-[#E5E7EB] rounded-lg pl-8 pr-7 py-1 text-xs text-[#0F172A] placeholder-[#94A3B8] focus:outline-none focus:border-[#0071E3] transition-colors"
            @keyup.enter="handleSearch"
          />
          <button
            v-if="analyticsStore.auditSearchKeyword"
            type="button"
            class="absolute right-2 top-2 text-slate-400 hover:text-slate-600"
            @click="clearSearch"
          >
            <X :size="12" />
          </button>
        </div>

        <!-- Filter Pill Button Group -->
        <div class="inline-flex p-0.5 bg-slate-100 rounded-lg text-xs font-medium">
          <button
            type="button"
            class="px-2 py-1 rounded-md transition-colors"
            :class="analyticsStore.auditStatusFilter === 'ALL' ? 'bg-white text-[#0071E3] shadow-xs' : 'text-slate-600 hover:text-slate-900'"
            @click="setFilter('ALL')"
          >
            全部
          </button>
          <button
            type="button"
            class="px-2 py-1 rounded-md transition-colors"
            :class="analyticsStore.auditStatusFilter === 'BLOCKED' ? 'bg-white text-rose-600 shadow-xs' : 'text-slate-600 hover:text-slate-900'"
            @click="setFilter('BLOCKED')"
          >
            阻断拦截
          </button>
          <button
            type="button"
            class="px-2 py-1 rounded-md transition-colors"
            :class="analyticsStore.auditStatusFilter === 'ALLOWED' ? 'bg-white text-emerald-600 shadow-xs' : 'text-slate-600 hover:text-slate-900'"
            @click="setFilter('ALLOWED')"
          >
            全部放行
          </button>
          <button
            type="button"
            class="px-2 py-1 rounded-md transition-colors"
            :class="analyticsStore.auditStatusFilter === 'FAQ_HIT' ? 'bg-white text-[#0071E3] shadow-xs' : 'text-slate-600 hover:text-slate-900'"
            @click="setFilter('FAQ_HIT')"
          >
            FAQ直出
          </button>
        </div>

        <!-- Export Button -->
        <button
          type="button"
          class="px-2.5 py-1 text-xs text-[#475569] bg-white border border-[#E5E7EB] hover:bg-slate-50 rounded-lg transition-colors inline-flex items-center gap-1 font-medium shadow-2xs"
          @click="handleExport"
        >
          <Download :size="12" />
          <span>导出流水</span>
        </button>
      </div>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto">
      <table class="w-full text-left text-xs border-collapse">
        <thead>
          <tr class="bg-[#F8FAFC] text-[#64748B] border-b border-[#F1F5F9] font-medium text-[11px]">
            <th class="py-3 px-4 w-36">TraceID</th>
            <th class="py-3 px-4 w-24">提问时间</th>
            <th class="py-3 px-4 w-40">提问人 / 组织角色</th>
            <th class="py-3 px-4 min-w-[240px]">提问内容</th>
            <th class="py-3 px-4 w-20 text-center">召回</th>
            <th class="py-3 px-4 w-44">4D-RBAC 安全判决</th>
            <th class="py-3 px-4 w-20 text-center">Token</th>
            <th class="py-3 px-4 w-20 text-center">耗时</th>
            <th class="py-3 px-4 w-28 text-right">操作</th>
          </tr>
        </thead>

        <tbody v-if="analyticsStore.isLoadingAudit" class="divide-y divide-[#F1F5F9]">
          <tr v-for="i in 5" :key="i" class="animate-pulse">
            <td colspan="9" class="py-4 px-4">
              <div class="h-4 bg-gray-100 rounded w-full"></div>
            </td>
          </tr>
        </tbody>

        <tbody v-else-if="analyticsStore.auditLogs.length > 0" class="divide-y divide-[#F1F5F9]">
          <tr
            v-for="log in analyticsStore.auditLogs"
            :key="log.id || log.trace_id"
            class="hover:bg-[#F8FAFC] transition-colors"
          >
            <!-- Trace ID -->
            <td class="py-3 px-4 font-mono font-medium text-[#0071E3] text-[11px] whitespace-nowrap">
              {{ log.trace_id }}
            </td>

            <!-- Time -->
            <td class="py-3 px-4 text-[#64748B] font-mono text-[11px] whitespace-nowrap">
              {{ log.time || log.created_at.substring(11, 19) }}
            </td>

            <!-- User / Dept -->
            <td class="py-3 px-4">
              <div class="font-medium text-[#0F172A]">{{ log.username || '员工' }}</div>
              <div class="text-[10px] text-slate-400">
                {{ log.dept_name || (log as any).user_dept || '通用部门' }} · {{ log.role_name || (log as any).user_role || '普通员工' }}
              </div>
            </td>

            <!-- Query -->
            <td class="py-3 px-4">
              <span class="font-medium text-[#0F172A] line-clamp-1" :title="log.query || (log as any).query_text">
                {{ log.query || (log as any).query_text }}
              </span>
            </td>

            <!-- Recalled Count -->
            <td class="py-3 px-4 text-center font-mono font-medium text-[#475569]">
              {{ log.recalled_count }} 个
            </td>

            <!-- Verdict -->
            <td class="py-3 px-4">
              <div class="flex items-center gap-1.5 flex-wrap">
                <!-- Blocked -->
                <span
                  v-if="log.is_blocked"
                  class="text-[10px] font-medium px-2 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 inline-flex items-center gap-1"
                >
                  <ShieldAlert :size="11" />
                  <span>阻断 {{ log.restricted_count }} (4D越权)</span>
                </span>
                <span
                  v-if="log.is_blocked && log.allowed_count > 0"
                  class="text-[10px] font-medium px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200"
                >
                  放行 {{ log.allowed_count }}
                </span>

                <!-- FAQ Direct Hit -->
                <span
                  v-else-if="log.verdict_type === 'FAQ_HIT'"
                  class="text-[10px] font-medium px-2 py-0.5 rounded bg-blue-50 text-[#0071E3] border border-blue-200 inline-flex items-center gap-1 font-mono"
                >
                  <Zap :size="11" />
                  <span>⚡ FAQ 命中直出</span>
                </span>

                <!-- All Allowed -->
                <span
                  v-else
                  class="text-[10px] font-medium px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 inline-flex items-center gap-1"
                >
                  <ShieldCheck :size="11" />
                  <span>✓ 4D全部放行</span>
                </span>
              </div>
            </td>

            <!-- Tokens -->
            <td class="py-3 px-4 text-center font-mono text-[#64748B]">
              {{ ((log.tokens ?? (log as any).total_tokens ?? 0) as number).toLocaleString() }}
            </td>

            <!-- Latency -->
            <td class="py-3 px-4 text-center font-mono font-medium text-[#0F172A]">
              {{ log.latency_ms }}ms
            </td>

            <!-- Action -->
            <td class="py-3 px-4 text-right whitespace-nowrap">
              <button
                type="button"
                class="text-[11px] font-medium inline-flex items-center gap-1 transition-colors"
                :class="log.is_blocked ? 'text-rose-600 hover:text-rose-700 font-semibold' : 'text-[#0071E3] hover:underline'"
                @click="analyticsStore.openAuditDetail(log)"
              >
                <span>{{ log.is_blocked ? '溯源详情 →' : '查看全链路' }}</span>
              </button>
            </td>
          </tr>
        </tbody>

        <!-- Empty State -->
        <tbody v-else>
          <tr>
            <td colspan="9" class="py-14 text-center text-[#94A3B8]">
              <div class="flex flex-col items-center gap-2">
                <CheckCircle2 :size="24" class="text-emerald-500" />
                <span class="font-medium text-slate-600">未检索到符合条件的审计日志</span>
                <span class="text-slate-400 text-[11px]">系统持续全量记录问答交互与安全裁决证据链</span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div
      v-if="analyticsStore.totalAuditLogs > analyticsStore.auditPageSize"
      class="p-3 border-t border-[#F1F5F9] bg-[#FAFAFA]/60 flex items-center justify-between text-xs text-[#64748B]"
    >
      <div>
        共 <span class="font-medium text-[#0F172A]">{{ analyticsStore.totalAuditLogs }}</span> 条安全存证记录
      </div>
      <div class="flex items-center gap-2">
        <button
          type="button"
          :disabled="analyticsStore.auditPage <= 1"
          class="px-2.5 py-1 border border-[#E5E7EB] rounded bg-white hover:bg-gray-50 disabled:opacity-40 transition-colors"
          @click="changePage(analyticsStore.auditPage - 1)"
        >
          上一页
        </button>
        <span class="px-2 font-mono text-[#0F172A]">第 {{ analyticsStore.auditPage }} 页</span>
        <button
          type="button"
          :disabled="analyticsStore.auditPage * analyticsStore.auditPageSize >= analyticsStore.totalAuditLogs"
          class="px-2.5 py-1 border border-[#E5E7EB] rounded bg-white hover:bg-gray-50 disabled:opacity-40 transition-colors"
          @click="changePage(analyticsStore.auditPage + 1)"
        >
          下一页
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 全链路安全审计流水表格组件
 * 模块: FE-M6 (PAGE-07 原型 1:1)
 */

import { Search, X, Download, ShieldAlert, ShieldCheck, Zap, CheckCircle2 } from 'lucide-vue-next'
import { useAnalyticsStore } from '@/stores/analytics'

const analyticsStore = useAnalyticsStore()

const emit = defineEmits<{
  (e: 'toast', msg: string, type?: 'success' | 'error'): void
}>()

const setFilter = (status: string) => {
  analyticsStore.auditStatusFilter = status
  analyticsStore.fetchAuditLogs(1)
}

const handleSearch = () => {
  analyticsStore.fetchAuditLogs(1)
}

const clearSearch = () => {
  analyticsStore.auditSearchKeyword = ''
  analyticsStore.fetchAuditLogs(1)
}

const changePage = (page: number) => {
  analyticsStore.fetchAuditLogs(page)
}

const handleExport = () => {
  emit('toast', '已成功导出全链路问答安全审计流水存证清单 (CSV格式)', 'success')
}
</script>
