/**
 * 知识资产管理状态仓库 (Knowledge Store)
 * 模块: FE-M4 / P1-1
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { KnowledgeUnit } from '@/types/knowledge'
import {
  getKnowledgeUnitsApi,
  uploadDocumentApi,
  batchUploadDocumentsApi,
  updateUnitStatusApi,
  deleteKnowledgeUnitApi
} from '@/api/knowledge'

export const useKnowledgeStore = defineStore('knowledge', () => {
  const units = ref<KnowledgeUnit[]>([])
  const total = ref<number>(0)
  const page = ref<number>(1)
  const pageSize = ref<number>(10)
  const searchQuery = ref<string>('')
  const selectedFormat = ref<string>('ALL')
  const selectedCategory = ref<string>('ALL')
  const selectedStatus = ref<string>('ALL')
  const isLoading = ref<boolean>(false)

  // 统计指标计算 (PAGE-03 原型对齐)
  const metrics = computed(() => {
    let ready = 0
    let parsing = 0
    let failed = 0
    for (const u of units.value) {
      if (u.status === 'INDEXED' || u.status === 'AVAILABLE') ready++
      else if (u.status === 'PARSING' || u.status === 'CHUNKING' || u.status === 'PENDING') parsing++
      else if (u.status === 'FAILED') failed++
    }
    return {
      total: total.value,
      ready,
      parsing,
      failed
    }
  })

  // 1. 获取知识资产列表
  const fetchUnits = async () => {
    isLoading.value = true
    try {
      const res = await getKnowledgeUnitsApi({
        page: page.value,
        page_size: pageSize.value,
        search: searchQuery.value,
        format: selectedFormat.value !== 'ALL' ? selectedFormat.value : undefined,
        category: selectedCategory.value !== 'ALL' ? selectedCategory.value : undefined,
        status: selectedStatus.value !== 'ALL' ? selectedStatus.value : undefined
      })
      if (res.data) {
        units.value = res.data.items
        total.value = res.data.total
      }
    } finally {
      isLoading.value = false
    }
  }

  // 2. 上传文档联动刷新
  const uploadDocument = async (file: File, category: string = 'DEFAULT'): Promise<KnowledgeUnit> => {
    const res = await uploadDocumentApi(file, category)
    if (!res.data) {
      throw new Error(res.message || '上传失败')
    }
    // 上传成功后自动刷新表格列表
    await fetchUnits()
    return res.data
  }

  // 2.1 批量上传多文档联动刷新
  const batchUploadDocuments = async (
    files: File[],
    category: string = 'DEFAULT'
  ): Promise<KnowledgeUnit[]> => {
    const res = await batchUploadDocumentsApi(files, category)
    if (!res.data) {
      throw new Error(res.message || '批量上传失败')
    }
    // 上传成功后自动刷新表格列表
    await fetchUnits()
    return res.data
  }

  // 3. 启停用状态切换 (PATCH /status)
  const toggleStatus = async (unit: KnowledgeUnit) => {
    const isCurrentlyActive = unit.status === 'INDEXED' || unit.status === 'AVAILABLE'
    const targetStatus = isCurrentlyActive ? 'DISABLED' : 'INDEXED'

    const res = await updateUnitStatusApi(unit.id, targetStatus)
    if (res.data) {
      const idx = units.value.findIndex((u) => u.id === unit.id)
      if (idx !== -1) {
        units.value[idx].status = res.data.status
      }
    }
  }

  // 4. 单篇删除物理销毁 (DELETE)
  const deleteUnit = async (unitId: number) => {
    await deleteKnowledgeUnitApi(unitId)
    if (units.value.length === 1 && page.value > 1) {
      page.value -= 1
    }
    await fetchUnits()
  }

  // 5. 过滤条件与分页设置
  const setFilter = (params: {
    search?: string
    format?: string
    category?: string
    status?: string
  }) => {
    if (params.search !== undefined) searchQuery.value = params.search
    if (params.format !== undefined) selectedFormat.value = params.format
    if (params.category !== undefined) selectedCategory.value = params.category
    if (params.status !== undefined) selectedStatus.value = params.status
    page.value = 1
    fetchUnits()
  }

  const resetFilters = () => {
    searchQuery.value = ''
    selectedFormat.value = 'ALL'
    selectedCategory.value = 'ALL'
    selectedStatus.value = 'ALL'
    page.value = 1
    fetchUnits()
  }

  const setPage = (newPage: number) => {
    page.value = newPage
    fetchUnits()
  }

  const setPageSize = (newSize: number) => {
    pageSize.value = newSize
    page.value = 1
    fetchUnits()
  }

  return {
    units,
    total,
    page,
    pageSize,
    searchQuery,
    selectedFormat,
    selectedCategory,
    selectedStatus,
    isLoading,
    metrics,
    fetchUnits,
    uploadDocument,
    batchUploadDocuments,
    toggleStatus,
    deleteUnit,
    setFilter,
    resetFilters,
    setPage,
    setPageSize
  }
})
