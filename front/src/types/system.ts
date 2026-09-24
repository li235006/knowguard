/**
 * 组织架构、员工与角色契约 (System DTO)
 * 镜像对齐: backend/app/schemas/user.py
 */

export interface DepartmentNode {
  id: number
  name: string
  parent_id?: number
  path: string
  level: number
  children?: DepartmentNode[]
}

export interface UserItem {
  id: number
  username: string
  real_name: string
  dept_id: number
  dept_name?: string
  role_ids: number[]
  is_active: boolean
  created_at: string
}

export interface RoleItem {
  id: number
  role_name: string
  role_code: string
  description?: string
  permissions: string[]
}
