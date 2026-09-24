/**
 * 组织架构、员工与角色权限 API
 * 模块: FE-M3 / M1: IAM
 * 严格对齐后端 StandardResponse 契约规范与 Axios 响应拦截器解包机制
 * 支持 VITE_ENABLE_MOCK=true/false 双态自由切换
 */

import request, { generateTraceId } from '@/utils/request'
import type { ApiResponse, PaginatedData, PaginationParams } from '@/types/common'
import type {
  DepartmentNode,
  UserItem,
  RoleItem,
  PermissionNode,
  DepartmentCreate,
  UserCreate,
  RoleCreate
} from '@/types/system'
import { mockDepartments, mockUsers, mockRoles, mockPermissionTree } from '@/mock/data'

const isMockEnabled = (): boolean => {
  return import.meta.env.VITE_ENABLE_MOCK === 'true'
}

// 内存中维护可变的 Mock 数据副本
let liveMockDepartments: DepartmentNode[] = JSON.parse(JSON.stringify(mockDepartments))
let liveMockUsers: UserItem[] = JSON.parse(JSON.stringify(mockUsers))
let liveMockRoles: RoleItem[] = JSON.parse(JSON.stringify(mockRoles))

// 部门架构 API
export const getDepartmentTreeApi = async (): Promise<ApiResponse<DepartmentNode[]>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 120))
    return {
      code: 200,
      message: 'success',
      data: JSON.parse(JSON.stringify(liveMockDepartments)),
      trace_id: generateTraceId()
    }
  }
  return request.get('/api/v1/departments/tree')
}

export const createDepartmentApi = async (payload: DepartmentCreate): Promise<ApiResponse<DepartmentNode>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 150))
    const newDept: DepartmentNode = {
      id: Date.now(),
      name: payload.name,
      code: payload.code || `DEPT_${Date.now()}`,
      parent_id: payload.parent_id,
      path: payload.parent_id ? `/1/${payload.parent_id}/${Date.now()}` : `/${Date.now()}`,
      materialized_path: payload.parent_id ? `/1/${payload.parent_id}/${Date.now()}` : `/${Date.now()}`,
      level: payload.parent_id ? 3 : 1,
      member_count: 0
    }

    const appendChild = (nodes: DepartmentNode[]): boolean => {
      for (const node of nodes) {
        if (node.id === payload.parent_id) {
          if (!node.children) node.children = []
          node.children.push(newDept)
          return true
        }
        if (node.children && appendChild(node.children)) return true
      }
      return false
    }

    if (!payload.parent_id || !appendChild(liveMockDepartments)) {
      liveMockDepartments.push(newDept)
    }

    return {
      code: 200,
      message: '部门创建成功',
      data: newDept,
      trace_id: generateTraceId()
    }
  }

  const sendData = {
    name: payload.name,
    code: payload.code || `DEPT_${Date.now().toString().slice(-6)}`,
    parent_id: payload.parent_id || null,
    sort_order: payload.sort_order || 0,
    leader_name: payload.leader_name,
    phone: payload.phone,
    email: payload.email
  }

  return request.post('/api/v1/departments', sendData)
}

// 员工台账 API
export const getUsersListApi = async (
  params: PaginationParams & { dept_id?: number | null; search?: string; keyword?: string }
): Promise<ApiResponse<PaginatedData<UserItem>>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 150))
    let filtered = [...liveMockUsers]

    if (params.dept_id) {
      filtered = filtered.filter((u) => (u.dept_id ?? u.department_id) === params.dept_id)
    }

    const kw = params.search || params.keyword
    if (kw && kw.trim()) {
      const q = kw.trim().toLowerCase()
      filtered = filtered.filter(
        (u) =>
          u.username.toLowerCase().includes(q) ||
          u.real_name.toLowerCase().includes(q) ||
          (u.email && u.email.toLowerCase().includes(q))
      )
    }

    const page = params.page || 1
    const pageSize = params.page_size || 10
    const start = (page - 1) * pageSize
    const paginatedItems = filtered.slice(start, start + pageSize)

    return {
      code: 200,
      message: 'success',
      data: {
        items: paginatedItems,
        total: filtered.length,
        page,
        page_size: pageSize
      },
      trace_id: generateTraceId()
    }
  }

  const queryParams: Record<string, unknown> = {
    page: params.page || 1,
    page_size: params.page_size || 10
  }
  if (params.dept_id) {
    queryParams.dept_id = params.dept_id
  }
  const kw = params.search || params.keyword
  if (kw && kw.trim()) {
    queryParams.keyword = kw.trim()
  }

  return request.get('/api/v1/users', { params: queryParams })
}

