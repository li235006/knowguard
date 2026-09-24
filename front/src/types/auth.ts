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

export interface UserContext {
  user_id: number
  username: string
  dept_id: number
  role_ids: number[]
  permissions: string[]
}
