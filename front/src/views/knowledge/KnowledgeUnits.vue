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
            <RefreshCw :size="14" :class="{ 'animate-spin': knowledgeStore.metrics.parsing > 0 }" />
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
      @batch-delete="handleBatchDelete"
      @page-change="handlePageChange"
      @page-size-change="handlePageSizeChange"
      @view-chunks="handleViewChunks"
      @edit-policy="handleEditPolicy"
    />

    <!-- Document Batch Upload Modal Dialog -->
    <div
      v-if="showUploadModal"
      class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-200"
    >
      <div class="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl border border-gray-100 flex flex-col gap-4 text-xs max-h-[92vh] overflow-y-auto">
        <!-- Modal Header -->
        <div class="flex items-center justify-between border-b border-[#F1F5F9] pb-3">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-lg bg-blue-50 text-[#0071E3] flex items-center justify-center border border-blue-100">
              <UploadCloud :size="16" />
            </div>
            <div>
              <h3 class="text-sm font-semibold text-[#0F172A]">批量导入知识文档</h3>
              <p class="text-[11px] text-[#64748B]">多格式自动清洗、滑动分块与向量入库一体化流水线</p>
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

        <!-- Hidden Multiple File Input -->
        <input
          ref="fileInputRef"
          type="file"
          multiple
          accept=".pdf,.md,.docx,.txt"
          class="hidden"
          @change="handleFileSelect"
        />

        <!-- Drag & Drop Zone -->
        <div
          class="border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-all duration-200 flex flex-col items-center justify-center gap-2"
          :class="isDragging ? 'border-[#0071E3] bg-blue-50/40' : (uploadQueue.length > 0 ? 'border-blue-200 bg-blue-50/10 hover:border-[#0071E3]' : 'border-[#E2E8F0] hover:border-[#0071E3] bg-[#F8FAFC]')"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="handleFileDrop"
          @click="triggerFileInput"
        >
          <div class="w-10 h-10 rounded-full bg-blue-50 text-[#0071E3] flex items-center justify-center">
            <UploadCloud :size="20" />
          </div>
          <div class="flex flex-col items-center">
            <span class="font-medium text-[#0F172A]">
              {{ uploadQueue.length > 0 ? '点击或继续拖拽文档追加到队列' : '点击选择或将文档批量拖拽至此处' }}
            </span>
            <span class="text-[11px] text-[#94A3B8] mt-0.5">
              支持 Word (.docx)、PDF (.pdf)、Markdown (.md)、纯文本 (.txt)，支持批量多选，单文件最大 50MB
            </span>
          </div>
        </div>

        <!-- Batch Queue List (when items exist) -->
        <div v-if="uploadQueue.length > 0" class="flex flex-col gap-2">
          <div class="flex items-center justify-between text-[11px] text-[#64748B]">
            <span class="font-medium">
              待处理文档队列 ({{ completedFilesCount }}/{{ uploadQueue.length }} 完成)
            </span>
            <button
              v-if="!isUploading"
              type="button"
              class="text-rose-500 hover:text-rose-700 font-medium hover:underline inline-flex items-center gap-1"
              @click="clearUploadQueue"
            >
              <Trash2 :size="12" />
              <span>清空全部</span>
            </button>
          </div>

          <!-- Scrollable Queue List -->
          <div class="max-h-52 overflow-y-auto space-y-2 border border-slate-200 rounded-xl p-2.5 bg-slate-50/60">
            <div
              v-for="item in uploadQueue"
              :key="item.id"
              class="bg-white border rounded-lg p-2.5 flex items-center justify-between gap-3 shadow-xs transition-all"
              :class="{
                'border-slate-200': item.status === 'pending',
                'border-blue-300 bg-blue-50/20': item.status === 'uploading',
                'border-emerald-300 bg-emerald-50/20': item.status === 'indexed',
                'border-rose-300 bg-rose-50/20': item.status === 'failed'
              }"
            >
              <!-- File Info & Format Badge -->
              <div class="flex items-center gap-2.5 min-w-0 flex-1">
                <div
                  class="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 border"
                  :class="getQueueFileTypeStyle(item.file_type).iconWrapperClass"
                >
                  <component
                    :is="getQueueFileTypeStyle(item.file_type).iconComponent"
                    :size="14"
                    :class="getQueueFileTypeStyle(item.file_type).iconColor"
                  />
                </div>
                <div class="flex flex-col min-w-0 flex-1">
                  <div class="flex items-center gap-2">
                    <span class="font-medium text-[#0F172A] text-xs truncate" :title="item.name">
                      {{ item.name }}
                    </span>
                    <span
                      class="text-[9px] px-1 py-0.2 rounded font-bold uppercase shrink-0"
                      :class="getQueueFileTypeStyle(item.file_type).badgeClass"
                    >
                      {{ item.file_type }}
                    </span>
                  </div>
                  <div class="flex items-center gap-2 text-[10px] text-[#64748B] mt-0.5">
                    <span>{{ formatQueueFileSize(item.size) }}</span>
                    <span v-if="item.error_message" class="text-rose-500 font-medium truncate">
                      {{ item.error_message }}
                    </span>
                  </div>
                  <!-- Progress bar for uploading item -->
                  <div v-if="item.status === 'uploading'" class="w-full bg-blue-100 rounded-full h-1 mt-1.5 overflow-hidden">
                    <div
                      class="bg-[#0071E3] h-full rounded-full transition-all duration-300"
                      :style="{ width: `${item.progress}%` }"
                    ></div>
                  </div>
                </div>
              </div>

              <!-- Status Badge & Remove Action -->
              <div class="flex items-center gap-2 shrink-0">
                <!-- Status Badge -->
                <span
                  class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium"
                  :class="{
                    'bg-slate-100 text-slate-600 border border-slate-200': item.status === 'pending',
                    'bg-blue-50 text-blue-600 border border-blue-200': item.status === 'uploading',
                    'bg-emerald-50 text-emerald-700 border border-emerald-200': item.status === 'indexed',
                    'bg-rose-50 text-rose-700 border border-rose-200': item.status === 'failed'
                  }"
                >
                  <Clock v-if="item.status === 'pending'" :size="11" />
                  <Loader2 v-else-if="item.status === 'uploading'" :size="11" class="animate-spin" />
                  <CheckCircle2 v-else-if="item.status === 'indexed'" :size="11" />
                  <AlertCircle v-else-if="item.status === 'failed'" :size="11" />
                  <span>
                    {{
                      item.status === 'pending'
                        ? '等待中'
                        : item.status === 'uploading'
                          ? `解析切片中 ${item.progress}%`
                          : item.status === 'indexed'
                            ? '已就绪'
                            : '失败'
                    }}
                  </span>
                </span>

                <!-- Remove Row (only when not uploading) -->
                <button
                  v-if="!isUploading"
                  type="button"
                  class="text-[#94A3B8] hover:text-rose-500 p-1 rounded hover:bg-slate-100 transition-colors"
                  title="移除此文档"
                  @click.stop="removeQueueItem(item.id)"
                >
                  <X :size="13" />
                </button>
              </div>
            </div>
          </div>

          <!-- Overall Batch Progress Indicator -->
          <div v-if="isUploading || completedFilesCount > 0" class="mt-1 space-y-1">
            <div class="flex items-center justify-between text-[11px] text-[#64748B]">
              <span>批量处理进度</span>
              <span class="font-mono text-[#0071E3] font-medium">
                {{ completedFilesCount }}/{{ uploadQueue.length }} 完成 ({{ overallProgress }}%)
              </span>
            </div>
            <div class="w-full bg-slate-100 rounded-full h-2 overflow-hidden border border-slate-200">
              <div
                class="bg-[#0071E3] h-full rounded-full transition-all duration-300"
                :style="{ width: `${overallProgress}%` }"
              ></div>
            </div>
          </div>
        </div>

        <!-- Category Selection -->
        <div class="flex flex-col gap-1.5">
          <label class="font-medium text-[#475569]">文档归属业务分类</label>
          <select
            v-model="uploadCategory"
            :disabled="isUploading"
            class="bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-3 py-2 text-xs text-[#0F172A] focus:outline-none focus:border-[#0071E3] disabled:opacity-60"
          >
            <option value="TECH">研发与技术 (TECH)</option>
            <option value="FINANCE">财务行政 (FINANCE)</option>
            <option value="HR">人力资源 (HR)</option>
            <option value="SECURITY">安全合规 (SECURITY)</option>
            <option value="LEGAL">法务审查 (LEGAL)</option>
            <option value="DEFAULT">通用综合 (DEFAULT)</option>
          </select>
        </div>

        <!-- Pipeline & Permission Notice -->
        <div class="space-y-2">
          <div class="bg-blue-50/50 border border-blue-100 rounded-xl p-3 text-[11px] text-[#0071E3] flex items-start gap-2">
            <Info :size="14" class="shrink-0 mt-0.5" />
            <span>批量上传完成后，系统将自动触发滑动切片流水线并将其写入本地与向量知识检索库。</span>
          </div>
          <div class="bg-amber-50/60 border border-amber-200/60 rounded-xl p-3 text-[11px] text-amber-800 flex items-start gap-2">
            <ShieldCheck :size="14" class="shrink-0 mt-0.5 text-amber-600" />
            <span><strong>权限说明</strong>：此处的“业务分类”仅作为文档领域归类。文档入库后默认全员公开；如需设置为“<strong>仅管理员可见</strong>”或指定部门可见，请在上传完成后点击列表对应行右侧的【<strong>权限设置</strong>】进行四维精准授权。</span>
          </div>
        </div>

        <!-- Modal Actions -->
        <div class="flex items-center justify-between pt-2 border-t border-[#F1F5F9]">
          <span class="text-[11px] text-[#94A3B8]">
            {{ uploadQueue.length > 0 ? `已就绪 ${uploadQueue.length} 篇待入库资产` : '尚未选择文档' }}
          </span>
          <div class="flex items-center gap-2.5">
            <button
              type="button"
              :disabled="isUploading"
              class="px-4 py-2 text-xs text-[#475569] hover:bg-gray-100 rounded-lg transition-colors font-medium disabled:opacity-50"
              @click="closeUploadModal"
            >
              {{ completedFilesCount === uploadQueue.length && uploadQueue.length > 0 ? '完成' : '取消' }}
            </button>
            <button
              type="button"
              :disabled="uploadQueue.length === 0 || isUploading"
              class="px-4 py-2 text-xs bg-[#0071E3] hover:bg-[#0077ED] text-white rounded-lg font-medium transition-colors shadow-sm inline-flex items-center gap-1.5 disabled:opacity-50"
              @click="submitBatchUpload"
            >
              <Loader2 v-if="isUploading" :size="13" class="animate-spin" />
              <span>
                {{
                  isUploading
                    ? `正在批量解析入库 (${completedFilesCount}/${uploadQueue.length})...`
                    : `开始批量解析与入库 (${uploadQueue.length})`
                }}
              </span>
            </button>
          </div>
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