export const createUserApi = async (payload: UserCreate): Promise<ApiResponse<UserItem>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 150))
    const dept = findDeptName(liveMockDepartments, payload.dept_id ?? payload.department_id ?? 1)
    const newUser: UserItem = {
      id: Date.now(),
      employee_id: payload.employee_id || (payload.username.match(/^\d+$/) ? payload.username : 'EMP_' + Date.now().toString().slice(-5)),
      username: payload.username,
      real_name: payload.real_name,
      dept_id: payload.dept_id ?? payload.department_id ?? 1,
      dept_name: dept || '未分配部门',
      role_ids: payload.role_ids || [],
      role_names: (payload.role_ids || []).map((rid) => liveMockRoles.find((r) => r.id === rid)?.role_name || '自定义角色'),
      is_active: true,
      email: payload.email,
      phone: payload.phone,
      created_at: new Date().toISOString().replace('T', ' ').substring(0, 19)
    }
    liveMockUsers.unshift(newUser)

    return {
      code: 200,
      message: '员工创建成功',
      data: newUser,
      trace_id: generateTraceId()
    }
  }

  const sendData = {
    employee_id: payload.employee_id || (payload.username.match(/^\d+$/) ? payload.username : 'EMP_' + Date.now().toString().slice(-5)),
    username: payload.username,
    real_name: payload.real_name,
    password: payload.password || 'KnowGuard@2026',
    department_id: payload.department_id ?? payload.dept_id ?? 1,
    role_ids: payload.role_ids || [],
    email: payload.email,
    phone: payload.phone,
    is_active: true
  }

  return request.post('/api/v1/users', sendData)
}

export const toggleUserStatusApi = async (userId: number, isActive: boolean): Promise<ApiResponse<boolean>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 100))
    const target = liveMockUsers.find((u) => u.id === userId)
    if (!target) {
      throw new Error('未找到指定员工记录')
    }
    target.is_active = isActive
    return {
      code: 200,
      message: isActive ? '账号已启用' : '账号已停用',
      data: isActive,
      trace_id: generateTraceId()
    }
  }

  return request.patch(`/api/v1/users/${userId}/status`, { is_active: isActive })
}

export const resetUserPasswordApi = async (
  userId: number,
  newPassword: string = 'KnowGuard@2026'
): Promise<ApiResponse<UserItem>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 150))
    const target = liveMockUsers.find((u) => u.id === userId)
    if (!target) throw new Error('未找到指定员工记录')
    return {
      code: 200,
      message: `员工密码重置成功，新密码已生效: ${newPassword}`,
      data: target,
      trace_id: generateTraceId()
    }
  }

  return request.post(`/api/v1/users/${userId}/reset-password`, { password: newPassword })
}

// 角色与权限 API
export const getRolesListApi = async (): Promise<ApiResponse<RoleItem[]>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 120))
    return {
      code: 200,
      message: 'success',
      data: JSON.parse(JSON.stringify(liveMockRoles)),
      trace_id: generateTraceId()
    }
  }

  return request.get('/api/v1/roles')
}

export const createRoleApi = async (payload: RoleCreate): Promise<ApiResponse<RoleItem>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 150))
    const newRole: RoleItem = {
      id: Date.now(),
      role_name: payload.role_name || payload.name || '',
      name: payload.name || payload.role_name,
      role_code: payload.role_code || payload.code || '',
      code: payload.code || payload.role_code,
      description: payload.description,
      user_count: 0,
      permissions: payload.permissions || payload.permission_codes || []
    }
    liveMockRoles.push(newRole)
    return {
      code: 200,
      message: '角色创建成功',
      data: newRole,
      trace_id: generateTraceId()
    }
  }

  const sendData = {
    name: payload.name || payload.role_name,
    code: payload.code || payload.role_code,
    description: payload.description,
    status: true,
    permission_codes: payload.permission_codes || payload.permissions || []
  }

  return request.post('/api/v1/roles', sendData)
}

export const getPermissionTreeApi = async (): Promise<ApiResponse<PermissionNode[]>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 100))
    return {
      code: 200,
      message: 'success',
      data: JSON.parse(JSON.stringify(mockPermissionTree)),
      trace_id: generateTraceId()
    }
  }

  return request.get('/api/v1/roles/permissions/tree')
}

export const updateRolePermissionsApi = async (
  roleId: number,
  permissions: string[]
): Promise<ApiResponse<RoleItem>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 180))
    const target = liveMockRoles.find((r) => r.id === roleId)
    if (!target) throw new Error('角色不存在')
    target.permissions = [...permissions]
    target.permission_codes = [...permissions]
    return {
      code: 200,
      message: '权限配置保存成功，下发即刻生效',
      data: target,
      trace_id: generateTraceId()
    }
  }

  return request.put(`/api/v1/roles/${roleId}/permissions`, {
    permission_codes: permissions,
    permissions: permissions
  })
}

// 辅助工具函数
function findDeptName(nodes: DepartmentNode[], id: number): string | null {
  for (const n of nodes) {
    if (n.id === id) return n.name
    if (n.children) {
      const childRes = findDeptName(n.children, id)
      if (childRes) return childRes
    }
  }
  return null
}
