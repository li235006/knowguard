<template>
  <!-- FE-M4: 知识资产台账数据表格 (PAGE-03 原型精确对齐) -->
  <div class="w-full bg-white rounded-xl border border-[#E5E7EB] shadow-sm flex flex-col min-w-0 overflow-hidden">
    <!-- Table Container -->
    <div class="relative flex-1 overflow-x-auto overflow-y-auto">
      <!-- Loading Overlay -->
      <div
        v-if="loading"
        class="absolute inset-0 bg-white/70 backdrop-blur-[2px] z-10 flex items-center justify-center"
      >
        <div class="flex flex-col items-center gap-2 text-xs text-[#0071E3] font-medium">
          <Loader2 :size="22" class="animate-spin" />
          <span>正在检索与同步知识资产台账...</span>
        </div>
      </div>

      <table class="w-full text-left border-collapse text-xs">
        <thead>
          <tr class="bg-[#F8FAFC] text-[#64748B] border-b border-[#E5E7EB] font-medium select-none">
            <th class="py-2.5 px-4 w-10 text-center">
              <input
                type="checkbox"
                class="rounded border-[#CBD5E1] text-[#0071E3] focus:ring-0 cursor-pointer"
                :checked="isAllSelected"
                :indeterminate="isIndeterminate"
                @change="toggleSelectAll"
              />
            </th>
            <th class="py-2.5 px-3 w-24">Unit ID</th>
            <th class="py-2.5 px-4 min-w-[240px]">文档名称与分类</th>
            <th class="py-2.5 px-3 w-20 text-center">格式</th>
            <th class="py-2.5 px-3 w-24 text-right">文件大小</th>
            <th class="py-2.5 px-3 w-20 text-center">切片</th>
            <th class="py-2.5 px-4 min-w-[150px]">四维权限概要</th>
            <th class="py-2.5 px-3 w-24 text-center">状态</th>
            <th class="py-2.5 px-3 w-32">更新时间</th>
            <th class="py-2.5 px-4 w-44 text-right">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-[#F1F5F9]">
          <tr
            v-for="unit in units"
            :key="unit.id"
            class="hover:bg-[#F8FAFC]/80 transition-colors group"
            :class="{ 'bg-blue-50/20': selectedIds.has(unit.id) }"
          >
            <!-- Checkbox -->
            <td class="py-3 px-4 text-center">
              <input
                type="checkbox"
                class="rounded border-[#CBD5E1] text-[#0071E3] focus:ring-0 cursor-pointer"
                :checked="selectedIds.has(unit.id)"
                @change="toggleSelectRow(unit.id)"
              />
            </td>

            <!-- Unit ID -->
            <td class="py-3 px-3 font-mono font-medium text-[#64748B]">
              KU-{{ unit.id }}
            </td>

            <!-- Doc Title & Category -->
            <td class="py-3 px-4">
              <div class="flex items-center gap-2.5">
                <!-- File Type Icon -->
                <div
                  class="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 border"
                  :class="getFileTypeStyle(unit.file_type).iconWrapperClass"
                >
                  <component
                    :is="getFileTypeStyle(unit.file_type).iconComponent"
                    :size="14"
                    :class="getFileTypeStyle(unit.file_type).iconColor"
                  />
                </div>

                <!-- Title and Category Subtext -->
                <div class="flex flex-col min-w-0">
                  <span
                    class="font-medium text-[#0F172A] truncate max-w-[320px] hover:text-[#0071E3] cursor-pointer"
                    :title="unit.title"
                    @click="emit('view-chunks', unit)"
                  >
                    {{ unit.title }}
                  </span>
                  <div class="flex items-center gap-2 mt-0.5">
                    <span
                      class="inline-block text-[10px] px-1.5 py-0.2 rounded font-mono"
                      :class="getCategoryStyle(unit.category)"
                    >
                      {{ getCategoryLabel(unit.category) }}
                    </span>
                    <span
                      v-if="unit.error_message"
                      class="text-[10px] text-red-500 truncate max-w-[200px]"
                      :title="unit.error_message"
                    >
                      错误: {{ unit.error_message }}
                    </span>
                  </div>
                </div>
              </div>
            </td>

            <!-- Format Badge -->
            <td class="py-3 px-3 text-center">
              <span
                class="inline-block px-1.5 py-0.5 rounded text-[10px] font-bold tracking-wider"
                :class="getFileTypeStyle(unit.file_type).badgeClass"
              >
                {{ unit.file_type.toUpperCase() }}
              </span>
            </td>

            <!-- File Size -->
            <td class="py-3 px-3 text-right font-mono text-[#64748B]">
              {{ formatFileSize(unit.file_size) }}
            </td>

            <!-- Chunk Count -->
            <td class="py-3 px-3 text-center">
              <button
                type="button"
                class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-100 hover:bg-slate-200 text-[#334155] font-mono text-[11px] font-medium transition-colors"
                title="查看向量切片详情"
                @click="emit('view-chunks', unit)"
              >
                <Layers :size="11" class="text-[#64748B]" />
                <span>{{ unit.chunk_count }}</span>
              </button>
            </td>

            <!-- Permissions Summary -->
            <td class="py-3 px-4">
              <div class="flex items-center gap-1.5">
                <span
                  class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium truncate max-w-[200px]"
                  :class="getPermissionBadgeStyle(unit.permission_summary)"
                  :title="unit.permission_summary || '未配置策略'"
                >
                  <ShieldCheck
                    v-if="unit.permission_summary?.includes('公开')"
                    :size="11"
                    class="text-emerald-600"
                  />
                  <Lock
                    v-else
                    :size="11"
                    class="text-indigo-600"
                  />
                  <span>{{ unit.permission_summary || '全员公开' }}</span>
                </span>
              </div>
            </td>

            <!-- Status Badge -->
            <td class="py-3 px-3 text-center">
              <div class="inline-flex items-center gap-1.5">
                <span
                  class="w-2 h-2 rounded-full shrink-0"
                  :class="getStatusDotClass(unit.status)"
                ></span>
                <span
                  class="text-[11px] font-medium"
                  :class="getStatusTextClass(unit.status)"
                >
                  {{ getStatusLabel(unit.status) }}
                </span>
                <Loader2
                  v-if="unit.status === 'PARSING' || unit.status === 'CHUNKING'"
                  :size="11"
                  class="animate-spin text-blue-500"
                />
              </div>
            </td>

            <!-- Created/Updated Time -->
            <td class="py-3 px-3 font-mono text-[11px] text-[#94A3B8] whitespace-nowrap">
              {{ formatDateTime(unit.created_at) }}
            </td>

            <!-- Actions -->
            <td class="py-3 px-4 text-right whitespace-nowrap">
              <div class="flex items-center justify-end gap-3">
                <!-- Status Toggle Switch (PATCH /status) -->
                <label
                  class="relative inline-flex items-center select-none"
                  :class="isStatusToggleDisabled(unit.status) ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'"
                  :title="isStatusToggleDisabled(unit.status) ? '正在解析或异常，暂无法切换启停状态' : (isActive(unit.status) ? '点击停用' : '点击重新启用')"
                >
                  <input
                    type="checkbox"
                    :checked="isActive(unit.status)"
                    :disabled="isStatusToggleDisabled(unit.status) || isUpdatingStatus === unit.id"
                    class="sr-only peer"
                    @change="handleToggleStatus(unit)"
                  />
                  <div
                    class="w-7 h-4 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-[#0071E3]"
                  ></div>
                </label>

                <!-- Chunks Detail Trigger -->
                <button
                  type="button"
                  class="text-[11px] font-medium text-[#0071E3] hover:underline"
                  @click="emit('view-chunks', unit)"
                >
                  切片
                </button>

                <!-- Security Policy Trigger -->
                <button
                  type="button"
                  class="text-[11px] font-medium text-[#475569] hover:text-[#0071E3] transition-colors"
                  @click="emit('edit-policy', unit)"
                >
                  权限
                </button>

                <!-- Delete Action Trigger -->
                <button
                  type="button"
                  class="text-[11px] font-medium text-rose-500 hover:text-rose-700 transition-colors"
                  @click="openDeleteDialog(unit)"
                >
                  删除
                </button>
              </div>
            </td>
          </tr>

          <!-- Empty State -->
          <tr v-if="!loading && units.length === 0">
            <td colspan="10" class="py-16 text-center text-[#94A3B8]">
              <div class="flex flex-col items-center justify-center gap-2.5">
                <div class="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-slate-400">
                  <Inbox :size="24" />
                </div>
                <span class="font-medium text-slate-600">未找到符合条件的知识文档资产</span>
                <span class="text-slate-400 text-[11px]">您可以尝试调整检索词或上传全新的企业文档</span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination Footer -->
    <div class="p-3 border-t border-[#F1F5F9] bg-[#FAFAFA]/60 flex flex-wrap items-center justify-between gap-3 text-xs text-[#64748B]">
      <!-- Left: Summary & Selected Count -->
      <div class="flex items-center gap-3">
        <div>
          共 <span class="font-medium text-[#0F172A]">{{ total }}</span> 篇文档资产
        </div>
        <div v-if="selectedIds.size > 0" class="text-[#0071E3] font-medium">
          已选中 {{ selectedIds.size }} 项
        </div>
      </div>

      <!-- Right: Page Controls & Page Size -->
      <div class="flex items-center gap-3">
        <!-- Page Size Selector -->
        <div class="flex items-center gap-1.5 text-[#64748B]">
          <span>每页</span>
          <select
            :value="pageSize"
            class="bg-white border border-[#E5E7EB] rounded px-2 py-0.5 text-xs text-[#0F172A] focus:outline-none focus:border-[#0071E3]"
            @change="onPageSizeChange"
          >
            <option :value="10">10 篇</option>
            <option :value="20">20 篇</option>
            <option :value="50">50 篇</option>
          </select>
        </div>

        <!-- Navigation Buttons -->
        <div class="flex items-center gap-1.5">
          <button
            type="button"
            :disabled="page <= 1 || loading"
            class="px-2.5 py-1 border border-[#E5E7EB] rounded bg-white hover:bg-gray-50 disabled:opacity-40 disabled:hover:bg-white text-xs text-[#475569] transition-colors"
            @click="changePage(page - 1)"
          >
            上一页
          </button>
          <span class="px-2 font-mono text-[#0F172A]">
            {{ page }} / {{ totalPages || 1 }}
          </span>
          <button
            type="button"
            :disabled="page >= totalPages || loading"
            class="px-2.5 py-1 border border-[#E5E7EB] rounded bg-white hover:bg-gray-50 disabled:opacity-40 disabled:hover:bg-white text-xs text-[#475569] transition-colors"
            @click="changePage(page + 1)"
          >
            下一页
          </button>
        </div>
      </div>
    </div>

    <!-- Single Delete Confirmation Dialog -->
    <div
      v-if="unitToDelete"
      class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-200"
    >
      <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-gray-100 flex flex-col gap-4">
        <!-- Header -->
        <div class="flex items-start gap-3">
          <div class="w-10 h-10 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center shrink-0">
            <Trash2 :size="20" />
          </div>
          <div class="flex-1">
            <h3 class="font-semibold text-sm text-[#0F172A]">确认物理销毁该知识资产？</h3>
            <p class="text-xs text-[#64748B] mt-1 leading-relaxed">
              此操作将永久物理删除文档及其在向量数据库中对应的全部分块与索引，无法撤回。
            </p>
          </div>
        </div>

        <!-- Target Detail Box -->
        <div class="bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl p-3 text-xs flex flex-col gap-1.5">
          <div class="flex items-center justify-between text-[#64748B]">
            <span>资产编号:</span>
            <span class="font-mono font-medium text-[#0F172A]">KU-{{ unitToDelete.id }}</span>
          </div>
          <div class="flex items-center justify-between text-[#64748B]">
            <span>文档名称:</span>
            <span class="font-medium text-[#0F172A] truncate max-w-[240px]">{{ unitToDelete.title }}</span>
          </div>
          <div class="flex items-center justify-between text-[#64748B]">
            <span>切片数量:</span>
            <span class="font-mono text-rose-600 font-medium">{{ unitToDelete.chunk_count }} 个切片向量待销毁</span>
          </div>
        </div>

        <!-- Modal Actions -->
        <div class="flex items-center justify-end gap-2.5 pt-2 border-t border-[#F1F5F9]">
          <button
            type="button"
            :disabled="isDeleting"
            class="px-4 py-2 text-xs text-[#475569] hover:bg-gray-100 rounded-lg transition-colors font-medium"
            @click="unitToDelete = null"
          >
            取消
          </button>
          <button
            type="button"
            :disabled="isDeleting"
            class="px-4 py-2 text-xs bg-rose-600 hover:bg-rose-700 text-white rounded-lg font-medium transition-colors shadow-sm inline-flex items-center gap-1.5 disabled:opacity-50"
            @click="confirmDelete"
          >
            <Loader2 v-if="isDeleting" :size="13" class="animate-spin" />
            <span>{{ isDeleting ? '正在销毁...' : '确认物理销毁' }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 知识资产台账数据表格组件
 * 模块: FE-M4 (PAGE-03 原型精确对齐)
 */

import { ref, computed } from 'vue'
import {
  FileText,
  FileCode2,
  FileSpreadsheet,
  File,
  Layers,
  ShieldCheck,
  Lock,
  Trash2,
  Inbox,
  Loader2
} from 'lucide-vue-next'
import type { KnowledgeUnit } from '@/types/knowledge'

const props = withDefaults(
  defineProps<{
    units: KnowledgeUnit[]
    loading?: boolean
    total: number
    page: number
    pageSize: number
  }>(),
  {
    loading: false
  }
)

const emit = defineEmits<{
  (e: 'toggle-status', unit: KnowledgeUnit): void
  (e: 'delete-unit', unitId: number): void
  (e: 'page-change', page: number): void
  (e: 'page-size-change', size: number): void
  (e: 'view-chunks', unit: KnowledgeUnit): void
  (e: 'edit-policy', unit: KnowledgeUnit): void
}>()

// 多选与状态控制
const selectedIds = ref<Set<number>>(new Set())
const isUpdatingStatus = ref<number | null>(null)
const unitToDelete = ref<KnowledgeUnit | null>(null)
const isDeleting = ref<boolean>(false)

const totalPages = computed(() => Math.ceil(props.total / props.pageSize) || 1)

const isAllSelected = computed(() => {
  return props.units.length > 0 && props.units.every((u) => selectedIds.value.has(u.id))
})

const isIndeterminate = computed(() => {
  const selectedCount = props.units.filter((u) => selectedIds.value.has(u.id)).length
  return selectedCount > 0 && selectedCount < props.units.length
})

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    props.units.forEach((u) => selectedIds.value.delete(u.id))
  } else {
    props.units.forEach((u) => selectedIds.value.add(u.id))
  }
}

const toggleSelectRow = (id: number) => {
  if (selectedIds.value.has(id)) {
    selectedIds.value.delete(id)
  } else {
    selectedIds.value.add(id)
  }
}

// 格式与样式映射
const getFileTypeStyle = (fileType: string) => {
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
  if (t === 'XLSX' || t === 'CSV') {
    return {
      iconComponent: FileSpreadsheet,
      iconColor: 'text-emerald-500',
      iconWrapperClass: 'bg-emerald-50 border-emerald-100',
      badgeClass: 'bg-emerald-50 text-emerald-600 border border-emerald-200'
    }
  }
  return {
    iconComponent: File,
    iconColor: 'text-slate-500',
    iconWrapperClass: 'bg-slate-50 border-slate-200',
    badgeClass: 'bg-slate-100 text-slate-600 border border-slate-200'
  }
}

const getCategoryLabel = (category: string): string => {
  const map: Record<string, string> = {
    TECH: '研发技术',
    FINANCE: '财务行政',
    HR: '人力资源',
    SECURITY: '安全合规',
    LEGAL: '法务审查',
    DEFAULT: '通用分类'
  }
  return map[category?.toUpperCase()] || category || '未分类'
}

const getCategoryStyle = (category: string): string => {
  const c = category?.toUpperCase()
  if (c === 'TECH') return 'bg-cyan-50 text-cyan-700'
  if (c === 'FINANCE') return 'bg-amber-50 text-amber-700'
  if (c === 'HR') return 'bg-violet-50 text-violet-700'
  if (c === 'SECURITY') return 'bg-rose-50 text-rose-700'
  if (c === 'LEGAL') return 'bg-emerald-50 text-emerald-700'
  return 'bg-gray-100 text-gray-600'
}

const formatFileSize = (bytes?: number): string => {
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

const formatDateTime = (dtStr?: string): string => {
  if (!dtStr) return '-'
  return dtStr.replace('T', ' ').substring(0, 16)
}

const getPermissionBadgeStyle = (summary?: string): string => {
  if (!summary || summary.includes('全员公开')) {
    return 'bg-emerald-50 text-emerald-700 border border-emerald-200'
  }
  if (summary.includes('部门')) {
    return 'bg-sky-50 text-sky-700 border border-sky-200'
  }
  if (summary.includes('角色')) {
    return 'bg-purple-50 text-purple-700 border border-purple-200'
  }
  return 'bg-gray-100 text-gray-700 border border-gray-200'
}

const isActive = (status: string): boolean => {
  const s = status?.toUpperCase()
  return s === 'INDEXED' || s === 'AVAILABLE'
}

const isStatusToggleDisabled = (status: string): boolean => {
  const s = status?.toUpperCase()
  return s === 'PARSING' || s === 'CHUNKING' || s === 'PENDING' || s === 'FAILED'
}

const getStatusLabel = (status: string): string => {
  const map: Record<string, string> = {
    INDEXED: '已就绪',
    AVAILABLE: '已就绪',
    PARSING: '解析中',
    CHUNKING: '切片中',
    PENDING: '排队中',
    DISABLED: '已停用',
    FAILED: '解析失败'
  }
  return map[status?.toUpperCase()] || status
}

const getStatusDotClass = (status: string): string => {
  const s = status?.toUpperCase()
  if (s === 'INDEXED' || s === 'AVAILABLE') return 'bg-emerald-500'
  if (s === 'PARSING' || s === 'CHUNKING' || s === 'PENDING') return 'bg-blue-500 animate-pulse'
  if (s === 'DISABLED') return 'bg-gray-400'
  if (s === 'FAILED') return 'bg-rose-500'
  return 'bg-slate-400'
}

const getStatusTextClass = (status: string): string => {
  const s = status?.toUpperCase()
  if (s === 'INDEXED' || s === 'AVAILABLE') return 'text-emerald-700'
  if (s === 'PARSING' || s === 'CHUNKING' || s === 'PENDING') return 'text-blue-700'
  if (s === 'DISABLED') return 'text-gray-500'
  if (s === 'FAILED') return 'text-rose-600'
  return 'text-slate-600'
}

// 交互操作
const handleToggleStatus = async (unit: KnowledgeUnit) => {
  isUpdatingStatus.value = unit.id
  try {
    emit('toggle-status', unit)
  } finally {
    isUpdatingStatus.value = null
  }
}

const openDeleteDialog = (unit: KnowledgeUnit) => {
  unitToDelete.value = unit
}

const confirmDelete = async () => {
  if (!unitToDelete.value) return
  isDeleting.value = true
  try {
    emit('delete-unit', unitToDelete.value.id)
    unitToDelete.value = null
  } finally {
    isDeleting.value = false
  }
}

const changePage = (newPage: number) => {
  emit('page-change', newPage)
}

const onPageSizeChange = (event: Event) => {
  const target = event.target as HTMLSelectElement
  emit('page-size-change', Number(target.value))
}
</script>
