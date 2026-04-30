<template>
  <div id="app">
    <el-container class="app-container">
      <!-- 侧边栏 - 会话列表 -->
      <el-aside width="260px" class="sidebar">
        <div class="sidebar-header">
          <h2>StyleMate</h2>
          <el-button type="primary" @click="handleNewChat" :icon="Plus">
            新对话
          </el-button>
        </div>
        <div class="session-list">
          <div
            v-for="session in chatStore.sessions"
            :key="session.id"
            class="session-item"
            :class="{ active: session.id === chatStore.currentSessionId }"
            @click="chatStore.setCurrentSession(session.id)"
          >
            <el-icon><ChatDotRound /></el-icon>
            <span class="session-title">{{ session.title }}</span>
            <el-button
              type="danger"
              :icon="Delete"
              size="small"
              circle
              @click.stop="handleDeleteSession(session.id)"
            />
          </div>
        </div>
      </el-aside>

      <!-- 主内容区 -->
      <el-main class="main-content">
        <ChatWindow />
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { ChatDotRound, Plus, Delete } from '@element-plus/icons-vue'
import { useChatStore } from '@/stores/chat'
import ChatWindow from '@/components/ChatWindow.vue'

const chatStore = useChatStore()

onMounted(() => {
  // 初始化
})

function handleNewChat() {
  chatStore.createNewSession()
}

function handleDeleteSession(sessionId: string) {
  chatStore.deleteSession(sessionId)
}
</script>

<style scoped>
.app-container {
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  background-color: #f5f7fa;
  border-right: 1px solid #e4e7ed;
  padding: 20px;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.sidebar-header h2 {
  margin: 0;
  color: #409eff;
}

.session-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.session-item:hover {
  background-color: #e8f4ff;
}

.session-item.active {
  background-color: #d9ecff;
}

.session-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.main-content {
  padding: 0;
  overflow: hidden;
}
</style>

<style global>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
}
</style>
