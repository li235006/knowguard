<template>
  <!-- PAGE-02: 员工智能问答工作台 (/chat) -->
  <div class="h-screen w-full flex bg-[#F8FAFC] overflow-hidden select-none">
    <!-- Left Conversation Sidebar (CRUD Actions Linked) -->
    <ConversationSidebar
      :conversations="chatStore.conversations"
      :active-id="chatStore.activeConversationId"
      @new-chat="handleNewChat"
      @select-chat="handleSelectChat"
      @delete-chat="handleDeleteChat"
      @rename-chat="handleRenameChat"
    />

    <!-- Main Chat Container -->
    <div class="flex-1 flex flex-col h-full min-w-0 bg-[#F8FAFC] relative">
      <!-- Top Workspace Header -->
      <header
        class="h-14 w-full bg-white/90 backdrop-blur-apple border-b border-[#E5E7EB] px-6 flex items-center justify-between shrink-0"
      >
        <div class="flex items-center gap-2.5 overflow-hidden">
          <h2 class="font-bold text-xs text-[#0F172A] truncate">
            {{ activeTitle }}
          </h2>
        </div>
      </header>

      <!-- Message History Loading Skeleton Overlay -->
      <div
        v-if="chatStore.isLoadingMessages"
        class="absolute inset-x-0 top-14 bottom-32 bg-white/50 backdrop-blur-[1px] z-10 flex items-center justify-center pointer-events-none"
      >
        <div class="flex items-center gap-2 text-xs text-[#0071E3] font-medium bg-white px-4 py-2 rounded-xl shadow-sm border border-gray-100">
          <Loader2 :size="16" class="animate-spin" />
          <span>正在同步会话消息记录...</span>
        </div>
      </div>

      <!-- Message History List (Multi-turn Follow-up Thread) -->
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
 * 模块: FE-M2 / P1-3
 */

import { computed, onMounted } from 'vue'
import { Loader2 } from 'lucide-vue-next'
import { useChatStore } from '@/stores/chat'
import ConversationSidebar from '@/components/Chat/ConversationSidebar.vue'
import MessageList from '@/components/Chat/MessageList.vue'
import MessageInput from '@/components/Chat/MessageInput.vue'

const chatStore = useChatStore()

const activeTitle = computed(() => {
  const current = chatStore.conversations.find((c) => c.id === chatStore.activeConversationId)
  return current ? current.title : '员工智能问答'
})

const handleNewChat = async () => {
  await chatStore.createNewConversation()
}

const handleSelectChat = async (convId: string) => {
  await chatStore.selectConversation(convId)
}

const handleDeleteChat = async (convId: string) => {
  await chatStore.deleteConversation(convId)
}

const handleRenameChat = (convId: string, newTitle: string) => {
  chatStore.renameConversation(convId, newTitle)
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
})
</script>
