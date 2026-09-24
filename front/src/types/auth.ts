/**
 * 身份认证与会话契约 (Auth DTO)
 * 镜像对齐: backend/app/schemas/auth.py
 */

export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface RefreshTokenRequest {
  refresh_token: string
}

export interface TokenPayload {
  sub: string
  user_id: number
  username: string
  real_name: string
  employee_id: string
  dept_id?: number | null
  dept_name?: string | null
  role_code?: string | null
  role_codes: string[]
  role_ids: number[]
  permissions: string[]
  token_type: string
  exp: number
  iat?: number | null
}

export interface UserContext {
  user_id: number
  username: string
  real_name: string
  employee_id: string
  dept_id?: number | null
  dept_name?: string | null
  role_code?: string | null
  role_codes: string[]
  role_ids: number[]
  permissions: string[]
  avatar?: string | null
  is_superuser?: boolean
}
