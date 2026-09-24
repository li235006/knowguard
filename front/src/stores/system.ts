/**
 * 组织架构、员工与角色状态仓库 (System Store)
 * 模块: FE-M3
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { DepartmentNode, UserItem, RoleItem, PermissionNode } from '@/types/system'
import {
  getDepartmentTreeApi,
  getUsersListApi,
  getRolesListApi,
  getPermissionTreeApi,
  toggleUserStatusApi,
  updateRolePermissionsApi
} from '@/api/system'

export const useSystemStore = defineStore('system', () => {
  const departmentTree = ref<DepartmentNode[]>([])
  const selectedDeptId = ref<number | null>(null)
  const users = ref<UserItem[]>([])
  const totalUsers = ref<number>(0)
  const roles = ref<RoleItem[]>([])
  const permissionTree = ref<PermissionNode[]>([])
  const isLoading = ref<boolean>(false)

  const fetchDepartmentTree = async () => {
    isLoading.value = true
    try {
      const res = await getDepartmentTreeApi()
      if (res.data) {
        departmentTree.value = res.data
      }
    } finally {
      isLoading.value = false
    }
  }

  const fetchUsers = async (params: { page?: number; page_size?: number; search?: string } = {}) => {
    isLoading.value = true
    try {
      const res = await getUsersListApi({
        page: params.page || 1,
        page_size: params.page_size || 10,
        dept_id: selectedDeptId.value,
        search: params.search
      })
      if (res.data) {
        users.value = res.data.items
        totalUsers.value = res.data.total
      }
    } finally {
      isLoading.value = false
    }
  }

  const fetchRoles = async () => {
    isLoading.value = true
    try {
      const res = await getRolesListApi()
      if (res.data) {
        roles.value = res.data
      }
    } finally {
      isLoading.value = false
    }
  }

  const fetchPermissionTree = async () => {
    try {
      const res = await getPermissionTreeApi()
      if (res.data) {
        permissionTree.value = res.data
      }
    } catch {
      // handled
    }
  }

  const toggleUserStatus = async (userId: number, isActive: boolean) => {
    const res = await toggleUserStatusApi(userId, isActive)
    if (res.data) {
      const target = users.value.find((u) => u.id === userId)
      if (target) {
        target.is_active = res.data.is_active
      }
    }
  }

  const updateRolePermissions = async (roleId: number, permissions: string[]) => {
    const res = await updateRolePermissionsApi(roleId, permissions)
    if (res.data) {
      const target = roles.value.find((r) => r.id === roleId)
      if (target) {
        target.permissions = [...res.data.permissions]
      }
    }
  }

  const selectDepartment = (deptId: number | null) => {
    selectedDeptId.value = deptId
    fetchUsers({ page: 1, page_size: 10 })
  }

  return {
    departmentTree,
    selectedDeptId,
    users,
    totalUsers,
    roles,
    permissionTree,
    isLoading,
    fetchDepartmentTree,
    fetchUsers,
    fetchRoles,
    fetchPermissionTree,
    toggleUserStatus,
    updateRolePermissions,
    selectDepartment
  }
})

