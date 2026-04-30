<template>
  <div class="chat-window">
    <!-- 消息列表 -->
    <div class="message-list" ref="messageListRef">
      <!-- 欢迎语 -->
      <div v-if="chatStore.currentMessages.length === 0" class="welcome">
        <h1>👋 你好！我是 StyleMate</h1>
        <p>我可以根据天气和场合为你推荐穿搭，试试问我：</p>
        <div class="example-questions">
          <el-button
            v-for="q in exampleQuestions"
            :key="q"
            @click="handleSend(q)"
            round
          >
            {{ q }}
          </el-button>
        </div>
      </div>

      <!-- 消息列表 -->
      <div
        v-for="msg in chatStore.currentMessages"
        :key="msg.id"
        class="message-item"
        :class="msg.role"
      >
        <div class="message-avatar">
          <el-avatar v-if="msg.role === 'user'" :size="40">
            <el-icon><User /></el-icon>
          </el-avatar>
          <el-avatar v-else :size="40" style="background-color: #409eff">
            <el-icon><MagicStick /></el-icon>
          </el-avatar>
        </div>
        <div class="message-content">
          <div class="message-role">
            {{ msg.role === 'user' ? '你' : 'StyleMate' }}
          </div>
          <div class="message-text">
            {{ msg.content }}{{ msg.isStreaming ? '▌' : '' }}
          </div>
          <!-- 穿搭建议卡片 -->
          <ClothingCard
            v-if="msg.advice && msg.role === 'assistant'"
            :advice="msg.advice"
          />
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="chatStore.isLoading" class="loading-indicator">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>StyleMate 正在思考...</span>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="input-area">
      <div class="input-wrapper">
        <el-input
          v-model="userInput"
          type="textarea"
          :rows="2"
          placeholder="输入你的问题，例如：上海明天穿什么？"
          @keydown.enter.exact="handleSend(userInput)"
          :disabled="chatStore.isLoading"
        />
        <el-button
          type="primary"
          :icon="Promotion"
          @click="handleSend(userInput)"
          :disabled="!userInput.trim() || chatStore.isLoading"
          circle
          class="send-button"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { User, MagicStick, Loading, Promotion } from '@element-plus/icons-vue'
import { useChatStore } from '@/stores/chat'
import { sendChatMessage } from '@/api/chat'
import ClothingCard from './ClothingCard.vue'
import type { ClothingAdvice } from '@/types/chat'

const chatStore = useChatStore()
const userInput = ref('')
const messageListRef = ref<HTMLElement>()

const exampleQuestions = [
  '上海明天穿什么？',
  '北京今天适合运动吗？',
  '广州周末约会怎么穿？'
]

function scrollToBottom() {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

async function handleSend(message: string) {
  if (!message.trim() || chatStore.isLoading) return

  const msg = message.trim()
  userInput.value = ''

  // 添加用户消息
  chatStore.sendMessage(msg)
  scrollToBottom()

  // 创建助手消息占位
  const assistantMsg = chatStore.addAssistantMessage('', undefined)
  assistantMsg.isStreaming = true
  let currentContent = ''

  // 发送消息并处理流式响应
  await sendChatMessage(
    msg,
    chatStore.currentSessionId,
    (chunk: string) => {
      currentContent += chunk
      chatStore.updateMessageContent(assistantMsg.id, currentContent)
      scrollToBottom()
    },
    (fullMessage: string, advice?: any) => {
      chatStore.updateMessageContent(assistantMsg.id, fullMessage)
      // 更新 advice
      const session = chatStore.currentSession
      if (session) {
        const msg = session.messages.find(m => m.id === assistantMsg.id)
        if (msg && advice) {
          msg.advice = advice as ClothingAdvice
          msg.isStreaming = false
        }
      }
      chatStore.isLoading = false
      scrollToBottom()
    },
    (error: string) => {
      chatStore.updateMessageContent(assistantMsg.id, `抱歉，出错了：${error}`)
      const session = chatStore.currentSession
      if (session) {
        const msg = session.messages.find(m => m.id === assistantMsg.id)
        if (msg) {
          msg.isStreaming = false
        }
      }
      chatStore.isLoading = false
      scrollToBottom()
    }
  )
}

onMounted(() => {
  // 初始化
})
</script>

<style scoped>
.chat-window {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f7fa;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.welcome {
  text-align: center;
  padding: 60px 20px;
  color: #606266;
}

.welcome h1 {
  color: #303133;
  margin-bottom: 16px;
}

.example-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
  margin-top: 20px;
}

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
}

.message-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  background-color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.message-item.user .message-content {
  background-color: #409eff;
  color: white;
}

.message-role {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.message-item.user .message-role {
  color: #e0e0e0;
}

.message-text {
  line-height: 1.6;
  white-space: pre-wrap;
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  color: #909399;
}

.input-area {
  padding: 20px;
  background-color: white;
  border-top: 1px solid #e4e7ed;
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-wrapper .el-textarea {
  flex: 1;
}

.send-button {
  flex-shrink: 0;
}
</style>
