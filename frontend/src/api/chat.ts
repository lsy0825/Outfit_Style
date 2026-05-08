import type { ChatResponse } from '@/types/chat'

/**
 * 发送聊天消息（非流式）
 * 返回包含文本回复和图片列表的响应
 */
export async function sendChatMessage(
  message: string,
  sessionId: string = 'default'
): Promise<ChatResponse> {
  const response = await fetch('/v1/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message,
      session_id: sessionId
    })
  })

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  const data: ChatResponse = await response.json()
  return data
}
