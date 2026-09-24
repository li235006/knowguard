/**
 * 员工智能问答工作台状态仓库 (Chat Store)
 * 模块: FE-M2
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ChatMessage } from '@/types/chat'

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const activeConversationId = ref<string | null>(null)

  return { messages, activeConversationId }
})
