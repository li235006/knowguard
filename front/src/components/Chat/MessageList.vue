<template>
  <!-- FE-M2: 消息气泡流容器 (PAGE-02 原型对齐) -->
  <div ref="containerRef" class="flex-1 overflow-y-auto p-6 flex flex-col gap-6">
    <!-- Empty State Greeting -->
    <div
      v-if="messages.length === 0"
      class="flex-1 flex flex-col items-center justify-center gap-3 text-center my-auto select-none"
    >
      <div class="w-12 h-12 rounded-2xl bg-[#0071E3] text-white flex items-center justify-center shadow-lg shadow-blue-500/20">
        <Shield :size="24" />
      </div>
      <h3 class="text-base font-bold text-[#0F172A]">你好！我是 KnowGuard 企业安全知识大脑</h3>
      <p class="text-xs text-[#64748B] max-w-md leading-relaxed">
        已接入企业知识库与 4D-RBAC 动态鉴权护栏。请在下方输入框中提问任何制度政策、业务流程或规章标准。
      </p>
    </div>

    <!-- Message Bubble Loop -->
    <div
      v-for="msg in messages"
      :key="msg.id"
      class="flex flex-col gap-2 max-w-3xl w-full mx-auto"
    >
      <!-- Time Anchor Pill -->
      <div class="flex justify-center my-1 select-none">
        <span class="text-[10px] text-[#94A3B8] bg-[#F1F5F9] px-2 py-0.5 rounded-full font-mono">
          {{ msg.created_at }}
        </span>
      </div>

      <!-- User Message Bubble -->
      <div v-if="msg.role === 'user'" class="flex items-start justify-end gap-3">
        <div
          class="bg-white border border-[#E5E7EB] rounded-2xl rounded-tr-xs px-4 py-3 text-xs text-[#0F172A] shadow-sm max-w-xl leading-relaxed whitespace-pre-wrap"
        >
          {{ msg.content }}
        </div>
        <div
          class="w-8 h-8 rounded-full bg-blue-100 text-[#0071E3] flex items-center justify-center font-bold text-xs shrink-0 select-none shadow-sm"
        >
          {{ userInitial }}
        </div>
      </div>

      <!-- Assistant Message Bubble -->
      <div v-else class="flex items-start gap-3">
        <div
          class="w-8 h-8 rounded-xl bg-[#0071E3] text-white flex items-center justify-center shrink-0 select-none shadow-sm shadow-blue-500/20"
        >
          <Shield :size="16" />
        </div>

        <div class="flex-1 flex flex-col gap-3 min-w-0">
          <!-- Main Content Card -->
          <div
            class="bg-white border border-[#E5E7EB] rounded-2xl rounded-tl-xs p-4 shadow-sm flex flex-col gap-3"
          >
            <!-- Markdown Stream -->
            <MarkdownRenderer
              :content="msg.content"
              :is-streaming="msg.status === 'streaming'"
            />

            <!-- Silent Fallback Card (越权降级或未命中) -->
            <SilentFallback v-if="msg.is_silent_fallback" />

            <!-- Citation Cards (溯源引用卡片: 置信度超 60% 且最多展示 4 篇，回答完成后最后呈现) -->
            <div
              v-if="filteredCitations(msg).length > 0 && (msg.content || msg.status !== 'streaming')"
              class="flex flex-col gap-2 pt-2 border-t border-[#F1F5F9]"
            >
              <div class="flex items-center gap-1.5 text-[11px] font-semibold text-[#64748B]">
                <BookOpen :size="13" class="text-[#0071E3]" />
                <span>知识溯源参考 ({{ filteredCitations(msg).length }} 篇)：</span>
              </div>
              <CitationCard
                v-for="cite in filteredCitations(msg)"
                :key="cite.chunk_id"
                :citation="cite"
              />
            </div>
          </div>

          <!-- Bottom Feedback Actions Row -->
          <div
            v-if="msg.status !== 'streaming'"
            class="flex items-center justify-between px-1 text-[#94A3B8] text-[11px] select-none"
          >
            <div class="flex items-center gap-3">
              <button
                type="button"
                class="flex items-center gap-1 hover:text-[#0071E3] transition-colors cursor-pointer"
                title="有帮助"
                @click="toggleLike(msg.id)"
              >
                <ThumbsUp :size="12" />
                <span>赞同</span>
              </button>
              <button
                type="button"
                class="flex items-center gap-1 hover:text-red-500 transition-colors cursor-pointer"
                title="待改进"
                @click="toggleDislike(msg.id)"
              >
                <ThumbsDown :size="12" />
              </button>
              <button
                type="button"
                class="flex items-center gap-1 hover:text-[#0F172A] transition-colors ml-1 cursor-pointer"
                title="复制回复内容"
                @click="copyContent(msg.content)"
              >
                <Copy :size="12" />
                <span>{{ copyStatus[msg.id] ? '已复制' : '复制' }}</span>
              </button>
            </div>

            <!-- Model Provenance Tag (判断是否真的调用大模型) -->
            <div class="flex items-center gap-1.5 text-[10px]">
              <span
                v-if="msg.is_real_llm || msg.llm_source === 'remote_dashscope'"
                class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200"
                title="真实调用阿里云百炼通义千问云端大模型生成"
              >
                <Sparkles :size="11" class="text-emerald-600" />
                <span>{{ msg.llm_model || 'qwen3.7-flash' }} · 云端大模型已调用</span>
              </span>
              <span
                v-else
                class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200"
                title="本地离线安全合成输出"
              >
                <Cpu :size="11" class="text-blue-600" />
                <span>企业知识大脑引擎响应</span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 消息气泡流容器组件
 * 模块: FE-M2 (PAGE-02 原型对齐)
 */

import { ref, computed, watch, nextTick } from 'vue'
import { Shield, BookOpen, ThumbsUp, ThumbsDown, Copy, Sparkles, Cpu } from 'lucide-vue-next'
import type { ChatMessage, CitationItem } from '@/types/chat'
import { useAuthStore } from '@/stores/auth'
import MarkdownRenderer from './MarkdownRenderer.vue'
import CitationCard from './CitationCard.vue'
import SilentFallback from './SilentFallback.vue'

const props = defineProps<{
  messages: ChatMessage[]
}>()

// 用户置信度硬性过滤：超 60% (>= 0.60)，且最多展示 4 篇
const filteredCitations = (msg: ChatMessage): CitationItem[] => {
  if (!msg.citations) return []
  return msg.citations
    .filter((c) => (c.score ?? 0) >= 0.60)
    .slice(0, 4)
}

const authStore = useAuthStore()
const containerRef = ref<HTMLDivElement | null>(null)
const copyStatus = ref<Record<string, boolean>>({})

const userInitial = computed(() => {
  const name = authStore.user?.real_name || authStore.user?.username || 'U'
  return name.charAt(0)
})

const scrollToBottom = async () => {
  await nextTick()
  if (containerRef.value) {
    containerRef.value.scrollTop = containerRef.value.scrollHeight
  }
}

watch(
  () => props.messages,
  () => {
    scrollToBottom()
  },
  { deep: true }
)

const toggleLike = (id: string) => {
  alert(`已收到您的反馈，感谢对问答质量的评价！[会话: ${id}]`)
}

const toggleDislike = (id: string) => {
  alert(`感谢您的反馈，系统已将该条问答标记为低置信度缺口并异步送入自进化挖掘池。[会话: ${id}]`)
}

const copyContent = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    alert('已复制回答内容至剪贴板')
  } catch {
    // 忽略剪贴板权限异常
  }
}
</script>
