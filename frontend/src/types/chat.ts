/**
 * 聊天相关类型定义
 */

// 消息角色
export type MessageRole = 'user' | 'assistant' | 'system'

// 消息类型
export interface ChatMessage {
  id: string
  role: MessageRole
  content: string
  timestamp: number
  advice?: ClothingAdvice // 结构化穿搭建议
  images: string[] // 文生图返回的图片URL列表
  isStreaming?: boolean // 是否正在流式输出
}

// 穿搭建议（结构化）
export interface ClothingItem {
  name: string
  category: string
  color: string
  material?: string
  reason?: string
}

export interface ClothingAdvice {
  city: string
  date: string
  weather_summary: string
  occasion: string
  style: string
  tops: ClothingItem[]
  bottoms: ClothingItem[]
  outerwear: ClothingItem[]
  shoes: ClothingItem[]
  accessories: ClothingItem[]
  reason: string
  tips?: string
  color_scheme?: string
  temperature: number
  feels_like?: number
  temperature_advice?: string
}

// API 响应类型
export interface ChatResponse {
  session_id: string
  user_id: string
  message: string
  images: string[]
  advice?: ClothingAdvice
}

// 会话
export interface ChatSession {
  id: string
  title: string
  messages: ChatMessage[]
  createdAt: number
  updatedAt: number
}
