<template>
  <!-- FE-M4: 切片详情穿透预览抽屉 (PAGE-03 原型对齐) -->
  <div v-if="visible" class="fixed inset-0 z-50 overflow-hidden">
    <!-- Backdrop -->
    <div
      class="absolute inset-0 bg-black/30 backdrop-blur-[2px] transition-opacity"
      @click="emit('close')"
    ></div>

    <!-- Drawer Panel -->
    <div class="fixed inset-y-0 right-0 max-w-full flex pl-10">
      <div class="w-screen max-w-xl bg-white shadow-2xl flex flex-col border-l border-[#E5E7EB] animate-in slide-in-from-right duration-200">
        <!-- Header -->
        <div class="p-4 border-b border-[#F1F5F9] flex items-center justify-between bg-[#F8FAFC]">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-lg bg-blue-50 text-[#0071E3] flex items-center justify-center border border-blue-100">
              <Layers :size="16" />
            </div>
            <div>
              <h3 class="text-sm font-semibold text-[#0F172A] truncate max-w-sm">
                {{ unit?.title || '切片详情' }}
              </h3>
              <p class="text-[11px] text-[#64748B] font-mono mt-0.5">
                Unit ID: KU-{{ unit?.id }} · 共 {{ chunks.length }} 个切片分块
              </p>
            </div>
          </div>
          <button
            type="button"
            class="text-[#94A3B8] hover:text-[#0F172A] p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
            @click="emit('close')"
          >
            <X :size="16" />
          </button>
        </div>

        <!-- Content Body -->
        <div class="flex-1 overflow-y-auto p-4 space-y-3.5 bg-slate-50/50">
          <!-- Loading State -->
          <div v-if="loading" class="py-12 flex flex-col items-center justify-center gap-2 text-xs text-[#64748B]">
            <Loader2 :size="20" class="animate-spin text-[#0071E3]" />
            <span>正在检索向量切片明细...</span>
          </div>

          <!-- Empty State -->
          <div v-else-if="chunks.length === 0" class="py-12 text-center text-xs text-[#94A3B8]">
            暂无切片数据，文档可能正在分块流水线处理中
          </div>

          <!-- Chunk Cards List -->
          <div
            v-for="(chunk, idx) in chunks"
            :key="chunk.id || idx"
            class="bg-white rounded-xl border border-[#E2E8F0] p-3.5 shadow-sm hover:border-[#0071E3]/40 transition-colors space-y-2 text-xs"
          >
            <!-- Card Header -->
            <div class="flex items-center justify-between text-[11px] pb-2 border-b border-gray-100">
              <div class="flex items-center gap-2">
                <span class="font-mono font-semibold text-[#0071E3] bg-blue-50 px-2 py-0.5 rounded">
                  #{{ chunk.chunk_index !== undefined ? chunk.chunk_index : idx }}
                </span>
                <span class="text-[#64748B] font-mono">
                  长度: {{ chunk.char_length || chunk.content.length }} 字符
                </span>
              </div>
              <span
                class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium"
                :class="chunk.has_vector ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-700'"
              >
                <span class="w-1.5 h-1.5 rounded-full" :class="chunk.has_vector ? 'bg-emerald-500' : 'bg-amber-500'"></span>
                {{ chunk.has_vector ? '已向量化入库' : '未向量化' }}
              </span>
            </div>

            <!-- Content Preview -->
            <p class="text-[#334155] font-sans leading-relaxed whitespace-pre-wrap bg-slate-50/70 p-2.5 rounded-lg border border-slate-100 select-text">
              {{ chunk.content }}
            </p>

            <!-- Metadata tags -->
            <div v-if="chunk.metadata && Object.keys(chunk.metadata).length > 0" class="flex flex-wrap gap-1.5 pt-1">
              <span
                v-for="(val, key) in chunk.metadata"
                :key="key"
                class="inline-block text-[10px] font-mono bg-gray-100 text-gray-600 px-2 py-0.5 rounded"
              >
                {{ key }}: {{ val }}
              </span>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="p-3 border-t border-[#F1F5F9] bg-white flex justify-end">
          <button
            type="button"
            class="px-4 py-1.5 rounded-lg bg-gray-100 hover:bg-gray-200 text-xs font-medium text-[#475569] transition-colors"
            @click="emit('close')"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 切片穿透明细抽屉组件
 * 模块: FE-M4 (PAGE-03 原型对齐)
 */

import { ref, watch } from 'vue'
import { Layers, X, Loader2 } from 'lucide-vue-next'
import type { KnowledgeUnit, ChunkItem } from '@/types/knowledge'
import { getUnitChunksApi } from '@/api/knowledge'

const props = defineProps<{
  unit: KnowledgeUnit | null
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const chunks = ref<ChunkItem[]>([])
const loading = ref<boolean>(false)

watch(
  () => [props.visible, props.unit],
  async ([isVisible, unitVal]) => {
    if (isVisible && unitVal) {
      loading.value = true
      try {
        const res = await getUnitChunksApi((unitVal as KnowledgeUnit).id)
        chunks.value = res.data || []
      } catch (err) {
        console.error('获取切片失败:', err)
        chunks.value = []
      } finally {
        loading.value = false
      }
    } else {
      chunks.value = []
    }
  }
)
</script>
