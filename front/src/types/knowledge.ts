/**
 * 知识资产与切片契约 (Knowledge DTO)
 * 镜像对齐: backend/app/schemas/knowledge.py & guard.py
 */

export interface KnowledgeUnit {
  id: number
  title: string
  file_type: string
  file_size?: number
  category: string
  status: 'PENDING' | 'PARSING' | 'CHUNKING' | 'INDEXED' | 'DISABLED' | 'FAILED' | string
  chunk_count: number
  permission_summary?: string
  error_message?: string | null
  created_at: string
  updated_at?: string | null
}

export interface KnowledgeUnitStatusUpdate {
  status: 'AVAILABLE' | 'DISABLED' | 'INDEXED' | string
}

export interface ChunkItem {
  id: number
  unit_id: number
  chunk_index: number
  content: string
  metadata: Record<string, unknown>
  has_vector: boolean
  char_length?: number
  status?: string
}

export interface PermissionPolicyConfig {
  unit_id: number
  is_global: boolean
  is_public?: boolean
  department_ids: number[]
  role_ids: number[]
  user_ids: number[]
  updated_at?: string | null
}

export interface BatchUploadItem {
  id: string
  file: File
  name: string
  size: number
  file_type: string
  status: 'pending' | 'uploading' | 'indexed' | 'failed'
  progress: number
  error_message?: string
}
