/**
 * 组织架构、员工与角色契约 (System DTO)
 * 镜像对齐: backend/app/schemas/user.py
 */

export interface DepartmentNode {
  id: number
  name: string
  code?: string
  parent_id?: number | null
  path?: string
  materialized_path?: string
  level: number
  sort_order?: number
  leader_name?: string
  phone?: string
  email?: string
  status?: boolean
  member_count?: number
  children?: DepartmentNode[]
}

export interface UserRoleInfo {
  id: number
  name: string
  code: string
  permission_codes?: string[]
}

export interface UserItem {
  id: number
  employee_id?: string
  username: string
  real_name: string
  dept_id?: number
  department_id?: number
  dept_name?: string
  department_name?: string
  role_ids: number[]
  role_names?: string[]
  roles?: UserRoleInfo[]
  is_active: boolean
  is_superuser?: boolean
  email?: string
  phone?: string
  created_at: string
}

export interface RoleItem {
  id: number
  role_name: string
  name?: string
  role_code: string
  code?: string
  description?: string
  is_system?: boolean
  status?: boolean
  user_count?: number
  permissions: string[]
  permission_codes?: string[]
}

export interface PermissionNode {
  id: string
  code: string
  title: string
  label?: string
  type: 'menu' | 'route' | 'button' | string
  resource_path?: string | null
  parent_id?: string | null
  children?: PermissionNode[]
}

export interface DepartmentCreate {
  name: string
  code?: string
  parent_id?: number | null
  sort_order?: number
  leader_name?: string
  phone?: string
  email?: string
}

export interface UserCreate {
  employee_id?: string
  username: string
  real_name: string
  password?: string
  dept_id?: number
  department_id?: number
  role_ids: number[]
  email?: string
  phone?: string
}

export interface RoleCreate {
  role_name?: string
  name?: string
  role_code?: string
  code?: string
  description?: string
  permissions?: string[]
  permission_codes?: string[]
}

export interface RolePermissionUpdate {
  role_id: number
  permissions?: string[]
  permission_codes?: string[]
}

