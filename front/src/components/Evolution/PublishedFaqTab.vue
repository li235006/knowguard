<template>
  <!-- FE-M5: 已发布 FAQ 库与缓存开关维护 (PAGE-06) -->
  <div class="space-y-4">
    <!-- Header Tool & Filter Bar -->
    <div class="flex flex-wrap items-center justify-between gap-3 bg-white p-3.5 rounded-xl border border-[#E5E7EB] shadow-sm">
      <div class="flex items-center gap-2">
        <span class="text-xs font-semibold text-[#0F172A] flex items-center gap-1.5">
          <Layers :size="14" class="text-[#0071E3]" />
          <span>标准 FAQ 知识库</span>
        </span>
        <span class="text-[11px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium">
          共 {{ evolutionStore.totalPublishedFaqs }} 条沉淀问答
        </span>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <!-- Category Filter -->
        <select
          v-model="evolutionStore.selectedCategory"
          class="bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-2.5 py-1 text-xs text-[#0F172A] focus:outline-none focus:border-[#0071E3]"
          @change="handleCategoryChange"
        >
          <option value="ALL">全部业务分类</option>
          <option value="产品介绍">产品介绍</option>
          <option value="薪酬福利">薪酬福利</option>
          <option value="IT运维">IT运维</option>
          <option value="合规风控">合规风控</option>
          <option value="技术创新">技术创新</option>
          <option value="通用">通用分类</option>
        </select>

        <!-- Create FAQ Button -->
        <button
          type="button"
          class="px-3 py-1.5 bg-[#0071E3] hover:bg-[#0077ED] text-white rounded-lg text-xs font-medium inline-flex items-center gap-1.5 transition-colors shadow-sm"
          @click="openCreateFaqModal"
        >
          <Plus :size="13" />
          <span>直接发布 FAQ</span>
        </button>
      </div>
    </div>

    <!-- Published FAQs Table Card -->
    <div class="bg-white rounded-xl border border-[#E5E7EB] shadow-sm overflow-hidden flex flex-col">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs border-collapse">
          <thead>
            <tr class="bg-[#F8FAFC] text-[#64748B] border-b border-[#F1F5F9] font-medium text-[11px]">
              <th class="py-3 px-4 w-16">ID</th>
              <th class="py-3 px-4 min-w-[240px]">标准问题与回答</th>
              <th class="py-3 px-4 w-28">业务分类</th>
              <th class="py-3 px-4 w-36 text-center">极速缓存直出 (&lt;50ms)</th>
              <th class="py-3 px-4 w-24 text-center">命中次数</th>
              <th class="py-3 px-4 w-28 text-center">启停维护</th>
              <th class="py-3 px-4 w-32">更新时间</th>
              <th class="py-3 px-4 w-28 text-right">操作</th>
            </tr>
          </thead>

          <tbody v-if="evolutionStore.isLoading" class="divide-y divide-[#F1F5F9]">
            <tr v-for="i in 5" :key="i" class="animate-pulse">
              <td colspan="8" class="py-4 px-4">
                <div class="h-4 bg-gray-100 rounded w-full"></div>
              </td>
            </tr>
          </tbody>

          <tbody v-else-if="evolutionStore.publishedFaqs.length > 0" class="divide-y divide-[#F1F5F9]">
            <tr
              v-for="faq in evolutionStore.publishedFaqs"
              :key="faq.id"
              class="hover:bg-[#F8FAFC] transition-colors"
            >
              <!-- ID -->
              <td class="py-3 px-4 text-[#94A3B8] font-mono text-[11px]">
                #{{ faq.id }}
              </td>

              <!-- Question & Answer -->
              <td class="py-3 px-4">
                <div class="flex flex-col gap-1 max-w-[420px]">
                  <div class="font-semibold text-[#0F172A] leading-snug flex items-start gap-1.5">
                    <HelpCircle :size="13" class="text-[#0071E3] shrink-0 mt-0.5" />
                    <span>{{ faq.standard_question }}</span>
                  </div>
                  <div class="text-[11px] text-[#475569] line-clamp-2 pl-4">
                    {{ faq.standard_answer }}
                  </div>
                  <div v-if="faq.similar_questions && faq.similar_questions.length > 0" class="flex flex-wrap gap-1 pl-4 mt-0.5">
                    <span
                      v-for="(sim, sIdx) in faq.similar_questions.slice(0, 2)"
                      :key="sIdx"
                      class="text-[10px] px-1.5 py-0.2 rounded bg-slate-100 text-slate-500 font-mono"
                    >
                      ~ {{ sim }}
                    </span>
                    <span v-if="faq.similar_questions.length > 2" class="text-[10px] text-slate-400">
                      +{{ faq.similar_questions.length - 2 }}个别名
                    </span>
                  </div>
                </div>
              </td>

              <!-- Category -->
              <td class="py-3 px-4">
                <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200">
                  {{ faq.category || '通用' }}
                </span>
              </td>

              <!-- Cache Switch -->
              <td class="py-3 px-4 text-center">
                <div class="inline-flex items-center justify-center gap-1.5">
                  <label class="relative inline-flex items-center cursor-pointer select-none">
                    <input
                      type="checkbox"
                      :checked="faq.is_cached"
                      class="sr-only peer"
                      @change="handleToggleCache(faq)"
                    />
                    <div
                      class="w-7 h-4 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-emerald-500"
                    ></div>
                  </label>
                  <span
                    class="text-[10px] font-mono"
                    :class="faq.is_cached ? 'text-emerald-600 font-semibold' : 'text-slate-400'"
                  >
                    {{ faq.is_cached ? 'Redis直出' : '已关闭' }}
                  </span>
                </div>
              </td>

              <!-- Hit Count -->
              <td class="py-3 px-4 text-center">
                <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-mono font-medium bg-blue-50 text-[#0071E3] border border-blue-100">
                  <Zap :size="11" class="text-amber-500 shrink-0" />
                  <span>{{ (faq.hit_count || 0).toLocaleString() }} 次</span>
                </span>
              </td>

              <!-- Enable Switch -->
              <td class="py-3 px-4 text-center">
                <div class="inline-flex items-center justify-center gap-1.5">
                  <label class="relative inline-flex items-center cursor-pointer select-none">
                    <input
                      type="checkbox"
                      :checked="faq.is_enabled"
                      class="sr-only peer"
                      @change="handleToggleStatus(faq)"
                    />
                    <div
                      class="w-7 h-4 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-[#0071E3]"
                    ></div>
                  </label>
                  <span
                    class="text-[11px] font-medium"
                    :class="faq.is_enabled ? 'text-[#16A34A]' : 'text-gray-400'"
                  >
                    {{ faq.is_enabled ? '正常' : '已停用' }}
                  </span>
                </div>
              </td>

              <!-- Updated At -->
              <td class="py-3 px-4 text-[#94A3B8] font-mono text-[11px] whitespace-nowrap">
                {{ formatDateTime(faq.updated_at || faq.created_at) }}
              </td>

              <!-- Actions -->
              <td class="py-3 px-4 text-right whitespace-nowrap">
                <div class="flex items-center justify-end gap-2">
                  <button
                    type="button"
                    class="text-[11px] text-[#0071E3] hover:underline font-medium inline-flex items-center gap-0.5"
                    @click="openEditModal(faq)"
                  >
                    <Edit3 :size="11" />
                    <span>编辑</span>
                  </button>
                  <button
                    type="button"
                    class="text-[11px] text-rose-500 hover:text-rose-700 hover:underline font-medium inline-flex items-center gap-0.5"
                    @click="handleDelete(faq)"
                  >
                    <Trash2 :size="11" />
                    <span>删除</span>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>

          <!-- Empty State -->
          <tbody v-else>
            <tr>
              <td colspan="8" class="py-16 text-center text-[#94A3B8]">
                <div class="flex flex-col items-center gap-2">
                  <div class="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-slate-400">
                    <Inbox :size="24" />
                  </div>
                  <span class="font-medium text-slate-600">未找到符合条件的 FAQ 知识记录</span>
                  <span class="text-slate-400 text-[11px]">可切换业务分类或点击“直接发布 FAQ”创建</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div
        v-if="evolutionStore.totalPublishedFaqs > evolutionStore.faqsPageSize"
        class="p-3 border-t border-[#F1F5F9] bg-[#FAFAFA]/60 flex items-center justify-between text-xs text-[#64748B]"
      >
        <div>
          共 <span class="font-medium text-[#0F172A]">{{ evolutionStore.totalPublishedFaqs }}</span> 条问答
        </div>
        <div class="flex items-center gap-2">
          <button
            type="button"
            :disabled="evolutionStore.faqsPage <= 1"
            class="px-2.5 py-1 border border-[#E5E7EB] rounded bg-white hover:bg-gray-50 disabled:opacity-40 transition-colors"
            @click="changePage(evolutionStore.faqsPage - 1)"
          >
            上一页
          </button>
          <span class="px-2 font-mono text-[#0F172A]">第 {{ evolutionStore.faqsPage }} 页</span>
          <button
            type="button"
            :disabled="evolutionStore.faqsPage * evolutionStore.faqsPageSize >= evolutionStore.totalPublishedFaqs"
            class="px-2.5 py-1 border border-[#E5E7EB] rounded bg-white hover:bg-gray-50 disabled:opacity-40 transition-colors"
            @click="changePage(evolutionStore.faqsPage + 1)"
          >
            下一页
          </button>
        </div>
      </div>
    </div>

    <!-- Create or Edit FAQ Modal -->
    <div
      v-if="showFaqModal"
      class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-200"
    >
      <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-gray-100 flex flex-col gap-4 text-xs">
        <div class="flex items-center justify-between border-b border-[#F1F5F9] pb-3">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-lg bg-blue-50 text-[#0071E3] flex items-center justify-center border border-blue-100">
              <HelpCircle :size="16" />
            </div>
            <div>
              <h3 class="font-semibold text-sm text-[#0F172A]">
                {{ editingFaqId ? '编辑标准 FAQ 问答' : '手动直接发布标准 FAQ' }}
              </h3>
              <p class="text-[11px] text-[#64748B]">配置标准问题、解答要点、归属分类与极速缓存策略</p>
            </div>
          </div>
          <button type="button" class="text-gray-400 hover:text-gray-600 p-1 rounded-lg" @click="showFaqModal = false">
            <X :size="16" />
          </button>
        </div>

        <div class="flex flex-col gap-3">
          <!-- Standard Question -->
          <div class="flex flex-col gap-1">
            <label class="font-medium text-[#475569]">标准提问 *</label>
            <input
              v-model="faqForm.standard_question"
              type="text"
              placeholder="例如: 员工如何申领办公笔记本电脑？"
              class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-3 py-2 text-xs text-[#0F172A] focus:outline-none focus:border-[#0071E3]"
            />
          </div>

          <!-- Category -->
          <div class="flex flex-col gap-1">
            <label class="font-medium text-[#475569]">归属业务分类</label>
            <input
              v-model="faqForm.category"
              type="text"
              placeholder="例如: IT运维 / 薪酬福利 / 合规风控"
              class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-3 py-2 text-xs text-[#0F172A] focus:outline-none focus:border-[#0071E3]"
            />
          </div>

          <!-- Standard Answer -->
          <div class="flex flex-col gap-1">
            <label class="font-medium text-[#475569]">标准回答正文 *</label>
            <textarea
              v-model="faqForm.standard_answer"
              rows="4"
              placeholder="准确详尽地陈述回答内容，支持排版规范..."
              class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-3 py-2 text-xs text-[#0F172A] focus:outline-none focus:border-[#0071E3]"
            ></textarea>
          </div>

          <!-- Similar Questions -->
          <div class="flex flex-col gap-1">
            <label class="font-medium text-[#475569]">类似提问别名 (换行或英文逗号分隔)</label>
            <textarea
              v-model="faqForm.similarQuestionsText"
              rows="2"
              placeholder="领电脑找谁, 电脑坏了申请换新, 笔记本领用流程"
              class="w-full bg-[#F8FAFC] border border-[#E5E7EB] rounded-lg px-3 py-2 text-xs text-[#0F172A] focus:outline-none focus:border-[#0071E3]"
            ></textarea>
          </div>

          <!-- Cache Toggle -->
          <div class="flex items-center justify-between p-3 rounded-xl bg-[#F8FAFC] border border-[#E5E7EB]">
            <div>
              <div class="font-medium text-slate-800 flex items-center gap-1.5">
                <Zap :size="13" class="text-amber-500" />
                <span>预热至前置 Redis 极速缓存</span>
              </div>
              <p class="text-[11px] text-slate-400">开启后，相似提问命中率高的问题将在 &lt; 50ms 优先秒级直出</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer select-none">
              <input
                v-model="faqForm.is_cached"
                type="checkbox"
                class="sr-only peer"
              />
              <div
                class="w-8 h-4 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-emerald-500"
              ></div>
            </label>
          </div>
        </div>

        <div class="flex items-center justify-end gap-2 pt-2 border-t border-[#F1F5F9]">
          <button
            type="button"
            class="px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-100 rounded-lg transition-colors font-medium"
            @click="showFaqModal = false"
          >
            取消
          </button>
          <button
            type="button"
            :disabled="!faqForm.standard_question.trim() || !faqForm.standard_answer.trim() || isSubmitting"
            class="px-4 py-1.5 text-xs bg-[#0071E3] hover:bg-[#0077ED] text-white rounded-lg font-medium transition-colors disabled:opacity-50 inline-flex items-center gap-1.5 shadow-sm"
            @click="submitFaqForm"
          >
            <span>{{ isSubmitting ? '保存中...' : (editingFaqId ? '更新 FAQ' : '确认发布') }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 已发布 FAQ 库与缓存直出维护组件
 * 模块: FE-M5 (PAGE-06)
 */

import { ref, reactive } from 'vue'
import {
  Layers,
  Plus,
  HelpCircle,
  Zap,
  Edit3,
  Trash2,
  Inbox,
  X
} from 'lucide-vue-next'
import { useEvolutionStore } from '@/stores/evolution'
import type { FaqItem } from '@/types/evolution'

const evolutionStore = useEvolutionStore()

const emit = defineEmits<{
  (e: 'toast', msg: string, type?: 'success' | 'error'): void
}>()

const showFaqModal = ref(false)
const editingFaqId = ref<number | null>(null)
const isSubmitting = ref(false)

const faqForm = reactive({
  standard_question: '',
  standard_answer: '',
  category: '通用',
  similarQuestionsText: '',
  is_cached: true
})

const handleCategoryChange = () => {
  evolutionStore.fetchPublishedFaqs(1)
}

const changePage = (page: number) => {
  evolutionStore.fetchPublishedFaqs(page)
}

const handleToggleStatus = async (faq: FaqItem) => {
  const nextStatus = !faq.is_enabled
  try {
    await evolutionStore.toggleFaqStatus(faq.id, nextStatus)
    emit('toast', nextStatus ? `FAQ [${faq.standard_question}] 已启用` : `FAQ [${faq.standard_question}] 已停用维护`, 'success')
  } catch (err) {
    emit('toast', err instanceof Error ? err.message : '切换状态失败', 'error')
  }
}

const handleToggleCache = async (faq: FaqItem) => {
  const nextCache = !faq.is_cached
  try {
    await evolutionStore.toggleFaqCache(faq.id, nextCache)
    emit('toast', nextCache ? '已开启极速缓存直出 (< 50ms)' : '已关闭极速缓存', 'success')
  } catch (err) {
    emit('toast', err instanceof Error ? err.message : '切换缓存失败', 'error')
  }
}

const openCreateFaqModal = () => {
  editingFaqId.value = null
  faqForm.standard_question = ''
  faqForm.standard_answer = ''
  faqForm.category = '通用'
  faqForm.similarQuestionsText = ''
  faqForm.is_cached = true
  showFaqModal.value = true
}

const openEditModal = (faq: FaqItem) => {
  editingFaqId.value = faq.id
  faqForm.standard_question = faq.standard_question
  faqForm.standard_answer = faq.standard_answer
  faqForm.category = faq.category || '通用'
  faqForm.similarQuestionsText = (faq.similar_questions || []).join(', ')
  faqForm.is_cached = faq.is_cached
  showFaqModal.value = true
}

const submitFaqForm = async () => {
  if (!faqForm.standard_question.trim() || !faqForm.standard_answer.trim()) return
  isSubmitting.value = true
  const simList = faqForm.similarQuestionsText
    .split(/[,，\n]/)
    .map((s) => s.trim())
    .filter(Boolean)

  try {
    if (editingFaqId.value) {
      await evolutionStore.updateFaq(editingFaqId.value, {
        standard_question: faqForm.standard_question.trim(),
        standard_answer: faqForm.standard_answer.trim(),
        category: faqForm.category.trim() || '通用',
        similar_questions: simList,
        is_cached: faqForm.is_cached
      })
      emit('toast', 'FAQ 更新成功', 'success')
    } else {
      await evolutionStore.publishFaq({
        standard_question: faqForm.standard_question.trim(),
        standard_answer: faqForm.standard_answer.trim(),
        category: faqForm.category.trim() || '通用',
        similar_questions: simList,
        is_cached: faqForm.is_cached,
        is_enabled: true
      })
      emit('toast', '新 FAQ 发布成功并已注入缓存', 'success')
    }
    showFaqModal.value = false
  } catch (err) {
    emit('toast', err instanceof Error ? err.message : '保存失败', 'error')
  } finally {
    isSubmitting.value = false
  }
}

const handleDelete = async (faq: FaqItem) => {
  if (!confirm(`确定彻底删除该 FAQ 词条：“${faq.standard_question}”？`)) return
  try {
    await evolutionStore.deleteFaq(faq.id)
    emit('toast', 'FAQ 已成功删除', 'success')
  } catch (err) {
    emit('toast', err instanceof Error ? err.message : '删除失败', 'error')
  }
}

const formatDateTime = (dtStr?: string): string => {
  if (!dtStr) return '-'
  return dtStr.replace('T', ' ').substring(0, 16)
}
</script>
