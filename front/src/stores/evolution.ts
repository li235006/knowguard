/**
 * 知识自进化工作台状态仓库 (Evolution Store)
 * 模块: FE-M5
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useEvolutionStore = defineStore('evolution', () => {
  const pendingCandidatesCount = ref<number>(0)

  return { pendingCandidatesCount }
})
