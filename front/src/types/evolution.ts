/**
 * 知识自进化与沉淀契约 (Evolution DTO)
 * 镜像对齐: backend/app/schemas/evolution.py
 */

export interface FaqCandidate {
  id: number
  cluster_id: string
  cluster_count: number
  suggested_question: string
  suggested_answer: string
  confidence_score: number
  status: 'PENDING' | 'ACCEPTED' | 'REJECTED'
  similar_queries?: string[]
  sample_queries?: string[]
  created_at?: string
  updated_at?: string
}

export interface FaqItem {
  id: number
  standard_question: string
  standard_answer: string
  category: string
  similar_questions: string[]
  hit_count: number
  is_cached: boolean
  is_enabled: boolean
  status?: boolean
  candidate_id?: number | null
  created_at?: string
  updated_at?: string
}

export interface KnowledgeGap {
  id: number
  gap_code?: string
  query_text: string
  hit_count: number
  domain?: string
  department_name?: string
  severity?: 'P1' | 'P2' | 'P3'
  status: 'OPEN' | 'CONVERTED' | 'DISMISSED' | 'RESOLVED' | 'IGNORED'
  reason?: string
  user_id?: number
  first_seen_at?: string
  last_seen_at?: string
  created_at?: string
}

export interface CandidateApprovePayload {
  standard_question?: string
  standard_answer?: string
  category?: string
  similar_questions?: string[]
  is_cached?: boolean
}

export interface CandidateRejectPayload {
  reason?: string
}

export interface FaqCreatePayload {
  standard_question: string
  standard_answer: string
  category?: string
  similar_questions?: string[]
  is_cached?: boolean
  is_enabled?: boolean
  candidate_id?: number | null
}

export interface FaqUpdatePayload {
  standard_question?: string
  standard_answer?: string
  category?: string
  similar_questions?: string[]
  is_cached?: boolean
  is_enabled?: boolean
}

export interface KnowledgeGapConvertPayload {
  title?: string
  domain?: string
  assignee?: string
  deadline?: string
  priority?: string
  notes?: string
}

export interface ClusterMiningResult {
  mined_clusters: number
  total_queries_analyzed: number
  candidates_created?: number
  candidates_updated?: number
}

export interface EvolutionMetrics {
  unresolved_gaps_count: number
  unresolved_gaps_delta: string
  pending_candidates_count: number
  clustering_accuracy: string
  avg_resolution_days: number
  resolution_speedup_percent: number
}
