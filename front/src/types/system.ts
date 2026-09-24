/**
 * 组织架构、员工与角色契约 (System DTO)
 * 镜像对齐: backend/app/schemas/user.py
 */

export interface DepartmentNode {
  id: number
  name: string
  parent_id?: number | null
  path: string
  level: number
  member_count?: number
  children?: DepartmentNode[]
}

export interface UserItem {
  id: number
  username: string
  real_name: string
  dept_id: number
  dept_name?: string
  role_ids: number[]
  role_names?: string[]
  is_active: boolean
  email?: string
  phone?: string
  created_at: string
}

export interface RoleItem {
  id: number
  role_name: string
  role_code: string
  description?: string
  user_count?: number
  permissions: string[]
}

export interface PermissionNode {
  id: string
  code: string
  title: string
  type: 'menu' | 'route' | 'button'
  parent_id?: string | null
  children?: PermissionNode[]
}

export interface DepartmentCreate {
  name: string
  parent_id?: number | null
}

export interface UserCreate {
  username: string
  real_name: string
  password?: string
  dept_id: number
  role_ids: number[]
  email?: string
  phone?: string
}

export interface RoleCreate {
  role_name: string
  role_code: string
  description?: string
  permissions: string[]
}

export interface RolePermissionUpdate {
  role_id: number
  permissions: string[]
}

