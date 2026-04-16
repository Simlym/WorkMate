const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export interface ToolCall {
  tool: string
  tool_input: string
  observation: string
}

export interface ChatEvent {
  type: 'text' | 'done' | 'error' | 'tool_call'
  content?: string | ToolCall
}

export async function* streamChat(
  conversationId: number,
  message: string,
  func?: string | null,
): AsyncGenerator<ChatEvent> {
  const token = localStorage.getItem('access_token')
  const resp = await fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ conversation_id: conversationId, message, function: func }),
  })

  if (!resp.ok) {
    yield { type: 'error', content: `HTTP ${resp.status}` }
    return
  }

  const reader = resp.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''

    for (const line of lines) {
      if (!line.startsWith('data:')) continue
      const raw = line.slice(5).trim()
      if (!raw) continue
      try {
        yield JSON.parse(raw) as ChatEvent
      } catch {
        // skip malformed
      }
    }
  }
}
