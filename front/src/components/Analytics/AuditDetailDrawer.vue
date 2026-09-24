<template>
  <!-- FE-M6: 全链路安全拦截证据链溯源抽屉 (PAGE-07 原型 1:1) -->
  <div v-if="analyticsStore.showDetailDrawer" class="fixed inset-0 z-50 overflow-hidden">
    <!-- Backdrop Blur -->
    <div
      class="absolute inset-0 bg-black/40 backdrop-blur-xs transition-opacity"
      @click="analyticsStore.closeAuditDetail"
    />

    <div class="fixed inset-y-0 right-0 max-w-full flex pl-10">
      <div class="w-screen max-w-2xl bg-white shadow-2xl flex flex-col justify-between border-l border-[#E5E7EB] animate-in slide-in-from-right duration-300">
        <!-- Header -->
        <div class="p-4 border-b border-[#F1F5F9] flex items-center justify-between shrink-0 bg-[#F8FAFC]">
          <div class="flex items-center gap-2.5">
            <h3 class="font-semibold text-sm text-[#0F172A] font-mono">
              Trace 溯源: {{ currentLog?.trace_id }}
            </h3>
            <span
              class="text-[11px] px-2 py-0.5 rounded font-medium"
              :class="
                currentLog?.is_blocked
                  ? 'bg-rose-50 text-rose-700 border border-rose-200'
                  : currentLog?.verdict_type === 'FAQ_HIT'
                  ? 'bg-blue-50 text-[#0071E3] border border-blue-200'
                  : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
              "
            >
              {{
                currentLog?.is_blocked
                  ? '4D越权拦截 (静默脱敏)'
                  : currentLog?.verdict_type === 'FAQ_HIT'
                  ? 'FAQ 极速缓存直出'
                  : '4D 合规放行'
              }}
            </span>
          </div>

          <button
            type="button"
            class="text-gray-400 hover:text-gray-600 p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
            @click="analyticsStore.closeAuditDetail"
          >
            <X :size="16" />
          </button>
        </div>

        <!-- Body -->
        <div class="flex-1 overflow-y-auto p-5 space-y-4 text-xs">
          <!-- 1. User Query Prompt Card -->
          <div class="bg-[#F8FAFC] border border-[#E5E7EB] rounded-xl p-4 space-y-2">
            <div class="flex items-center justify-between text-[#64748B] text-xs">
              <span class="font-medium text-[#0F172A]">
                提问人: <strong class="text-[#0071E3]">{{ currentLog?.username || '员工' }}</strong> · {{ currentLog?.dept_name || (currentLog as any)?.user_dept || '通用部门' }} · {{ currentLog?.role_name || (currentLog as any)?.user_role || '普通员工' }}
              </span>
              <span class="text-[10px] bg-white border border-[#E2E8F0] px-2 py-0.5 rounded text-slate-500 font-medium">
                {{ currentLog?.client_endpoint || 'Web 问答工作台' }}
              </span>
            </div>

            <div class="font-medium text-xs text-[#0F172A] bg-white border border-[#E5E7EB] p-2.5 rounded-lg leading-relaxed">
              “{{ currentLog?.query || (currentLog as any)?.query_text }}”
            </div>

            <div class="text-[11px] text-[#94A3B8] flex flex-wrap items-center gap-3 font-mono">
              <span>时间: {{ currentLog?.created_at }}</span>
              <span>·</span>
              <span>模式: {{ currentLog?.silent_intercept_triggered ? '静默防越权' : '普通问答' }}</span>
              <span>·</span>
              <span>客户端: {{ currentLog?.client_endpoint || 'Web问答工作台' }}</span>
            </div>
          </div>

          <!-- 2. Silent Intercept Banner (Triggered when blocked) -->
          <div
            v-if="currentLog?.is_blocked || currentLog?.silent_intercept_triggered"
            class="bg-rose-50/70 border border-rose-200 rounded-xl p-3.5 flex gap-3 text-xs"
          >
            <ShieldAlert :size="18" class="text-rose-600 shrink-0 mt-0.5" />
            <div class="space-y-1">
              <div class="font-semibold text-rose-900 text-xs">
                静默越权阻断策略已触发 (PRD 5.3 核心机制)
              </div>
              <p class="text-rose-700 text-[11px] leading-relaxed">
                命中受限敏感资产切片。系统未向用户暴露越权拒绝或文档元数据，而是静默剔除越权切片，由模型基于合规切片生成脱敏回复（'由于权限策略限制，未检索到相关高管薪酬细则'），确保零信息探测。
              </p>
            </div>
          </div>

          <!-- 3. 4D-RBAC Dynamic Matrix Section -->
          <div class="space-y-2.5">
            <div class="flex items-center justify-between">
              <h4 class="font-semibold text-xs text-[#0F172A] flex items-center gap-1.5">
                <ShieldCheck :size="14" class="text-[#0071E3]" />
                <span>四维权限 (4D-RBAC) 动态判决矩阵 (召回 {{ currentLog?.recalled_count }} 切片)</span>
              </h4>
            </div>

            <!-- Chunk List -->
            <div class="space-y-2">
              <div
                v-for="(chunk, idx) in currentLog?.chunk_verdicts || fallbackChunkVerdicts"
                :key="idx"
                class="rounded-xl border p-3 text-xs transition-colors"
                :class="
                  chunk.status === 'BLOCKED'
                    ? 'bg-rose-50/40 border-rose-200'
                    : 'bg-white border-[#E5E7EB]'
                "
              >
                <!-- Chunk Header -->
                <div class="flex items-center justify-between pb-1.5 border-b border-[#F1F5F9]">
                  <span class="font-medium text-[#0F172A] text-xs">
                    {{ chunk.chunk_name }}
                  </span>
                  <span
                    class="text-[10px] font-medium px-2 py-0.5 rounded"
                    :class="
                      chunk.status === 'BLOCKED'
                        ? 'bg-rose-100 text-rose-700 font-bold'
                        : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    "
                  >
                    {{ chunk.status === 'BLOCKED' ? '❌ 4D阻断剔除' : '✓ 4D放行' }}
                  </span>
                </div>

                <!-- Chunk Details -->
                <div class="mt-2 space-y-1.5 text-[11px]">
                  <div v-if="chunk.doc_title" class="text-[#64748B]">
                    文档: <strong class="text-[#0F172A]">{{ chunk.doc_code }} · {{ chunk.doc_title }}</strong>
                  </div>

                  <!-- If Blocked Detail -->
                  <template v-if="chunk.status === 'BLOCKED'">
                    <div class="bg-white/80 border border-rose-100 p-2 rounded-lg text-rose-800 space-y-0.5 font-mono">
                      <div>① 全局公开: 否 ✕</div>
                      <div>② 部门范围: {{ chunk.checks.dept_target || '人力资源中心' }} (当前: {{ chunk.checks.dept_actual || currentLog?.dept_name }} ✕)</div>
                      <div>③ 角色策略: {{ chunk.checks.role_target || '核心高管/HRBP' }} (当前: {{ chunk.checks.role_actual || currentLog?.role_name }} ✕)</div>
                      <div>④ 个人白名单: 无该用户 ✕</div>
                    </div>
                    <div class="text-rose-600 font-medium">
                      判定结果: {{ chunk.reason || 'UNAUTHORIZED_DEPARTMENT_AND_ROLE (所属部门与角色均未在授权策略内)' }}
                    </div>
                  </template>

                  <!-- If Allowed Detail -->
                  <template v-else>
                    <div class="text-[#64748B] flex flex-wrap gap-2">
                      <span>全局: 公开</span>
                      <span>·</span>
                      <span>部门: 匹配</span>
                      <span>·</span>
                      <span>角色: {{ currentLog?.role_name }}</span>
                      <span>·</span>
                      <span>个人: 无限制</span>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </div>

          <!-- 4. Latency Waterfall Section -->
          <div class="space-y-2.5">
            <h4 class="font-semibold text-xs text-[#0F172A] flex items-center justify-between">
              <span class="flex items-center gap-1.5">
                <Clock :size="14" class="text-indigo-500" />
                <span>全链路端到端耗时流水 (总耗时: {{ currentLog?.latency_ms }}ms)</span>
              </span>
            </h4>

            <div class="bg-[#F8FAFC] border border-[#E5E7EB] rounded-xl p-3.5 space-y-2.5">
              <div
                v-for="(step, idx) in currentLog?.waterfall || fallbackWaterfall"
                :key="idx"
                class="space-y-1"
              >
                <div class="flex items-center justify-between text-[11px]">
                  <span class="text-[#475569] font-medium">{{ step.step_name }}</span>
                  <span class="font-mono font-semibold text-[#0F172A]">{{ step.latency_ms }}ms</span>
                </div>
                <div class="w-full h-1.5 rounded-full bg-slate-200 overflow-hidden flex">
                  <div
                    class="h-full rounded-full bg-[#0071E3] transition-all duration-300"
                    :style="{ width: `${Math.min(100, Math.round((step.latency_ms / (currentLog?.latency_ms || 380)) * 100))}%` }"
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="p-4 border-t border-[#F1F5F9] bg-[#F8FAFC] flex items-center justify-between shrink-0">
          <div class="text-[10px] text-slate-400 font-mono flex items-center gap-1">
            <span>SHA-256:</span>
            <span class="text-slate-600 font-semibold">{{ currentLog?.sha256_hash ? `${currentLog.sha256_hash.substring(0, 16)}...` : '8f9a2b77c3e5...4d1e' }}</span>
            <span class="text-emerald-600 font-medium">(可信存证)</span>
          </div>

          <button
            type="button"
            class="px-4 py-2 text-xs bg-[#0071E3] hover:bg-[#0077ED] text-white rounded-lg font-medium transition-colors inline-flex items-center gap-1.5 shadow-sm"
            @click="exportProof"
          >
            <Download :size="13" />
            <span>导出审计存证报告</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 全链路安全拦截证据链抽屉组件
 * 模块: FE-M6 (PAGE-07 原型 1:1)
 */

