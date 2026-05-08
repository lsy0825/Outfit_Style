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
        <!-- 用户消息 -->
        <div v-if="msg.role === 'user'" class="user-message">
          <div class="message-avatar">
            <el-avatar :size="40">
              <el-icon><User /></el-icon>
            </el-avatar>
          </div>
          <div class="message-content">
            <div class="message-role">你</div>
            <div class="message-text">{{ msg.content }}</div>
          </div>
        </div>

        <!-- 助手消息 - 左右布局 -->
        <div v-else class="assistant-message">
          <div class="message-left">
            <div class="message-avatar">
              <el-avatar :size="40" style="background-color: #409eff">
                <el-icon><MagicStick /></el-icon>
              </el-avatar>
            </div>
            <div class="message-content">
              <div class="message-role">StyleMate</div>
              <div class="message-text">{{ msg.content }}</div>
              <!-- 穿搭建议卡片 -->
              <ClothingCard
                v-if="msg.advice"
                :advice="msg.advice"
              />
            </div>
          </div>
          <!-- 右侧图片展示 -->
          <div v-if="msg.images && msg.images.length > 0" class="message-right">
            <div class="image-gallery">
              <div class="gallery-title">
                <el-icon><Picture /></el-icon>
                <span>穿搭参考</span>
                <span class="gallery-hint">（点击可放大查看）</span>
              </div>
              <div class="image-grid">
                <el-image
                  v-for="(img, index) in msg.images"
                  :key="img"
                  :src="img"
                  :alt="`穿搭参考 ${index + 1}`"
                  :preview-src-list="msg.images"
                  :initial-index="index"
                  fit="cover"
                  class="image-item"
                  @click.stop
                >
                  <template #placeholder>
                    <div class="image-placeholder">
                      <el-icon class="is-loading"><Loading /></el-icon>
                      <span>图片加载中...</span>
                    </div>
                  </template>
                  <template #error>
                    <div class="image-error">
                      <el-icon><Picture /></el-icon>
                      <span>加载失败</span>
                    </div>
                  </template>
                </el-image>
              </div>
            </div>
          </div>
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
import { ref, nextTick } from 'vue'
import { User, MagicStick, Loading, Promotion, Picture } from '@element-plus/icons-vue'
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

  try {
    // 发送消息并处理非流式响应
    const response = await sendChatMessage(msg, chatStore.currentSessionId)
    
    // 添加助手消息（包含文本和图片）
    chatStore.addAssistantMessage(response.message, response.images, response.advice)
    scrollToBottom()
  } catch (error) {
    // 添加错误消息
    chatStore.addAssistantMessage(`抱歉，出错了：${error instanceof Error ? error.message : '未知错误'}`, [])
    scrollToBottom()
  }
}
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

/* 用户消息样式 */
.user-message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-direction: row-reverse;
}

.user-message .message-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  background-color: #409eff;
  color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.user-message .message-role {
  font-size: 12px;
  color: #e0e0e0;
  margin-bottom: 4px;
}

/* 助手消息样式 - 左右布局 */
.assistant-message {
  display: flex;
  gap: 20px;
  margin-bottom: 24px;
}

.message-left {
  flex: 1;
  display: flex;
  gap: 12px;
}

.message-left .message-content {
  flex: 1;
  max-width: 100%;
  padding: 12px 16px;
  border-radius: 12px;
  background-color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.message-role {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.message-text {
  line-height: 1.6;
  white-space: pre-wrap;
}

.message-avatar {
  flex-shrink: 0;
}

/* 右侧图片区域 */
.message-right {
  width: 320px;
  flex-shrink: 0;
}

.image-gallery {
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.gallery-title {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background-color: #67c23a;
  color: white;
  font-weight: 500;
}

.gallery-hint {
  font-size: 12px;
  opacity: 0.8;
  margin-left: auto;
}

.image-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
}

.image-item {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  width: 100%;
  height: 200px;
  cursor: pointer;
  transition: transform 0.3s ease;
}

.image-item:hover {
  transform: scale(1.02);
}

.image-placeholder,
.image-error {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: #f5f7fa;
  color: #909399;
  gap: 8px;
}

.image-placeholder .el-icon,
.image-error .el-icon {
  font-size: 24px;
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
