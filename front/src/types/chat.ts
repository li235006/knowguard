/**
 * 智能问答与溯源契约 (Chat DTO)
 * 镜像对齐: backend/app/schemas/chat.py
 */

export interface ChatRequest {
  conversation_id?: string
  query: string
  model?: string
}

export interface CitationItem {
  chunk_id: number
  unit_id: number
  unit_title: string
  snippet: string
  score: number
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: CitationItem[]
  is_silent_fallback?: boolean
  created_at: string
}

export interface ChatEvent {
  event: 'text_delta' | 'citation' | 'warning' | 'done'
  data: any
}
