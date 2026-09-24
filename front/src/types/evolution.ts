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
}

export interface FaqItem {
  id: number
  standard_question: string
  standard_answer: string
  category: string
  similar_questions: string[]
  is_cached: boolean
  created_at: string
}

export interface KnowledgeGap {
  id: number
  query_text: string
  hit_count: number
  first_seen_at: string
  last_seen_at: string
  status: 'OPEN' | 'CONVERTED' | 'DISMISSED'
}
