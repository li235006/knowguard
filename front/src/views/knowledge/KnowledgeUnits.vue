<template>
  <!-- PAGE-03: 知识维护与导入中心 (/admin/knowledge/units) -->
  <div class="w-full space-y-4">
    <!-- Top Toast Notification -->
    <div
      v-if="toastMessage"
      class="fixed top-5 right-5 z-50 flex items-center gap-2 px-4 py-2.5 rounded-xl shadow-lg border text-xs font-medium transition-all duration-300 animate-in fade-in slide-in-from-top-4"
      :class="toastType === 'success' ? 'bg-emerald-50 text-emerald-800 border-emerald-200' : 'bg-rose-50 text-rose-800 border-rose-200'"
    >
      <CheckCircle2 v-if="toastType === 'success'" :size="15" class="text-emerald-600 shrink-0" />
      <AlertCircle v-else :size="15" class="text-rose-600 shrink-0" />
      <span>{{ toastMessage }}</span>
    </div>

    <!-- Header & Breadcrumbs -->
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <div class="flex items-center gap-2 text-xs text-[#94A3B8]">
          <span>知识管理</span>
          <span>/</span>
          <span class="text-[#0F172A] font-medium">知识资产台账</span>
        </div>
        <h1 class="text-lg font-bold text-[#0F172A] tracking-tight mt-1">
          知识资产全生命周期维护
        </h1>
        <p class="text-xs text-[#64748B] mt-0.5">
          企业多源文档台账、解析状态穿透、切片向量入库与 4D-RBAC 安全访问控制
        </p>
      </div>

      <!-- Quick Actions -->
      <div class="flex items-center gap-2">
        <button
          type="button"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#E5E7EB] bg-white text-xs font-medium text-[#475569] hover:bg-[#F8FAFC] transition-colors"
          @click="openUploadModal"
        >
          <UploadCloud :size="14" class="text-[#0071E3]" />
          <span>上传知识文档</span>
        </button>
      </div>
    </div>

    <!-- Metric Cards Row (PAGE-03 原型对齐) -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
      <!-- Card 1: 知识资产总数 -->
      <div class="bg-white rounded-xl border border-[#E5E7EB] p-3.5 shadow-sm flex flex-col justify-between">
        <div class="flex items-center justify-between text-xs text-[#64748B]">
          <span class="font-medium">知识资产总数</span>
          <div class="w-7 h-7 rounded-lg bg-blue-50 text-[#0071E3] flex items-center justify-center">
            <Files :size="14" />
          </div>
        </div>
        <div class="flex items-baseline gap-2 mt-2">
          <span class="text-xl font-bold font-mono text-[#0F172A]">{{ knowledgeStore.metrics.total }}</span>
          <span class="text-[11px] text-[#94A3B8]">篇知识文档资产</span>
        </div>
      </div>

      <!-- Card 2: 已就绪入库 -->
      <div class="bg-white rounded-xl border border-[#E5E7EB] p-3.5 shadow-sm flex flex-col justify-between">
        <div class="flex items-center justify-between text-xs text-[#64748B]">
          <span class="font-medium">已就绪入库</span>
          <div class="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <CheckCircle2 :size="14" />
          </div>
        </div>
        <div class="flex items-baseline gap-2 mt-2">
          <span class="text-xl font-bold font-mono text-emerald-600">{{ knowledgeStore.metrics.ready }}</span>
          <span class="text-[11px] text-[#94A3B8]">可实时用于智能检索</span>
        </div>
      </div>

      <!-- Card 3: 正在解析中 -->
      <div class="bg-white rounded-xl border border-[#E5E7EB] p-3.5 shadow-sm flex flex-col justify-between">
        <div class="flex items-center justify-between text-xs text-[#64748B]">
          <span class="font-medium">正在解析中</span>
          <div class="w-7 h-7 rounded-lg bg-blue-50 text-[#0071E3] flex items-center justify-center">
            <RefreshCw :size="14" class="animate-spin" />
          </div>
        </div>
        <div class="flex items-baseline gap-2 mt-2">
          <span class="text-xl font-bold font-mono text-[#0071E3]">{{ knowledgeStore.metrics.parsing }}</span>
          <span class="text-[11px] text-[#94A3B8]">分块与向量化中</span>
        </div>
      </div>

      <!-- Card 4: 解析异常待处理 -->
      <div class="bg-white rounded-xl border border-[#E5E7EB] p-3.5 shadow-sm flex flex-col justify-between">
        <div class="flex items-center justify-between text-xs text-[#64748B]">
          <span class="font-medium">解析异常待处理</span>
          <div class="w-7 h-7 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center">
            <AlertCircle :size="14" />
          </div>
        </div>
        <div class="flex items-baseline gap-2 mt-2">
          <span class="text-xl font-bold font-mono text-rose-600">{{ knowledgeStore.metrics.failed }}</span>
          <span class="text-[11px] text-[#94A3B8]">需 OCR 或格式重试</span>
        </div>
      </div>
    </div>

    <!-- Filter Bar Component -->
    <UnitsFilterBar
      :search="knowledgeStore.searchQuery"
      :format="knowledgeStore.selectedFormat"
      :category="knowledgeStore.selectedCategory"
      :status="knowledgeStore.selectedStatus"
      :loading="knowledgeStore.isLoading"
      @update:search="handleSearchUpdate"
      @update:format="handleFormatUpdate"
      @update:category="handleCategoryUpdate"
      @update:status="handleStatusUpdate"
      @search="handleSearchSubmit"
      @reset="handleResetFilters"
      @refresh="knowledgeStore.fetchUnits"
      @open-upload="openUploadModal"
    />

    <!-- Units Table Component -->
    <UnitsTable
      :units="knowledgeStore.units"
      :loading="knowledgeStore.isLoading"
      :total="knowledgeStore.total"
      :page="knowledgeStore.page"
      :page-size="knowledgeStore.pageSize"
      @toggle-status="handleToggleStatus"
      @delete-unit="handleDeleteUnit"
      @page-change="handlePageChange"
      @page-size-change="handlePageSizeChange"
      @view-chunks="handleViewChunks"
      @edit-policy="handleEditPolicy"
    />

    <!-- Document Upload Modal Dialog -->
    <div
      v-if="showUploadModal"
      class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-200"
    >
      <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-gray-100 flex flex-col gap-4 text-xs">
        <!-- Modal Header -->
        <div class="flex items-center justify-between border-b border-[#F1F5F9] pb-3">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-lg bg-blue-50 text-[#0071E3] flex items-center justify-center border border-blue-100">
              <UploadCloud :size="16" />
            </div>
            <div>
              <h3 class="text-sm font-semibold text-[#0F172A]">导入新知识文档</h3>
              <p class="text-[11px] text-[#64748B]">自动进行文本清洗、滑动切片及全量向量索引入库</p>
            </div>
          </div>
          <button
            type="button"
            class="text-[#94A3B8] hover:text-[#0F172A] p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
            @click="closeUploadModal"
          >
            <X :size="16" />
          </button>
        </div>

        <!-- Drag & Drop Zone -->
        <div
          class="border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all duration-200 flex flex-col items-center justify-center gap-2"
          :class="isDragging ? 'border-[#0071E3] bg-blue-50/40' : (selectedFile ? 'border-emerald-400 bg-emerald-50/20' : 'border-[#E2E8F0] hover:border-[#0071E3] bg-[#F8FAFC]')"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="handleFileDrop"
          @click="triggerFileInput"
        >
          <input
            ref="fileInputRef"
            type="file"
            accept=".pdf,.md,.docx,.txt"
            class="hidden"
            @change="handleFileSelect"
          />

          <!-- If File Selected -->
          <template v-if="selectedFile">
            <div class="w-10 h-10 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center">
              <FileCheck2 :size="20" />
            </div>
            <div class="flex flex-col items-center">
              <span class="font-medium text-[#0F172A] text-xs max-w-xs truncate">{{ selectedFile.name }}</span>
              <span class="text-[11px] text-[#64748B] mt-0.5 font-mono">
                大小: {{ (selectedFile.size / 1024 / 1024).toFixed(2) }} MB
              </span>
            </div>
            <button
              type="button"
              class="text-[11px] text-rose-500 hover:underline mt-1"
              @click.stop="clearSelectedFile"
            >
              重新选择文档
            </button>
          </template>

          <!-- If No File Selected -->
          <template v-else>
            <div class="w-10 h-10 rounded-full bg-blue-50 text-[#0071E3] flex items-center justify-center">
              <UploadCloud :size="20" />
            </div>
            <div class="flex flex-col items-center">
              <span class="font-medium text-[#0F172A]">点击选择或将文档拖拽至此处</span>
              <span class="text-[11px] text-[#94A3B8] mt-0.5">支持 PDF、Markdown、Word (.docx)、纯文本 (.txt)，单个文档最大 50MB</span>
            </div>
          </template>
        </div>

        <!-- Category Selection -->
        <div class="flex flex-col gap-1.5">
          <label class="font-medium text-[#475569]">文档归属业务分类</label>
          <select
            v-model="uploadCategory"
            class="bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-3 py-2 text-xs text-[#0F172A] focus:outline-none focus:border-[#0071E3]"
          >
            <option value="TECH">研发与技术 (TECH)</option>
            <option value="FINANCE">财务行政 (FINANCE)</option>
            <option value="HR">人力资源 (HR)</option>
            <option value="SECURITY">安全合规 (SECURITY)</option>
            <option value="LEGAL">法务审查 (LEGAL)</option>
            <option value="DEFAULT">通用综合 (DEFAULT)</option>
          </select>
        </div>

        <!-- Pipeline Notice -->
        <div class="bg-blue-50/50 border border-blue-100 rounded-xl p-3 text-[11px] text-[#0071E3] flex items-start gap-2">
          <Info :size="14" class="shrink-0 mt-0.5" />
          <span>上传完成后，系统将自动触发滑动切片流水线并将其写入本地与向量知识检索库。</span>
        </div>

        <!-- Modal Actions -->
        <div class="flex items-center justify-end gap-2.5 pt-2 border-t border-[#F1F5F9]">
          <button
            type="button"
            :disabled="isUploading"
            class="px-4 py-2 text-xs text-[#475569] hover:bg-gray-100 rounded-lg transition-colors font-medium"
            @click="closeUploadModal"
          >
            取消
          </button>
          <button
            type="button"
            :disabled="!selectedFile || isUploading"
            class="px-4 py-2 text-xs bg-[#0071E3] hover:bg-[#0077ED] text-white rounded-lg font-medium transition-colors shadow-sm inline-flex items-center gap-1.5 disabled:opacity-50"
            @click="submitUpload"
          >
            <Loader2 v-if="isUploading" :size="13" class="animate-spin" />
            <span>{{ isUploading ? '正在上传解析...' : '开始解析与入库' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Chunks Drawer -->
    <ChunksDrawer
      :unit="activeUnitForChunks"
      :visible="showChunksDrawer"
      @close="showChunksDrawer = false"
    />

    <!-- Security Policy Modal -->
    <SecurityModal
      :unit="activeUnitForPolicy"
      :visible="showSecurityModal"
      @close="showSecurityModal = false"
      @saved="handlePolicySaved"
    />
  </div>
</template>

<script setup lang="ts">
/**
 * 知识资产维护台账视图 (PAGE-03 原型对齐)
 * 模块: FE-M4 / P1-1
 */

import { ref, onMounted } from 'vue'
import {
  Files,
  CheckCircle2,
  RefreshCw,
  AlertCircle,
  UploadCloud,
  X,
  FileCheck2,
  Info,
  Loader2
} from 'lucide-vue-next'
import { useKnowledgeStore } from '@/stores/knowledge'
import type { KnowledgeUnit } from '@/types/knowledge'
import UnitsFilterBar from '@/components/Knowledge/UnitsFilterBar.vue'
import UnitsTable from '@/components/Knowledge/UnitsTable.vue'
import ChunksDrawer from '@/components/Knowledge/ChunksDrawer.vue'
import SecurityModal from '@/components/Knowledge/SecurityModal.vue'

const knowledgeStore = useKnowledgeStore()

// 弹窗与抽屉控制
const showUploadModal = ref<boolean>(false)
const showChunksDrawer = ref<boolean>(false)
const showSecurityModal = ref<boolean>(false)
const activeUnitForChunks = ref<KnowledgeUnit | null>(null)
const activeUnitForPolicy = ref<KnowledgeUnit | null>(null)

// 上传表单控制
const fileInputRef = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const uploadCategory = ref<string>('TECH')
const isDragging = ref<boolean>(false)
const isUploading = ref<boolean>(false)

// 响应式 Toast 提示
const toastMessage = ref<string>('')
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

// 页面加载自动获取列表
onMounted(() => {
  knowledgeStore.fetchUnits()
})

// 筛选事件
const handleSearchUpdate = (val: string) => {
  knowledgeStore.searchQuery = val
}

const handleFormatUpdate = (val: string) => {
  knowledgeStore.setFilter({ format: val })
}

const handleCategoryUpdate = (val: string) => {
  knowledgeStore.setFilter({ category: val })
}

const handleStatusUpdate = (val: string) => {
  knowledgeStore.setFilter({ status: val })
}

const handleSearchSubmit = () => {
  knowledgeStore.page = 1
  knowledgeStore.fetchUnits()
}

const handleResetFilters = () => {
  knowledgeStore.resetFilters()
  showToast('筛选条件已重置')
}

// 表格分页与交互
const handlePageChange = (newPage: number) => {
  knowledgeStore.setPage(newPage)
}

const handlePageSizeChange = (newSize: number) => {
  knowledgeStore.setPageSize(newSize)
}

// 启停用切换 (PATCH /api/v1/knowledge/units/{id}/status)
const handleToggleStatus = async (unit: KnowledgeUnit) => {
  try {
    await knowledgeStore.toggleStatus(unit)
    const newStatusText = unit.status === 'INDEXED' || unit.status === 'AVAILABLE' ? '启用' : '停用'
    showToast(`文档 [${unit.title}] 已成功切换为${newStatusText}状态`)
  } catch (err) {
    showToast(err instanceof Error ? err.message : '切换状态失败', 'error')
  }
}

// 删除确认执行 (DELETE /api/v1/knowledge/units/{id})
const handleDeleteUnit = async (unitId: number) => {
  try {
    await knowledgeStore.deleteUnit(unitId)
    showToast('知识资产及关联分块向量已永久销毁')
  } catch (err) {
    showToast(err instanceof Error ? err.message : '销毁知识资产失败', 'error')
  }
}

// 穿透抽屉与权限配置
const handleViewChunks = (unit: KnowledgeUnit) => {
  activeUnitForChunks.value = unit
  showChunksDrawer.value = true
}

const handleEditPolicy = (unit: KnowledgeUnit) => {
  activeUnitForPolicy.value = unit
  showSecurityModal.value = true
}

const handlePolicySaved = () => {
  showToast('4D-RBAC 权限策略已保存并同步缓存')
  knowledgeStore.fetchUnits()
}

// 文档上传操作
const openUploadModal = () => {
  selectedFile.value = null
  uploadCategory.value = 'TECH'
  isDragging.value = false
  showUploadModal.value = true
}

const closeUploadModal = () => {
  if (isUploading.value) return
  showUploadModal.value = false
  selectedFile.value = null
}

const triggerFileInput = () => {
  fileInputRef.value?.click()
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0]
  }
}

const handleFileDrop = (event: DragEvent) => {
  isDragging.value = false
  if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
    selectedFile.value = event.dataTransfer.files[0]
  }
}

const clearSelectedFile = () => {
  selectedFile.value = null
  if (fileInputRef.value) fileInputRef.value.value = ''
}

// 上传联动刷新
const submitUpload = async () => {
  if (!selectedFile.value) return
  isUploading.value = true
  try {
    const newUnit = await knowledgeStore.uploadDocument(selectedFile.value, uploadCategory.value)
    showToast(`文档 [${newUnit.title}] 上传成功，已自动加入台账并完成切片向量化`)
    closeUploadModal()
  } catch (err) {
    showToast(err instanceof Error ? err.message : '上传失败', 'error')
  } finally {
    isUploading.value = false
  }
}
</script>
