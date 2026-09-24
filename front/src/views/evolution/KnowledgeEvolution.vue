<template>
  <!-- PAGE-06: 知识自进化与沉淀工作台视图 (1:1 像素级对齐原型图) -->
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
        <span class="font-semibold text-[#0F172A]">知识自进化运营</span>
      </div>

      <div class="flex items-center gap-2.5">
        <router-link
          to="/chat"
          class="px-3 py-1.5 bg-white hover:bg-slate-50 text-[#0071E3] border border-[#BFDBFE] rounded-lg text-xs font-medium inline-flex items-center gap-1.5 transition-colors shadow-2xs"
        >
          <ExternalLink :size="13" />
          <span>返回问答工作台</span>
        </router-link>
        <button
          type="button"
          class="w-8 h-8 rounded-lg bg-white border border-[#E5E7EB] hover:bg-slate-50 flex items-center justify-center text-[#64748B] transition-colors"
          title="系统消息通知"
        >
          <Bell :size="15" />
        </button>
      </div>
    </div>

    <!-- 4 Metrics Metric Cards Grid (Matching Prototype) -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- Card 1: 未闭环知识缺口 -->
      <div class="bg-white rounded-xl border border-[#E5E7EB] p-4 shadow-sm flex flex-col justify-between gap-3">
        <div class="flex items-center justify-between text-[#64748B] text-xs">
          <span class="font-medium text-[#475569]">未闭环知识缺口</span>
          <HelpCircle :size="14" class="text-[#94A3B8]" />
        </div>
        <div class="flex items-baseline justify-between">
          <div class="text-2xl font-bold text-[#0F172A] tracking-tight">
            {{ evolutionStore.metrics.unresolved_gaps_count }}
            <span class="text-xs font-normal text-[#64748B] ml-0.5">个</span>
          </div>
          <span class="text-[11px] font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-100">
            {{ evolutionStore.metrics.unresolved_gaps_delta }}
          </span>
        </div>
      </div>

      <!-- Card 2: 待审核 FAQ 候选 -->
      <div class="bg-white rounded-xl border border-[#E5E7EB] p-4 shadow-sm flex flex-col justify-between gap-3">
        <div class="flex items-center justify-between text-[#64748B] text-xs">
          <span class="font-medium text-[#475569]">待审核 FAQ 候选</span>
          <Sparkles :size="14" class="text-[#0071E3]" />
        </div>
        <div class="flex items-baseline justify-between">
          <div class="text-2xl font-bold text-[#0F172A] tracking-tight">
            {{ evolutionStore.metrics.pending_candidates_count }}
            <span class="text-xs font-normal text-[#64748B] ml-0.5">条</span>
          </div>
          <span class="text-[11px] font-medium text-[#0071E3] bg-blue-50 px-2 py-0.5 rounded-full border border-blue-100">
            聚类置信度 &gt; 92%
          </span>
        </div>
      </div>

      <!-- Card 3: 自动聚类准确率 -->
      <div class="bg-white rounded-xl border border-[#E5E7EB] p-4 shadow-sm flex flex-col justify-between gap-3">
        <div class="flex items-center justify-between text-[#64748B] text-xs">
          <span class="font-medium text-[#475569]">自动聚类准确率</span>
          <Target :size="14" class="text-indigo-500" />
        </div>
        <div class="flex items-baseline justify-between">
          <div class="text-2xl font-bold text-[#0F172A] tracking-tight font-mono">
            {{ evolutionStore.metrics.clustering_accuracy }}
          </div>
          <span class="text-[11px] font-medium text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-full border border-indigo-100">
            基于语义嵌入
          </span>
        </div>
      </div>

      <!-- Card 4: 缺口转建平均周期 -->
      <div class="bg-white rounded-xl border border-[#E5E7EB] p-4 shadow-sm flex flex-col justify-between gap-3">
        <div class="flex items-center justify-between text-[#64748B] text-xs">
          <span class="font-medium text-[#475569]">缺口转建平均周期</span>
          <Clock :size="14" class="text-amber-500" />
        </div>
        <div class="flex items-baseline justify-between">
          <div class="text-2xl font-bold text-[#0F172A] tracking-tight">
            {{ evolutionStore.metrics.avg_resolution_days }}
            <span class="text-xs font-normal text-[#64748B] ml-0.5">天</span>
          </div>
          <span class="text-[11px] font-medium text-[#0071E3] bg-blue-50 px-2 py-0.5 rounded-full border border-blue-100">
            较上月提速 {{ evolutionStore.metrics.resolution_speedup_percent }}%
          </span>
        </div>
      </div>
    </div>

    <!-- Navigation Tabs Bar with Inline Search -->
    <div class="flex flex-wrap items-center justify-between gap-3 border-b border-[#E5E7EB] pb-2">
      <!-- Tabs Group -->
      <div class="flex items-center gap-1.5">
        <!-- Tab 1: 知识缺口清单 -->
        <button
          type="button"
          class="px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all inline-flex items-center gap-1.5"
          :class="
            evolutionStore.activeTab === 'gaps'
              ? 'bg-[#0071E3] text-white shadow-sm'
              : 'text-[#475569] hover:bg-slate-100'
          "
          @click="switchTab('gaps')"
        >
          <span>知识缺口清单</span>
          <span
            class="text-[11px] px-1.5 py-0.2 rounded-full font-mono font-medium"
            :class="evolutionStore.activeTab === 'gaps' ? 'bg-white/20 text-white' : 'bg-slate-200 text-slate-700'"
          >
            {{ evolutionStore.totalKnowledgeGaps }}
          </span>
        </button>

        <!-- Tab 2: FAQ 聚类审核 -->
        <button
          type="button"
          class="px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all inline-flex items-center gap-1.5"
          :class="
            evolutionStore.activeTab === 'candidates'
              ? 'bg-[#0071E3] text-white shadow-sm'
              : 'text-[#475569] hover:bg-slate-100'
          "
          @click="switchTab('candidates')"
        >
          <span>FAQ 聚类审核</span>
          <span
            class="text-[11px] px-1.5 py-0.2 rounded-full font-mono font-medium"
            :class="evolutionStore.activeTab === 'candidates' ? 'bg-white/20 text-white' : 'bg-slate-200 text-slate-700'"
          >
            {{ evolutionStore.totalCandidates }}
          </span>
        </button>

        <!-- Tab 3: 已发布 FAQ 库 -->
        <button
          type="button"
          class="px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all inline-flex items-center gap-1.5"
          :class="
            evolutionStore.activeTab === 'published'
              ? 'bg-[#0071E3] text-white shadow-sm'
              : 'text-[#475569] hover:bg-slate-100'
          "
          @click="switchTab('published')"
        >
          <span>已发布 FAQ 库</span>
          <span
            class="text-[11px] px-1.5 py-0.2 rounded-full font-mono font-medium"
            :class="evolutionStore.activeTab === 'published' ? 'bg-white/20 text-white' : 'bg-slate-200 text-slate-700'"
          >
            {{ evolutionStore.totalPublishedFaqs }}
          </span>
        </button>
      </div>

      <!-- Search Input -->
      <div class="relative w-64">
        <Search :size="13" class="absolute left-3 top-2.5 text-[#94A3B8]" />
        <input
          v-model="evolutionStore.searchKeyword"
          type="text"
          :placeholder="searchPlaceholder"
          class="w-full bg-white border border-[#E5E7EB] rounded-lg pl-8 pr-7 py-1.5 text-xs text-[#0F172A] placeholder-[#94A3B8] focus:outline-none focus:border-[#0071E3] transition-colors shadow-2xs"
          @keyup.enter="handleSearch"
        />
        <button
          v-if="evolutionStore.searchKeyword"
          type="button"
          class="absolute right-2 top-2 text-slate-400 hover:text-slate-600"
          @click="clearSearch"
        >
          <X :size="12" />
        </button>
      </div>
    </div>

    <!-- Active Tab Content Area -->
    <div class="min-h-[460px]">
      <KnowledgeGapTab
        v-if="evolutionStore.activeTab === 'gaps'"
        @toast="showToast"
      />
      <CandidateFaqTab
        v-else-if="evolutionStore.activeTab === 'candidates'"
        @toast="showToast"
      />
      <PublishedFaqTab
        v-else-if="evolutionStore.activeTab === 'published'"
        @toast="showToast"
      />
    </div>

    <!-- Drawer: 润色对比采纳抽屉 -->
    <FaqEditDrawer @toast="showToast" />

    <!-- Drawer: 知识缺口转建工单抽屉 -->
    <GapTaskModal @toast="showToast" />
  </div>
