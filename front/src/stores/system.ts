/**
 * 组织架构、员工与角色状态仓库 (System Store)
 * 模块: FE-M3
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { DepartmentNode } from '@/types/system'

export const useSystemStore = defineStore('system', () => {
  const departmentTree = ref<DepartmentNode[]>([])

  return { departmentTree }
})
