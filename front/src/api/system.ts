/**
 * 组织架构、员工与角色权限 API 存根
 * 模块: FE-M3 / M1: IAM
 */

import request from '@/utils/request'
import type { ApiResponse, PaginatedData, PaginationParams } from '@/types/common'
import type { DepartmentNode, UserItem, RoleItem } from '@/types/system'

export const getDepartmentTreeApi = async (): Promise<ApiResponse<DepartmentNode[]>> => {
  return request.get('/api/v1/departments/tree')
}

export const getUsersListApi = async (params: PaginationParams): Promise<ApiResponse<PaginatedData<UserItem>>> => {
  return request.get('/api/v1/users', { params })
}

export const getRolesListApi = async (): Promise<ApiResponse<RoleItem[]>> => {
  return request.get('/api/v1/roles')
}
