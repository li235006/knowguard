/**
 * 知识资产管理状态仓库 (Knowledge Store)
 * 模块: FE-M4
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { KnowledgeUnit } from '@/types/knowledge'

export const useKnowledgeStore = defineStore('knowledge', () => {
  const units = ref<KnowledgeUnit[]>([])

  return { units }
})
