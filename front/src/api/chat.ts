/**
 * 智能问答、会话管理与多轮追问 API
 * 模块: FE-M2 / P1-3
 * 接口契约对齐: backend/app/schemas/chat.py
 * 支持真实后端 RESTful 联调与 VITE_ENABLE_MOCK=true/false 双态自由切换
 */

import request, { generateTraceId } from '@/utils/request'
import type { ApiResponse } from '@/types/common'
import type {
  ConversationItem,
  CreateConversationPayload,
  ChatMessage,
  ChatRequest
} from '@/types/chat'
import type { SseStreamCallbacks } from '@/utils/sse'

const isMockEnabled = (): boolean => {
  return import.meta.env.VITE_ENABLE_MOCK === 'true'
}

// 内存中维护可变的 Mock 会话与消息历史
let liveMockConversations: ConversationItem[] = [
  {
    id: 'conv-01',
    title: '出差报销与高管激励咨询',
    created_at: '刚刚',
    updated_at: '刚刚',
    message_count: 4
  },
  {
    id: 'conv-02',
    title: 'Q3 市场营销预算规范',
    created_at: '昨天',
    updated_at: '昨天',
    message_count: 6
  },
  {
    id: 'conv-03',
    title: '企业网络与 VPN 接入指引',
    created_at: '3天前',
    updated_at: '3天前',
    message_count: 2
  },
  {
    id: 'conv-04',
    title: '年假折算与调休审批流程',
    created_at: '上周',
    updated_at: '上周',
    message_count: 5
  }
]

const liveMockMessagesMap: Record<string, ChatMessage[]> = {
  'conv-01': [
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

export const mockSuggestions: string[] = [
  '国内出差住宿费用报销上限是多少？',
  '跨部门协作借调流程怎么申请？',
  '高管期权激励计划的分配细则是什么？',
  '企业知识库 4D-RBAC 动态权限如何配置？'
]

// 1. 获取用户全部历史会话 (GET /api/v1/chat/conversations)
export const getConversationsApi = async (): Promise<ApiResponse<ConversationItem[]>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 80))
    return {
      code: 200,
      message: 'success',
      data: [...liveMockConversations],
      trace_id: generateTraceId()
    }
  }

  return request.get('/api/v1/chat/conversations')
}

// 2. 创建全新问答会话 (POST /api/v1/chat/conversations)
export const createConversationApi = async (
  payload?: CreateConversationPayload
): Promise<ApiResponse<ConversationItem>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 80))
    const newId = `conv-${Date.now()}`
    const newConv: ConversationItem = {
      id: newId,
      title: payload?.title || '新建智能问答',
      created_at: '刚刚',
      updated_at: '刚刚',
      message_count: 0
    }
    liveMockConversations.unshift(newConv)
    liveMockMessagesMap[newId] = []
    return {
      code: 200,
      message: '新建会话成功',
      data: newConv,
      trace_id: generateTraceId()
    }
  }

  return request.post('/api/v1/chat/conversations', payload || {})
}

// 3. 获取指定会话的历史消息列表 (GET /api/v1/chat/conversations/{id}/messages)
export const getConversationMessagesApi = async (
  conversationId: string
): Promise<ApiResponse<ChatMessage[]>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 80))
    const msgs = liveMockMessagesMap[conversationId] || []
    return {
      code: 200,
      message: 'success',
      data: JSON.parse(JSON.stringify(msgs)),
      trace_id: generateTraceId()
    }
  }

  return request.get(`/api/v1/chat/conversations/${conversationId}/messages`)
}

// 4. 删除指定会话及其全部历史消息 (DELETE /api/v1/chat/conversations/{id})
export const deleteConversationApi = async (
  conversationId: string
): Promise<ApiResponse<{ deleted_id: string }>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 80))
    liveMockConversations = liveMockConversations.filter((c) => c.id !== conversationId)
    delete liveMockMessagesMap[conversationId]
    return {
      code: 200,
      message: '会话已成功删除',
      data: { deleted_id: conversationId },
      trace_id: generateTraceId()
    }
  }

  return request.delete(`/api/v1/chat/conversations/${conversationId}`)
}