</template>

<script setup lang="ts">
/**
 * 知识自进化工作台视图
 * 原型对应: PAGE-06 (knowledge_evolution.png)
 * 模块: FE-M5
 */

import { ref, computed, onMounted } from 'vue'
import {
  ExternalLink,
  Bell,
  HelpCircle,
  Sparkles,
  Target,
  Clock,
  Search,
  X,
  CheckCircle2,
  AlertCircle
} from 'lucide-vue-next'
import { useEvolutionStore } from '@/stores/evolution'

import CandidateFaqTab from '@/components/Evolution/CandidateFaqTab.vue'
import PublishedFaqTab from '@/components/Evolution/PublishedFaqTab.vue'
import KnowledgeGapTab from '@/components/Evolution/KnowledgeGapTab.vue'
import FaqEditDrawer from '@/components/Evolution/FaqEditDrawer.vue'
import GapTaskModal from '@/components/Evolution/GapTaskModal.vue'

const evolutionStore = useEvolutionStore()

const toastMessage = ref('')
const toastType = ref<'success' | 'error'>('success')
let toastTimer: ReturnType<typeof setTimeout> | null = null

const showToast = (msg: string, type: 'success' | 'error' = 'success') => {
  toastMessage.value = msg
  toastType.value = type
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    toastMessage.value = ''
  }, 3500)
}

const searchPlaceholder = computed(() => {
  switch (evolutionStore.activeTab) {
    case 'gaps':
      return '搜索未命中提问词...'
    case 'candidates':
      return '搜索候选标准提问或回答...'
    case 'published':
      return '搜索已发布标准 FAQ 问答...'
    default:
      return '搜索...'
  }
})

const switchTab = (tab: 'gaps' | 'candidates' | 'published') => {
  evolutionStore.activeTab = tab
  if (tab === 'gaps') {
    evolutionStore.fetchKnowledgeGaps(1)
  } else if (tab === 'candidates') {
    evolutionStore.fetchCandidates(1)
  } else if (tab === 'published') {
    evolutionStore.fetchPublishedFaqs(1)
  }
}

const handleSearch = () => {
  if (evolutionStore.activeTab === 'gaps') {
    evolutionStore.fetchKnowledgeGaps(1)
  } else if (evolutionStore.activeTab === 'candidates') {
    evolutionStore.fetchCandidates(1)
  } else if (evolutionStore.activeTab === 'published') {
    evolutionStore.fetchPublishedFaqs(1)
  }
}

const clearSearch = () => {
  evolutionStore.searchKeyword = ''
  handleSearch()
}

onMounted(async () => {
  await Promise.all([
    evolutionStore.fetchMetrics(),
    evolutionStore.fetchCandidates(1),
    evolutionStore.fetchPublishedFaqs(1),
    evolutionStore.fetchKnowledgeGaps(1)
  ])
})
</script>
