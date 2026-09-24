/**
 * 全局通用数据传输契约 (Common DTO)
 * 镜像对齐: backend/app/schemas/common.py
 */

export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
  trace_id?: string
}

export interface PaginationParams {
  page: number
  page_size: number
}

export interface PaginatedData<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
