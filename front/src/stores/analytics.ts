/**
 * 运营监控大盘状态仓库 (Analytics Store)
 * 模块: FE-M6
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAnalyticsStore = defineStore('analytics', () => {
  const summary = ref<any>(null)

  return { summary }
})
