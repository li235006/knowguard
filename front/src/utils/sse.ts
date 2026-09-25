/**
 * SSE (Server-Sent Events) 原生 Fetch ReadableStream 流式问答客户端
 * 
 * 职责:
 *  - 基于 Fetch API 原生 ReadableStream 消费 SSE 事件流
 *  - 自动注入 Authorization Bearer 与 X-Trace-Id
 *  - 流式解析 text_delta, citation, warning, done 事件帧并回调 (RedLine 3)
 *  - 支持 AbortController 中途主动停止打字机流式生成
 */

import type {
  ChatRequest,
  CitationItem,
  TextDeltaEventData,
  WarningEventData,
  DoneEventData
} from '@/types/chat'
import { generateTraceId } from './request'

export interface SseStreamCallbacks {
  onTextDelta: (delta: string) => void
  onCitation: (citation: CitationItem) => void
  onWarning: (warning: WarningEventData) => void
  onDone: (done: DoneEventData) => void
  onError?: (error: Error) => void
}

export interface ConnectSseOptions extends SseStreamCallbacks {
  url: string
  payload: ChatRequest
  signal?: AbortSignal
}

export const connectSseStream = async (options: ConnectSseOptions): Promise<void> => {
  const { url, payload, signal, onTextDelta, onCitation, onWarning, onDone, onError } = options
  const token = localStorage.getItem('access_token')

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        'X-Trace-Id': generateTraceId()
      },
      body: JSON.stringify(payload),
      signal
    })

    if (!response.ok) {
      throw new Error(`SSE 接口响应失败: HTTP ${response.status}`)
    }

    if (!response.body) {
      throw new Error('SSE 响应流体为空')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      buffer = buffer.replace(/\r\n/g, '\n')
      const blocks = buffer.split('\n\n')
      // 保留最后一个可能尚未完整的 chunk 放入 buffer
      buffer = blocks.pop() || ''

      for (const block of blocks) {
        if (!block.trim()) continue

        // 解析 event 与 data 行
        const lines = block.split('\n')
        let eventType = 'text_delta'
        let dataString = ''

        for (const line of lines) {
          if (line.startsWith('event:')) {
            eventType = line.slice(6).trim()
          } else if (line.startsWith('data:')) {
            dataString = line.slice(5).trim()
          }
        }

        if (!dataString) continue

        try {
          const parsedData = JSON.parse(dataString)

          if (eventType === 'text_delta') {
            const data = parsedData as TextDeltaEventData & { text?: string }
            const deltaText = data.delta ?? data.text ?? ''
            if (deltaText) {
              onTextDelta(deltaText)
            }
          } else if (eventType === 'citation') {
            const data = parsedData as CitationItem
            onCitation(data)
          } else if (eventType === 'warning') {
            const data = parsedData as WarningEventData
            onWarning(data)
          } else if (eventType === 'done') {
            const data = parsedData as DoneEventData
            onDone(data)
          }
        } catch {
          // 容错处理纯文本 data
          if (eventType === 'text_delta' && dataString) {
            onTextDelta(dataString)
          }
        }
      }
    }
  } catch (err: unknown) {
    if (signal?.aborted) {
      // 主动取消，不视为系统异常
      return
    }
    const errorObj = err instanceof Error ? err : new Error(String(err))
    onError?.(errorObj)
  }
}