import { ref, computed, onMounted } from 'vue'
import {
  Files,
  CheckCircle2,
  RefreshCw,
  AlertCircle,
  UploadCloud,
  X,
  Info,
  Loader2,
  FileText,
  FileCode2,
  File,
  Trash2,
  Clock
} from 'lucide-vue-next'
import { useKnowledgeStore } from '@/stores/knowledge'
import type { KnowledgeUnit, PermissionPolicyConfig, BatchUploadItem } from '@/types/knowledge'
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

// 批量上传控制与队列状态
const fileInputRef = ref<HTMLInputElement | null>(null)
const uploadQueue = ref<BatchUploadItem[]>([])
const uploadCategory = ref<string>('TECH')
const isDragging = ref<boolean>(false)
const isUploading = ref<boolean>(false)

// 批量上传计算指标
const completedFilesCount = computed(() => uploadQueue.value.filter((i) => i.status === 'indexed').length)
const overallProgress = computed(() => {
  if (uploadQueue.value.length === 0) return 0
  const totalProg = uploadQueue.value.reduce((sum, item) => sum + item.progress, 0)
  return Math.round(totalProg / uploadQueue.value.length)
})

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

// 批量删除执行
const handleBatchDelete = async (unitIds: number[]) => {
  if (!unitIds || unitIds.length === 0) return
  try {
    for (const id of unitIds) {
      await knowledgeStore.deleteUnit(id)
    }
    showToast(`成功批量物理销毁 ${unitIds.length} 篇知识资产及其向量`)
  } catch (err) {
    showToast(err instanceof Error ? err.message : '批量删除失败', 'error')
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

const handlePolicySaved = (savedPolicy?: PermissionPolicyConfig) => {
  if (activeUnitForPolicy.value && savedPolicy) {
    if (savedPolicy.is_global || savedPolicy.is_public) {
      activeUnitForPolicy.value.permission_summary = '全员公开'
    } else {
      const parts: string[] = []
      if (savedPolicy.department_ids && savedPolicy.department_ids.length > 0) {
        parts.push(`部门(${savedPolicy.department_ids.length})`)
      }
      if (savedPolicy.role_ids && savedPolicy.role_ids.length > 0) {
        parts.push(`角色(${savedPolicy.role_ids.length})`)
      }
      if (savedPolicy.user_ids && savedPolicy.user_ids.length > 0) {
        parts.push(`特权员工(${savedPolicy.user_ids.length})`)
      }
      activeUnitForPolicy.value.permission_summary = parts.length > 0 ? parts.join(' / ') : '受限私有 (无授权)'
    }
  }
  showToast('4D-RBAC 权限策略已成功保存并同步向量索引')
  knowledgeStore.fetchUnits()
}

// 格式化队列中文件大小与格式风格
const formatQueueFileSize = (bytes?: number): string => {
  if (!bytes || bytes <= 0) return '-'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let idx = 0
  while (size >= 1024 && idx < units.length - 1) {
    size /= 1024
    idx++
  }
  return `${size.toFixed(idx === 0 ? 0 : 1)} ${units[idx]}`
}

const getQueueFileTypeStyle = (fileType: string) => {
  const t = (fileType || '').toUpperCase()
  if (t === 'PDF') {
    return {
      iconComponent: FileText,
      iconColor: 'text-red-500',
      iconWrapperClass: 'bg-red-50 border-red-100',
      badgeClass: 'bg-red-50 text-red-600 border border-red-200'
    }
  }
  if (t === 'MD' || t === 'MARKDOWN') {
    return {
      iconComponent: FileCode2,
      iconColor: 'text-purple-500',
      iconWrapperClass: 'bg-purple-50 border-purple-100',
      badgeClass: 'bg-purple-50 text-purple-600 border border-purple-200'
    }
  }
  if (t === 'DOCX' || t === 'DOC') {
    return {
      iconComponent: FileText,
      iconColor: 'text-blue-500',
      iconWrapperClass: 'bg-blue-50 border-blue-100',
      badgeClass: 'bg-blue-50 text-blue-600 border border-blue-200'
    }
  }
  return {
    iconComponent: File,
    iconColor: 'text-slate-500',
    iconWrapperClass: 'bg-slate-50 border-slate-200',
    badgeClass: 'bg-slate-100 text-slate-600 border border-slate-200'
  }
}

// 批量文档上传队列操作
const addFilesToQueue = (files: FileList | File[]) => {
  const allowedExtensions = ['PDF', 'MD', 'DOCX', 'DOC', 'TXT']
  const maxSizeBytes = 50 * 1024 * 1024 // 50MB

  Array.from(files).forEach((file) => {
    const ext = file.name.split('.').pop()?.toUpperCase() || 'TXT'
    if (!allowedExtensions.includes(ext)) {
      showToast(`文档 [${file.name}] 格式不受支持，系统支持 Word (.docx)、PDF (.pdf)、Markdown (.md) 与 TXT (.txt)`, 'error')
      return
    }
    if (file.size > maxSizeBytes) {
      showToast(`文档 [${file.name}] 大小超过 50MB 限制`, 'error')
      return
    }
    const exists = uploadQueue.value.some((item) => item.name === file.name && item.size === file.size)
    if (!exists) {
      uploadQueue.value.push({
        id: `${file.name}-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
        file,
        name: file.name,
        size: file.size,
        file_type: ext,
        status: 'pending',
        progress: 0
      })
    }
  })

  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

const openUploadModal = () => {
  uploadQueue.value = []
  uploadCategory.value = 'TECH'
  isDragging.value = false
  showUploadModal.value = true
}

const closeUploadModal = () => {
  if (isUploading.value) return
  showUploadModal.value = false
  uploadQueue.value = []
}

const triggerFileInput = () => {
  fileInputRef.value?.click()
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    addFilesToQueue(target.files)
  }
}

const handleFileDrop = (event: DragEvent) => {
  isDragging.value = false
  if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
    addFilesToQueue(event.dataTransfer.files)
  }
}

const removeQueueItem = (id: string) => {
  if (isUploading.value) return
  uploadQueue.value = uploadQueue.value.filter((i) => i.id !== id)
}

const clearUploadQueue = () => {
  if (isUploading.value) return
  uploadQueue.value = []
  if (fileInputRef.value) fileInputRef.value.value = ''
}

// 批量上传与进度同步
const submitBatchUpload = async () => {
  if (uploadQueue.value.length === 0 || isUploading.value) return
  isUploading.value = true

  const pendingItems = uploadQueue.value.filter((i) => i.status === 'pending' || i.status === 'failed')
  if (pendingItems.length === 0) {
    isUploading.value = false
    return
  }

  pendingItems.forEach((item) => {
    item.status = 'uploading'
    item.progress = 15
    item.error_message = undefined
  })

  const progressInterval = setInterval(() => {
    pendingItems.forEach((item) => {
      if (item.status === 'uploading' && item.progress < 85) {
        item.progress += Math.floor(Math.random() * 15) + 5
      }
    })
  }, 200)

  try {
    const rawFiles = pendingItems.map((i) => i.file)
    const resultUnits = await knowledgeStore.batchUploadDocuments(rawFiles, uploadCategory.value)
    clearInterval(progressInterval)

    pendingItems.forEach((item) => {
      item.status = 'indexed'
      item.progress = 100
    })

    showToast(`成功批量上传并入库 ${resultUnits.length} 篇知识文档`, 'success')

    // 延迟自动关闭弹窗
    setTimeout(() => {
      if (showUploadModal.value && !uploadQueue.value.some((i) => i.status === 'failed')) {
        closeUploadModal()
      }
    }, 1200)
  } catch (err: unknown) {
    clearInterval(progressInterval)
    const errorMsg = err instanceof Error ? err.message : '批量上传失败'
    pendingItems.forEach((item) => {
      item.status = 'failed'
      item.error_message = errorMsg
    })
    showToast(errorMsg, 'error')
  } finally {
    isUploading.value = false
  }
}
</script>