// 5. 获取联想建议提问 (GET /api/v1/chat/suggestions)
export const getSuggestionsApi = async (): Promise<ApiResponse<string[]>> => {
  if (isMockEnabled()) {
    await new Promise((resolve) => setTimeout(resolve, 50))
    return {
      code: 200,
      message: 'success',
      data: [...mockSuggestions],
      trace_id: generateTraceId()
    }
  }

  return request.get('/api/v1/chat/suggestions')
}

/**
 * 模拟原生 SSE 打字机流式输出 (供 VITE_ENABLE_MOCK=true 环境使用)
 */
export const mockSendChatStream = async (
  payload: ChatRequest,
  callbacks: SseStreamCallbacks,
  signal?: AbortSignal
): Promise<void> => {
  const query = payload.query.trim()
  const isRestrictedQuery =
    query.includes('期权') || query.includes('高管') || query.includes('薪酬') || query.includes('保密')

  if (isRestrictedQuery) {
    // 模拟 4D-RBAC 越权拦截：静默未命中降级 (Silent Fallback)
    await new Promise((resolve) => setTimeout(resolve, 200))
    callbacks.onWarning({
      type: 'permission_restricted',
      message: '部分涉及核心高管期权薪酬的高密文档因 4D-RBAC 权限策略受限已实施安全隔离'
    })

    const fallbackDeltas = [
      '抱歉，在企业',
      '公开知识库中',
      '未检索到与“',
      query.slice(0, 10),
      '”相关的规章',
      '或政策文档。\n\n',
      '建议您确认问题描述是否准确，',
      '或向相关业务主管部门咨询合规制度指引。'
    ]

    for (const chunk of fallbackDeltas) {
      if (signal?.aborted) return
      await new Promise((resolve) => setTimeout(resolve, 60))
      callbacks.onTextDelta(chunk)
    }

    callbacks.onDone({
      conversation_id: payload.conversation_id || 'conv-01',
      trace_id: generateTraceId(),
      total_tokens: 120
    })
    return
  }

  // 正常放行问答流式输出
  const normalDeltas = [
    '您好！根据公司《2026年度企业差旅报销与补贴管理标准》的最新规定，现为您梳理关键报销要点：\n\n',
    '1. **住宿标准上限**：\n',
    '   - **一类城市**（北京、上海、广州、深圳）：国内出差住宿标准上限为 **600 元/天**；\n',
    '   - **二类城市**（各省会城市、新一线城市）：住宿标准上限为 **450 元/天**；\n',
    '   - **三类及其他城市**：标准上限为 **350 元/天**。\n\n',
    '2. **伙食与市内交通补助**：\n',
    '   - 伙食补助包干标准为 **120 元/天**（无须发票）；\n',
    '   - 市内公共交通补助标准为 **80 元/天**（据实报销或包干）。\n\n',
    '3. **报销流程与凭证规范**：\n',
    '   - 报销路径：通过 OA 办公系统 ➔ 财务审批中心 ➔ 提交《国内出差费用报销单》；\n',
    '   - 必须上传正规住宿增值税专用发票、交通客票（飞机行程单或高铁车票原件）。'
  ]

  for (const chunk of normalDeltas) {
    if (signal?.aborted) return
    await new Promise((resolve) => setTimeout(resolve, 80))
    callbacks.onTextDelta(chunk)
  }

  // 附带溯源卡片
  if (!signal?.aborted) {
    callbacks.onCitation({
      chunk_id: 1024,
      unit_id: 88,
      unit_title: '2026年度企业差旅报销与补贴管理标准.pdf · 第 14 页',
      snippet:
        '国内出差住宿标准上限为一类城市 600 元/天，二类城市 450 元/天，伙食补助 120 元/天。员工需在出差结束后 15 个工作日内登录 OA 完成票据归档。',
      score: 0.94
    })

    callbacks.onDone({
      conversation_id: payload.conversation_id || 'conv-01',
      trace_id: generateTraceId(),
      total_tokens: 386
    })
  }
}
