/**
 * 员工智能问答工作台状态仓库 (Chat Store)
 * 模块: FE-M2 / P1-3
 * 职责: 会话生命周期管理、多轮历史消息加载、真实 SSE 鉴权问答流与连续追问
 */

import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import type { ConversationItem, ChatMessage, CitationItem, WarningEventData, DoneEventData } from '@/types/chat'
import { connectSseStream } from '@/utils/sse'
import {
  getConversationsApi,
  createConversationApi,
  getConversationMessagesApi,
  deleteConversationApi,
  getSuggestionsApi,
  mockSendChatStream
} from '@/api/chat'

export const useChatStore = defineStore('chat', () => {
  const conversations = ref<ConversationItem[]>([])
  const activeConversationId = ref<string>('')
  const messages = ref<ChatMessage[]>([])
  const suggestions = ref<string[]>([])
  const isGenerating = ref<boolean>(false)
  const isLoadingMessages = ref<boolean>(false)
  let activeAbortController: AbortController | null = null

  // 1. 初始化拉取会话列表
  const fetchConversations = async () => {
    try {
      const res = await getConversationsApi()
      if (res.data && res.data.length > 0) {
        conversations.value = res.data
        if (!activeConversationId.value || !conversations.value.some((c) => c.id === activeConversationId.value)) {
          await selectConversation(conversations.value[0].id)
        }
      } else {
        await createNewConversation()
      }
    } catch (err) {
      console.error('拉取历史会话列表异常:', err)
    }
  }

  // 2. 初始化智能联想推荐提问
  const fetchSuggestions = async () => {
    try {
      const res = await getSuggestionsApi()
      if (res.data) {
        suggestions.value = res.data
      }
    } catch {
      // 容错降级
    }
  }

  // 3. 切换激活会话并加载真实历史消息
  const selectConversation = async (convId: string) => {
    if (isGenerating.value) {
      stopGenerating()
    }
    activeConversationId.value = convId
    isLoadingMessages.value = true
    try {
      const res = await getConversationMessagesApi(convId)
      if (res.data) {
        messages.value = res.data
      } else {
        messages.value = []
      }
    } catch (err) {
      console.error(`加载会话 [${convId}] 消息历史失败:`, err)
      messages.value = []
    } finally {
      isLoadingMessages.value = false
    }
  }

  // 4. 创建全新会话
  const createNewConversation = async (title?: string): Promise<ConversationItem | null> => {
    if (isGenerating.value) {
      stopGenerating()
    }
    try {
      const res = await createConversationApi({ title: title || '新建智能问答' })
      if (res.data) {
        conversations.value.unshift(res.data)
        activeConversationId.value = res.data.id
        messages.value = []
        return res.data
      }
    } catch (err) {
      console.error('新建会话异常:', err)
    }
    return null
  }

  // 5. 删除指定会话及其消息
  const deleteConversation = async (convId: string) => {
    try {
      await deleteConversationApi(convId)
      conversations.value = conversations.value.filter((c) => c.id !== convId)

      // 若被删除的正是当前激活会话，自动切换至首个会话或创建新会话
      if (activeConversationId.value === convId) {
        if (conversations.value.length > 0) {
          await selectConversation(conversations.value[0].id)
        } else {
          await createNewConversation()
        }
      }
    } catch (err) {
      console.error(`删除会话 [${convId}] 失败:`, err)
    }
  }

  // 6. 重命名会话标题
  const renameConversation = (convId: string, newTitle: string) => {
    const target = conversations.value.find((c) => c.id === convId)
    if (target && newTitle.trim()) {
      target.title = newTitle.trim()
    }
  }

  // 7. 发送消息并连续追问
  const sendMessage = async (queryText: string) => {
    const text = queryText.trim()
    if (!text || isGenerating.value) return

    // 若无激活会话，首先创建
    if (!activeConversationId.value) {
      await createNewConversation()
    }

    const now = new Date().toTimeString().slice(0, 8)
    const userMsgId = `user-${Date.now()}`
    const assistantMsgId = `asst-${Date.now()}`

    // 1. 追加用户提问气泡
    messages.value.push({
      id: userMsgId,
      role: 'user',
      content: text,
      created_at: now
    })

    // 2. 如果当前会话还是初始默认标题，根据用户首问智能归纳会话标题
    const currentConv = conversations.value.find((c) => c.id === activeConversationId.value)
    if (currentConv && (currentConv.title === '新建智能问答' || currentConv.title === '新建会话')) {
      currentConv.title = text.length > 18 ? `${text.slice(0, 18)}...` : text
    }

    // 3. 初始化 AI 响应消息气泡 (必须使用 reactive 确保流式打字即时驱动 DOM 响应式重绘)
    const assistantMsg = reactive<ChatMessage>({
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      citations: [],
      is_silent_fallback: false,
      created_at: now,
      status: 'streaming',
      llm_model: 'qwen3.7-flash',
      is_real_llm: false
    })
    messages.value.push(assistantMsg)

    isGenerating.value = true
    activeAbortController = new AbortController()

    const callbacks = {
      onTextDelta: (delta: string) => {
        assistantMsg.content += delta
        const idx = messages.value.findIndex((m) => m.id === assistantMsgId)
        if (idx !== -1) {
          messages.value[idx].content = assistantMsg.content
        }
      },
      onCitation: (citation: CitationItem) => {
        // 用户硬性要求：置信度必须超 60% (>= 0.60)，且最多展示 4 个
        if ((citation.score ?? 0) < 0.60) {
          return
        }
        if (!assistantMsg.citations) assistantMsg.citations = []
        if (
          assistantMsg.citations.length < 4 &&
          !assistantMsg.citations.some((c) => c.chunk_id === citation.chunk_id)
        ) {
          assistantMsg.citations.push(citation)
        }
        const idx = messages.value.findIndex((m) => m.id === assistantMsgId)
        if (idx !== -1) {
          messages.value[idx].citations = [...assistantMsg.citations]
        }
      },
      onWarning: (warning: WarningEventData) => {
        if (warning.type === 'permission_restricted' || warning.type === 'PERMISSION_ISOLATION') {
          assistantMsg.is_silent_fallback = true
          const idx = messages.value.findIndex((m) => m.id === assistantMsgId)
          if (idx !== -1) {
            messages.value[idx].is_silent_fallback = true
          }
        }
      },
      onDone: (doneData?: DoneEventData) => {
        assistantMsg.status = 'done'
        if (doneData) {
          assistantMsg.llm_source = doneData.llm_source
          assistantMsg.llm_model = doneData.llm_model || 'qwen3.7-flash'
          assistantMsg.is_real_llm = doneData.is_real_llm ?? (doneData.llm_source === 'remote_dashscope')
        }
        const idx = messages.value.findIndex((m) => m.id === assistantMsgId)
        if (idx !== -1) {
          messages.value[idx].status = 'done'
          if (doneData) {
            messages.value[idx].llm_source = assistantMsg.llm_source
            messages.value[idx].llm_model = assistantMsg.llm_model
            messages.value[idx].is_real_llm = assistantMsg.is_real_llm
          }
        }
        isGenerating.value = false
        activeAbortController = null
        if (currentConv) {
          currentConv.message_count = messages.value.length
          currentConv.updated_at = '刚刚'
        }
      },
      onError: (err: Error) => {
        assistantMsg.status = 'error'
        if (!assistantMsg.content) {
          assistantMsg.content = `服务暂时不可用: ${err.message}`
        }
        const target = messages.value.find((m) => m.id === assistantMsgId)
        if (target) {
          target.status = 'error'
          target.content = assistantMsg.content
        }
        isGenerating.value = false
        activeAbortController = null
      }
    }

    const payload = {
      conversation_id: activeConversationId.value,
      query: text
    }

    if (import.meta.env.VITE_ENABLE_MOCK === 'true') {
      await mockSendChatStream(payload, callbacks, activeAbortController.signal)
    } else {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
      const url = baseUrl ? `${baseUrl.replace(/\/$/, '')}/api/v1/chat/completions` : '/api/v1/chat/completions'
      await connectSseStream({
        url,
        payload,
        signal: activeAbortController.signal,
        ...callbacks
      })
    }
  }

  // 8. 停止生成
  const stopGenerating = () => {
    if (activeAbortController) {
      activeAbortController.abort()
      activeAbortController = null
    }
    isGenerating.value = false
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg && lastMsg.role === 'assistant' && lastMsg.status === 'streaming') {
      lastMsg.status = 'done'
    }
  }

  return {
    conversations,
    activeConversationId,
    messages,
    suggestions,
    isGenerating,
    isLoadingMessages,
    fetchConversations,
    fetchSuggestions,
    selectConversation,
    createNewConversation,
    deleteConversation,
    renameConversation,
    sendMessage,
    stopGenerating
  }
})
