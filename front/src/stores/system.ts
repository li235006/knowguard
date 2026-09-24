/**
 * 组织架构、员工与角色状态仓库 (System Store)
 * 模块: FE-M3
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import type {
  DepartmentNode,
  UserItem,
  RoleItem,
  PermissionNode,
  DepartmentCreate,
  UserCreate,
  RoleCreate
} from '@/types/system'
import {
  getDepartmentTreeApi,
  createDepartmentApi,
  getUsersListApi,
  createUserApi,
  resetUserPasswordApi,
  getRolesListApi,
  createRoleApi,
  getPermissionTreeApi,
  toggleUserStatusApi,
  updateRolePermissionsApi
} from '@/api/system'

export const useSystemStore = defineStore('system', () => {
  const departmentTree = ref<DepartmentNode[]>([])
  const selectedDeptId = ref<number | null>(null)
  const users = ref<UserItem[]>([])
  const totalUsers = ref<number>(0)
  const currentPage = ref<number>(1)
  const currentPageSize = ref<number>(10)
  const searchKeyword = ref<string>('')
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

  const createDepartment = async (payload: DepartmentCreate): Promise<DepartmentNode> => {
    const res = await createDepartmentApi(payload)
    if (!res.data) throw new Error(res.message || '创建部门失败')
    await fetchDepartmentTree()
    return res.data
  }

  const fetchUsers = async (params: { page?: number; page_size?: number; search?: string } = {}) => {
    isLoading.value = true
    try {
      if (params.page !== undefined) currentPage.value = params.page
      if (params.page_size !== undefined) currentPageSize.value = params.page_size
      if (params.search !== undefined) searchKeyword.value = params.search

      const res = await getUsersListApi({
        page: currentPage.value,
        page_size: currentPageSize.value,
        dept_id: selectedDeptId.value,
        search: searchKeyword.value
      })
      if (res.data) {
        users.value = res.data.items
        totalUsers.value = res.data.total
      }
    } finally {
      isLoading.value = false
    }
  }

  const createUser = async (payload: UserCreate): Promise<UserItem> => {
    const res = await createUserApi(payload)
    if (!res.data) throw new Error(res.message || '创建员工失败')
    await fetchUsers()
    return res.data
  }

  const resetUserPassword = async (userId: number, newPassword?: string): Promise<string> => {
    const res = await resetUserPasswordApi(userId, newPassword)
    return res.message || '密码重置成功'
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

  const createRole = async (payload: RoleCreate): Promise<RoleItem> => {
    const res = await createRoleApi(payload)
    if (!res.data) throw new Error(res.message || '创建角色失败')
    await fetchRoles()
    return res.data
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
    if (res && res.code === 200) {
      const target = users.value.find((u) => u.id === userId)
      if (target) {
        target.is_active = typeof res.data === 'boolean' ? res.data : isActive
      }
    }
  }

  const updateRolePermissions = async (roleId: number, permissions: string[]) => {
    const res = await updateRolePermissionsApi(roleId, permissions)
    if (res.data) {
      const target = roles.value.find((r) => r.id === roleId)
      if (target) {
        target.permissions = [...(res.data.permissions || permissions)]
        target.permission_codes = [...(res.data.permission_codes || permissions)]
      }
    }
  }

  const selectDepartment = (deptId: number | null) => {
    selectedDeptId.value = deptId
    currentPage.value = 1
    fetchUsers({ page: 1, page_size: currentPageSize.value })
  }

  return {
    departmentTree,
    selectedDeptId,
    users,
    totalUsers,
    currentPage,
    currentPageSize,
    searchKeyword,
    roles,
    permissionTree,
    isLoading,
    fetchDepartmentTree,
    createDepartment,
    fetchUsers,
    createUser,
    resetUserPassword,
    fetchRoles,
    createRole,
    fetchPermissionTree,
    toggleUserStatus,
    updateRolePermissions,
    selectDepartment
  }
})
