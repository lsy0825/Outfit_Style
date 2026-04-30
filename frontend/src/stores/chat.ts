import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChatMessage, ChatSession } from '@/types/chat'

export const useChatStore = defineStore('chat', () => {
  // 状态
  const currentSessionId = ref<string>('default')
  const sessions = ref<ChatSession[]>([
    {
      id: 'default',
      title: '新对话',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now()
    }
  ])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // 计算属性
  const currentSession = computed(() => {
    return sessions.value.find(s => s.id === currentSessionId.value)
  })

  const currentMessages = computed(() => {
    return currentSession.value?.messages || []
  })

  // 方法
// 用于生成唯一 ID 的计数器
let messageIdCounter = 0

function sendMessage(content: string) {
    // 添加用户消息
    const userMessage: ChatMessage = {
      id: `msg_user_${Date.now()}_${++messageIdCounter}`,
      role: 'user',
      content,
      timestamp: Date.now()
    }

    let session = currentSession.value
    if (!session) {
      session = createNewSession()
    }

    session.messages.push(userMessage)
    session.updatedAt = Date.now()
    isLoading.value = true
    error.value = null

    return userMessage
  }

  function addAssistantMessage(content: string, advice?: any) {
    const assistantMessage: ChatMessage = {
      id: `msg_assistant_${Date.now()}_${++messageIdCounter}`,
      role: 'assistant',
      content,
      timestamp: Date.now(),
      advice
    }

    const session = currentSession.value
    if (session) {
      session.messages.push(assistantMessage)
      session.updatedAt = Date.now()
    }

    isLoading.value = false
    return assistantMessage
  }

  function updateLastAssistantMessage(content: string) {
    const session = currentSession.value
    if (session && session.messages.length > 0) {
      const lastMsg = session.messages[session.messages.length - 1]
      if (lastMsg.role === 'assistant') {
        lastMsg.content = content
        lastMsg.timestamp = Date.now()
      }
    }
    isLoading.value = false
  }

  function updateMessageContent(messageId: string, content: string) {
    const session = currentSession.value
    if (session) {
      const message = session.messages.find(m => m.id === messageId)
      if (message) {
        message.content = content
        message.timestamp = Date.now()
      }
    }
  }

  function createNewSession() {
    const newSession: ChatSession = {
      id: `session_${Date.now()}`,
      title: '新对话',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now()
    }
    sessions.value.unshift(newSession)
    currentSessionId.value = newSession.id
    return newSession
  }

  function deleteSession(sessionId: string) {
    const index = sessions.value.findIndex(s => s.id === sessionId)
    if (index !== -1) {
      sessions.value.splice(index, 1)
      if (currentSessionId.value === sessionId && sessions.value.length > 0) {
        currentSessionId.value = sessions.value[0].id
      }
    }
  }

  function setCurrentSession(sessionId: string) {
    currentSessionId.value = sessionId
  }

  function clearError() {
    error.value = null
  }

  return {
    currentSessionId,
    sessions,
    isLoading,
    error,
    currentSession,
    currentMessages,
    sendMessage,
    addAssistantMessage,
    updateLastAssistantMessage,
    updateMessageContent,
    createNewSession,
    deleteSession,
    setCurrentSession,
    clearError
  }
})
