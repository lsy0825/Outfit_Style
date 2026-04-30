import type { ChatResponse } from '@/types/chat'

/**
 * 发送聊天消息（SSE 流式）
 * 后端现在逐 token 推送 {type: "text_chunk", data: "token"}
 * 使用队列机制确保字符按顺序输出，避免乱序问题
 */
export async function sendChatMessage(
  message: string,
  sessionId: string = 'default',
  onChunk: (chunk: string) => void,
  onComplete: (fullMessage: string, advice?: any) => void,
  onError: (error: string) => void
): Promise<void> {
  // 字符输出队列
  const charQueue: string[] = []
  // 是否正在输出
  let isProcessing = false

  // 延迟函数
  const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

  // 处理队列中的字符（确保顺序）
  const processQueue = async () => {
    if (isProcessing) return
    isProcessing = true

    while (charQueue.length > 0) {
      const char = charQueue.shift()!
      onChunk(char)
      // 根据字符类型调整延迟
      const charDelay = char.match(/[\u4e00-\u9fa5]/) ? 50 : 20
      await delay(charDelay)
    }

    isProcessing = false
  }

  try {
    const response = await fetch('/v1/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream'
      },
      body: JSON.stringify({
        message,
        session_id: sessionId,
        stream: true
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('无法读取响应流')
    }

    const decoder = new TextDecoder()
    let buffer = ''
    let fullMessage = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim()
          if (data === '[DONE]') {
            // 等待队列处理完成后再调用 onComplete
            while (charQueue.length > 0 || isProcessing) {
              await delay(10)
            }
            onComplete(fullMessage)
            return
          }

          try {
            const parsed: ChatResponse = JSON.parse(data)

            if (parsed.type === 'text_chunk') {
              // 处理流式数据：支持单字符或多字符
              const text = parsed.data as string
              fullMessage += text
              
              // 将所有字符添加到队列
              for (const char of text) {
                charQueue.push(char)
              }
              // 启动队列处理（如果还没在处理）
              processQueue()
            } else if (parsed.type === 'structured') {
              // 等待队列处理完成后再调用 onComplete
              while (charQueue.length > 0 || isProcessing) {
                await delay(10)
              }
              onComplete(fullMessage, parsed.data)
              return
            } else if (parsed.type === 'text') {
              // 兼容旧格式：一次性收到整段文字
              const text = parsed.data as string
              fullMessage = text
              // 将所有字符添加到队列
              for (const char of text) {
                charQueue.push(char)
              }
              processQueue()
            } else if (parsed.type === 'error') {
              onError(parsed.data as string)
              return
            }
          } catch (e) {
            // 忽略无法解析的行（如心跳包）
            console.debug('SSE 解析跳过:', line)
          }
        }
      }
    }

    // 等待队列处理完成后再调用 onComplete
    while (charQueue.length > 0 || isProcessing) {
      await delay(10)
    }
    onComplete(fullMessage)
  } catch (error) {
    onError(error instanceof Error ? error.message : '未知错误')
  }
}

/**
 * 发送聊天消息（非流式）
 */
export async function sendChatMessageSync(
  message: string,
  sessionId: string = 'default'
): Promise<string> {
  const response = await fetch('/v1/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      stream: false
    })
  })

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  const data = await response.json()
  return data.message || '抱歉，我无法处理您的请求。'
}
