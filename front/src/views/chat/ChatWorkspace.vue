<template>
  <!-- PAGE-02: 员工智能问答工作台 (/chat) -->
  <div class="h-screen w-full flex bg-[#F8FAFC] overflow-hidden select-none">
    <!-- Left Conversation Sidebar -->
    <ConversationSidebar
      :conversations="chatStore.conversations"
      :active-id="chatStore.activeConversationId"
      @new-chat="handleNewChat"
      @select-chat="handleSelectChat"
    />

    <!-- Main Chat Container -->
    <div class="flex-1 flex flex-col h-full min-w-0 bg-[#F8FAFC]">
      <!-- Top Workspace Header -->
      <header
        class="h-14 w-full bg-white/90 backdrop-blur-apple border-b border-[#E5E7EB] px-6 flex items-center justify-between shrink-0"
      >
        <div class="flex items-center gap-2.5 overflow-hidden">
          <h2 class="font-bold text-xs text-[#0F172A] truncate">
            {{ activeTitle }}
          </h2>
          <span
            class="px-2 py-0.5 rounded text-[10px] font-mono bg-blue-50 text-[#0071E3] border border-blue-200 shrink-0"
          >
            Qwen-Plus · 知识库 RAG 增强
          </span>
        </div>

        <div class="flex items-center gap-3">
          <!-- 4D-RBAC Security Engine Status Badge -->
          <div
            class="flex items-center gap-1.5 px-2.5 py-1 bg-[#F0FDF4] border border-[#BBF7D0] rounded-full text-[11px] text-[#16A34A] font-medium"
          >
            <span class="w-1.5 h-1.5 rounded-full bg-[#16A34A] animate-pulse"></span>
            <span>4D-RBAC 动态鉴权护栏在线</span>
          </div>
        </div>
      </header>

      <!-- Message History List -->
      <MessageList :messages="chatStore.messages" />

      <!-- Bottom Input and Suggestions Area -->
      <MessageInput
        :suggestions="chatStore.suggestions"
        :is-generating="chatStore.isGenerating"
        @send="handleSendMessage"
        @stop="handleStopGenerating"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 员工智能问答工作台视图
 * 原型对应: PAGE-02 (chat_workspace.png)
 * 模块: FE-M2 / P0-4
 */

import { computed, onMounted } from 'vue'
import { useChatStore } from '@/stores/chat'
import ConversationSidebar from '@/components/Chat/ConversationSidebar.vue'
import MessageList from '@/components/Chat/MessageList.vue'
import MessageInput from '@/components/Chat/MessageInput.vue'

const chatStore = useChatStore()

const activeTitle = computed(() => {
  const current = chatStore.conversations.find((c) => c.id === chatStore.activeConversationId)
  return current ? current.title : '员工智能问答'
})

const handleNewChat = () => {
  chatStore.createNewConversation()
}

const handleSelectChat = (convId: string) => {
  chatStore.selectConversation(convId)
}

const handleSendMessage = (query: string) => {
  chatStore.sendMessage(query)
}

const handleStopGenerating = () => {
  chatStore.stopGenerating()
}

onMounted(async () => {
  await chatStore.fetchConversations()
  await chatStore.fetchSuggestions()
  chatStore.selectConversation('conv-01')
})
</script>
