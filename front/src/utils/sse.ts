/**
 * SSE (Server-Sent Events) 打字机流式问答客户端工具存根
 * 
 * 职责:
 *  - 基于 Fetch API 建立长连接，传输 Authorization 与 TraceId
 *  - 流式解析 text_delta, citation, warning, done 事件帧并回调
 */

import type { ChatEvent } from '@/types/chat'

export interface SseOptions {
  url: string
  payload: any
  onMessage: (event: ChatEvent) => void
  onError?: (error: any) => void
  onDone?: () => void
}

export const connectSseStream = async (options: SseOptions): Promise<void> => {
  // SSE 流式解析存根: throw new Error('Not implemented')
}
