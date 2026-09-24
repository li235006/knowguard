/**
 * 知识资产与切片契约 (Knowledge DTO)
 * 镜像对齐: backend/app/schemas/knowledge.py & guard.py
 */

export interface KnowledgeUnit {
  id: number
  title: string
  file_type: string
  category: string
  status: 'PENDING' | 'PARSING' | 'CHUNKING' | 'INDEXED' | 'FAILED'
  chunk_count: number
  created_at: string
}

export interface ChunkItem {
  id: number
  unit_id: number
  chunk_index: number
  content: string
  metadata: Record<string, any>
  has_vector: boolean
}

export interface PermissionPolicyConfig {
  unit_id: number
  is_global: boolean
  department_ids: number[]
  role_ids: number[]
  user_ids: number[]
}