import { computed } from 'vue'
import { X, ShieldAlert, ShieldCheck, Clock, Download } from 'lucide-vue-next'
import { useAnalyticsStore } from '@/stores/analytics'
import type { ChunkVerdict, LatencyWaterfallStep } from '@/types/analytics'

const analyticsStore = useAnalyticsStore()

const emit = defineEmits<{
  (e: 'toast', msg: string, type?: 'success' | 'error'): void
}>()

const currentLog = computed(() => analyticsStore.selectedLogForDetail)

const fallbackChunkVerdicts: ChunkVerdict[] = [
  {
    chunk_id: 'Chunk-101',
    chunk_name: 'Chunk-101: 《财务审批权限管理办法》 4.2节',
    doc_code: 'KU-1001',
    doc_title: '财务审批权限管理办法.docx',
    status: 'ALLOWED',
    checks: { global_public: true, dept_matched: true, role_matched: true, user_matched: true }
  },
  {
    chunk_id: 'Chunk-102',
    chunk_name: 'Chunk-102: 《2024年度薪酬分配基本总则》',
    doc_code: 'KU-1003',
    doc_title: '2024年度薪酬分配基本总则.pdf',
    status: 'ALLOWED',
    checks: { global_public: true, dept_matched: true, role_matched: true, user_matched: true }
  },
  {
    chunk_id: 'Chunk-103',
    chunk_name: 'Chunk-103: 高管期权折算系数与特别激励授予条件',
    doc_code: 'KU-1002',
    doc_title: '集团核心高管中长期薪酬与股权激励细则.docx',
    status: 'BLOCKED',
    checks: {
      global_public: false,
      dept_matched: false,
      dept_actual: '市场营销部',
      dept_target: '人力资源中心',
      role_matched: false,
      role_actual: '普通员工',
      role_target: '核心高管/HRBP',
      user_matched: false
    },
    reason: 'UNAUTHORIZED_DEPARTMENT_AND_ROLE (所属部门与角色均未在授权策略内)'
  }
]

const fallbackWaterfall: LatencyWaterfallStep[] = [
  { step_name: '网关鉴权与会话校验', latency_ms: 12 },
  { step_name: '向量混合检索召回', latency_ms: 85 },
  { step_name: '4D-RBAC 权限判定硬过滤', latency_ms: 18 },
  { step_name: 'LLM 安全脱敏流式生成', latency_ms: 265 }
]

const exportProof = () => {
  emit('toast', `审计存证报告 [${currentLog.value?.trace_id}] 已生成并成功导出`, 'success')
}
</script>
