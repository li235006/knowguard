/**
 * 员工智能问答工作台状态仓库 (Chat Store)
 * 模块: FE-M2 / P0-4
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ConversationItem, ChatMessage, CitationItem, WarningEventData } from '@/types/chat'
import { connectSseStream } from '@/utils/sse'
import { getConversationsApi, getSuggestionsApi, mockSendChatStream } from '@/api/chat'

export const useChatStore = defineStore('chat', () => {
  const conversations = ref<ConversationItem[]>([])
  const activeConversationId = ref<string>('conv-01')
  const messages = ref<ChatMessage[]>([])
  const suggestions = ref<string[]>([])
  const isGenerating = ref<boolean>(false)
  let activeAbortController: AbortController | null = null

  // 初始化会话列表
  const fetchConversations = async () => {
    try {
      const res = await getConversationsApi()
      if (res.data) {
        conversations.value = res.data
      }
    } catch {
      // 容错降级
    }
  }

  // 初始化联想推荐
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

  // 切换会话
  const selectConversation = (convId: string) => {
    if (isGenerating.value) {
      stopGenerating()
    }
    activeConversationId.value = convId

    // 默认装载初始历史消息以还原 PAGE-02 原型效果
    if (convId === 'conv-01' && messages.value.length === 0) {
      messages.value = [
        {
          id: 'msg-01',
          role: 'user',
          content: '请问国内出差每天的住宿标准上限是多少？具体该怎么走报销流程？',
          created_at: '14:20:15'
        },
        {
          id: 'msg-02',
          role: 'assistant',
          content:
            '您好！根据公司《2026年度企业差旅报销与补贴管理标准》的最新规定，现为您梳理关键报销要点：\n\n' +
            '1. **住宿标准上限**：\n' +
            '   - **一类城市**（北京、上海、广州、深圳）：国内出差住宿标准上限为 **600 元/天**；\n' +
            '   - **二类城市**（各省会城市、新一线城市）：住宿标准上限为 **450 元/天**；\n' +
            '   - **三类及其他城市**：标准上限为 **350 元/天**。\n\n' +
            '2. **伙食与市内交通补助**：\n' +
            '   - 伙食补助包干标准为 **120 元/天**（无须发票）；\n' +
            '   - 市内公共交通补助标准为 **80 元/天**（据实报销或包干）。\n\n' +
            '3. **报销流程与凭证规范**：\n' +
            '   - 报销路径：通过 OA 办公系统 ➔ 财务审批中心 ➔ 提交《国内出差费用报销单》；\n' +
            '   - 必须上传正规住宿增值税专用发票、交通客票（飞机行程单或高铁车票原件）。',
          citations: [
            {
              chunk_id: 1024,
              unit_id: 88,
              unit_title: '2026年度企业差旅报销与补贴管理标准.pdf · 第 14 页',
              snippet:
                '国内出差住宿标准上限为一类城市 600 元/天，二类城市 450 元/天，伙食补助 120 元/天。员工需在出差结束后 15 个工作日内登录 OA 完成票据归档。',
              score: 0.94
            }
          ],
          created_at: '14:20:18',
          status: 'done'
        },
        {
          id: 'msg-03',
          role: 'user',
          content: '高管期权激励计划的分配细则是什么？',
          created_at: '14:22:50'
        },
        {
          id: 'msg-04',
          role: 'assistant',
          content:
            '抱歉，在企业公开知识库中未检索到与“高管期权激励计划”相关的规章或政策文档。\n\n' +
            '建议您确认问题描述是否准确，或向人力资源部门咨询相关制度指引。',
          is_silent_fallback: true,
          created_at: '14:23:07',
          status: 'done'
        }
      ]
    }
  }

  // 新建会话
  const createNewConversation = () => {
    if (isGenerating.value) {
      stopGenerating()
    }
    const newId = `conv-${Date.now()}`
    const newConv: ConversationItem = {
      id: newId,
      title: '新建智能问答',
      created_at: '刚刚',
      message_count: 0
    }
    conversations.value.unshift(newConv)
    activeConversationId.value = newId
    messages.value = []
  }

  // 发送消息并消费 SSE 流式事件
  const sendMessage = async (queryText: string) => {
    if (!queryText.trim() || isGenerating.value) return

    const now = new Date().toTimeString().slice(0, 8)
    const userMsgId = `user-${Date.now()}`
    const assistantMsgId = `asst-${Date.now()}`

    // 1. 追加用户提问
    messages.value.push({
      id: userMsgId,
      role: 'user',
      content: queryText.trim(),
      created_at: now
    })

    // 2. 初始化 AI 空白消息气泡
    const assistantMsg: ChatMessage = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      citations: [],
      is_silent_fallback: false,
      created_at: now,
      status: 'streaming'
    }
    messages.value.push(assistantMsg)

    isGenerating.value = true
    activeAbortController = new AbortController()

    const callbacks = {
      onTextDelta: (delta: string) => {
        assistantMsg.content += delta
      },
      onCitation: (citation: CitationItem) => {
        if (!assistantMsg.citations) assistantMsg.citations = []
        assistantMsg.citations.push(citation)
      },
      onWarning: (warning: WarningEventData) => {
        if (warning.type === 'permission_restricted') {
          assistantMsg.is_silent_fallback = true
        }
      },
      onDone: () => {
        assistantMsg.status = 'done'
        isGenerating.value = false
        activeAbortController = null
      },
      onError: (err: Error) => {
        assistantMsg.status = 'error'
        if (!assistantMsg.content) {
          assistantMsg.content = `服务暂时不可用: ${err.message}`
        }
        isGenerating.value = false
        activeAbortController = null
      }
    }

    const payload = {
      conversation_id: activeConversationId.value,
      query: queryText.trim()
    }

    if (import.meta.env.VITE_ENABLE_MOCK === 'true') {
      await mockSendChatStream(payload, callbacks, activeAbortController.signal)
    } else {
      const url = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/v1/chat/completions`
      await connectSseStream({
        url,
        payload,
        signal: activeAbortController.signal,
        ...callbacks
      })
    }
  }

  // 停止生成
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
    fetchConversations,
    fetchSuggestions,
    selectConversation,
    createNewConversation,
    sendMessage,
    stopGenerating
  }
})
