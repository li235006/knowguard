/**
 * 知识自进化工作台状态仓库 (Evolution Store)
 * 模块: FE-M5
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import type {
  FaqCandidate,
  FaqItem,
  KnowledgeGap,
  CandidateApprovePayload,
  CandidateRejectPayload,
  FaqCreatePayload,
  FaqUpdatePayload,
  KnowledgeGapConvertPayload,
  EvolutionMetrics
} from '@/types/evolution'
import {
  getFaqCandidatesApi,
  approveCandidateApi,
  rejectCandidateApi,
  getPublishedFaqsApi,
  publishFaqApi,
  updateFaqApi,
  toggleFaqStatusApi,
  toggleFaqCacheApi,
  deleteFaqApi,
  getKnowledgeGapsApi,
  convertKnowledgeGapApi,
  resolveKnowledgeGapApi,
  ignoreKnowledgeGapApi,
  triggerClusterMiningApi,
  getEvolutionMetricsApi
} from '@/api/evolution'

export const useEvolutionStore = defineStore('evolution', () => {
  // 当前激活页签: gaps(知识缺口清单) | candidates(FAQ聚类审核) | published(已发布FAQ库)
  const activeTab = ref<'gaps' | 'candidates' | 'published'>('candidates')

  // 顶层 4 大度量指标
  const metrics = ref<EvolutionMetrics>({
    unresolved_gaps_count: 0,
    unresolved_gaps_delta: '-',
    pending_candidates_count: 0,
    clustering_accuracy: '0.0%',
    avg_resolution_days: 0,
    resolution_speedup_percent: 0
  })

  // 候选 FAQ 列表
  const candidates = ref<FaqCandidate[]>([])
  const totalCandidates = ref<number>(0)
  const candidatesPage = ref<number>(1)
  const candidatesPageSize = ref<number>(10)
  const candidateStatusFilter = ref<string>('PENDING')

  // 已发布 FAQ 列表
  const publishedFaqs = ref<FaqItem[]>([])
  const totalPublishedFaqs = ref<number>(0)
  const faqsPage = ref<number>(1)
  const faqsPageSize = ref<number>(10)
  const selectedCategory = ref<string>('ALL')

  // 知识缺口清单
  const knowledgeGaps = ref<KnowledgeGap[]>([])
  const totalKnowledgeGaps = ref<number>(0)
  const gapsPage = ref<number>(1)
  const gapsPageSize = ref<number>(10)
  const gapStatusFilter = ref<string>('ALL')
  const gapSortBy = ref<string>('hit_count')
  const gapSortOrder = ref<'asc' | 'desc'>('desc')

  // 全局交互与抽屉/弹窗状态
  const searchKeyword = ref<string>('')
  const isLoading = ref<boolean>(false)
  const isMining = ref<boolean>(false)

  const selectedCandidateForEdit = ref<FaqCandidate | null>(null)
  const showEditDrawer = ref<boolean>(false)

  const selectedGapForTicket = ref<KnowledgeGap | null>(null)
  const showGapModal = ref<boolean>(false)

  // 1. 获取核心度量指标
  const fetchMetrics = async () => {
    try {
      const res = await getEvolutionMetricsApi()
      if (res && res.data) {
        metrics.value = res.data
      }
    } catch {
      // 保持当前度量容错
    }
  }

  // 2. 获取候选 FAQ 推荐列表
  const fetchCandidates = async (page: number = 1) => {
    isLoading.value = true
    candidatesPage.value = page
    try {
      const res = await getFaqCandidatesApi({
        page,
        page_size: candidatesPageSize.value,
        status: candidateStatusFilter.value,
        keyword: searchKeyword.value
      })
      if (res && res.data) {
        candidates.value = res.data.items || []
        totalCandidates.value = res.data.total ?? 0
      }
    } finally {
      isLoading.value = false
    }
  }

  // 3. 审核采纳候选 FAQ
  const approveCandidate = async (candidateId: number, payload: CandidateApprovePayload): Promise<FaqItem> => {
    const res = await approveCandidateApi(candidateId, payload)
    if (!res || !res.data) throw new Error(res?.message || '采纳候选 FAQ 失败')
    // 刷新数据
    await Promise.all([fetchCandidates(candidatesPage.value), fetchPublishedFaqs(faqsPage.value), fetchMetrics()])
    return res.data
  }

  // 4. 驳回候选 FAQ
  const rejectCandidate = async (candidateId: number, payload?: CandidateRejectPayload) => {
    const res = await rejectCandidateApi(candidateId, payload)
    if (!res) throw new Error('驳回候选 FAQ 失败')
    await Promise.all([fetchCandidates(candidatesPage.value), fetchMetrics()])
  }

  // 5. 获取已发布 FAQ 列表
  const fetchPublishedFaqs = async (page: number = 1) => {
    isLoading.value = true
    faqsPage.value = page
    try {
      const res = await getPublishedFaqsApi({
        page,
        page_size: faqsPageSize.value,
        category: selectedCategory.value,
        keyword: searchKeyword.value
      })
      if (res && res.data) {
        publishedFaqs.value = res.data.items || []
        totalPublishedFaqs.value = res.data.total ?? 0
      }
    } finally {
      isLoading.value = false
    }
  }

  // 6. 手动直接发布 FAQ
  const publishFaq = async (payload: FaqCreatePayload): Promise<FaqItem> => {
    const res = await publishFaqApi(payload)
    if (!res || !res.data) throw new Error(res?.message || '发布 FAQ 失败')
    await Promise.all([fetchPublishedFaqs(1), fetchMetrics()])
    return res.data
  }

  // 7. 更新 FAQ
  const updateFaq = async (faqId: number, payload: FaqUpdatePayload): Promise<FaqItem> => {
    const res = await updateFaqApi(faqId, payload)
    if (!res || !res.data) throw new Error(res?.message || '更新 FAQ 失败')
    await fetchPublishedFaqs(faqsPage.value)
    return res.data
  }

  // 8. 切换 FAQ 启停维护状态
  const toggleFaqStatus = async (faqId: number, isEnabled: boolean) => {
    const res = await toggleFaqStatusApi(faqId, isEnabled)
    if (res && res.code === 200) {
      const target = publishedFaqs.value.find((f) => f.id === faqId)
      if (target) {
        target.is_enabled = isEnabled
        target.status = isEnabled
      }
    }
  }

  // 9. 切换极速缓存直出开关
  const toggleFaqCache = async (faqId: number, isCached: boolean) => {
    const res = await toggleFaqCacheApi(faqId, isCached)
    if (res && res.code === 200) {
      const target = publishedFaqs.value.find((f) => f.id === faqId)
      if (target) {
        target.is_cached = isCached
      }
    }
  }

  // 10. 删除 FAQ
  const deleteFaq = async (faqId: number) => {
    await deleteFaqApi(faqId)
    await fetchPublishedFaqs(faqsPage.value)
  }

  // 11. 获取知识盲区缺口列表
  const fetchKnowledgeGaps = async (page: number = 1) => {
    isLoading.value = true
    gapsPage.value = page
    try {
      const res = await getKnowledgeGapsApi({
        page,
        page_size: gapsPageSize.value,
        status: gapStatusFilter.value,
        keyword: searchKeyword.value,
        sort_by: gapSortBy.value,
        order: gapSortOrder.value
      })
      if (res && res.data) {
        knowledgeGaps.value = res.data.items || []
        totalKnowledgeGaps.value = res.data.total ?? 0
      }
    } finally {
      isLoading.value = false
    }
  }

  // 12. 知识缺口转建为补充工单
  const convertKnowledgeGap = async (gapId: number, payload: KnowledgeGapConvertPayload) => {
    const res = await convertKnowledgeGapApi(gapId, payload)
    if (!res) throw new Error('工单转建下发失败')
    await Promise.all([fetchKnowledgeGaps(gapsPage.value), fetchMetrics()])
    return res.data
  }

  // 13. 标记知识缺口已解决
  const resolveKnowledgeGap = async (gapId: number) => {
    const res = await resolveKnowledgeGapApi(gapId)
    if (!res) throw new Error('标记缺口已解决失败')
    await Promise.all([fetchKnowledgeGaps(gapsPage.value), fetchMetrics()])
    return res.data
  }

  // 14. 忽略知识缺口
  const ignoreKnowledgeGap = async (gapId: number) => {
    const res = await ignoreKnowledgeGapApi(gapId)
    if (!res) throw new Error('忽略缺口失败')
    await Promise.all([fetchKnowledgeGaps(gapsPage.value), fetchMetrics()])
    return res.data
  }

  // 13. 触发提问聚类挖掘
  const triggerMining = async () => {
    isMining.value = true
    try {
      const res = await triggerClusterMiningApi()
      await Promise.all([fetchCandidates(1), fetchMetrics()])
      return res.data
    } finally {
      isMining.value = false
    }
  }

  // 打开润色采纳抽屉
  const openEditDrawer = (candidate: FaqCandidate) => {
    selectedCandidateForEdit.value = candidate
    showEditDrawer.value = true
  }

  // 打开缺口转建工单弹窗
  const openGapModal = (gap: KnowledgeGap) => {
    selectedGapForTicket.value = gap
    showGapModal.value = true
  }

  return {
    activeTab,
    metrics,
    candidates,
    totalCandidates,
    candidatesPage,
    candidatesPageSize,
    candidateStatusFilter,
    publishedFaqs,
    totalPublishedFaqs,
    faqsPage,
    faqsPageSize,
    selectedCategory,
    knowledgeGaps,
    totalKnowledgeGaps,
    gapsPage,
    gapsPageSize,
    gapStatusFilter,
    gapSortBy,
    gapSortOrder,
    searchKeyword,
    isLoading,
    isMining,
    selectedCandidateForEdit,
    showEditDrawer,
    selectedGapForTicket,
    showGapModal,
    fetchMetrics,
    fetchCandidates,
    approveCandidate,
    rejectCandidate,
    fetchPublishedFaqs,
    publishFaq,
    updateFaq,
    toggleFaqStatus,
    toggleFaqCache,
    deleteFaq,
    fetchKnowledgeGaps,
    convertKnowledgeGap,
    resolveKnowledgeGap,
    ignoreKnowledgeGap,
    triggerMining,
    openEditDrawer,
    openGapModal
  }
})
