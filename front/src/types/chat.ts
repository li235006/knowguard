/**
 * 智能问答与溯源契约 (Chat DTO)
 * 镜像对齐: backend/app/schemas/chat.py
 */

export interface ConversationItem {
  id: string
  title: string
  created_at: string
  updated_at?: string
  message_count?: number
}

export interface CreateConversationPayload {
  title?: string
}

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
  status?: 'streaming' | 'done' | 'error'
}

export interface TextDeltaEventData {
  delta: string
}

export interface WarningEventData {
  type: string
  message: string
}

export interface DoneEventData {
  conversation_id: string
  trace_id: string
  total_tokens?: number
}

export type ChatEventData =
  | TextDeltaEventData
  | CitationItem
  | WarningEventData
  | DoneEventData
  | Record<string, unknown>

export interface ChatEvent {
  event: 'text_delta' | 'citation' | 'warning' | 'done'
  data: ChatEventData
}
