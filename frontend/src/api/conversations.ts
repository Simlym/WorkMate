import request from './request'

export interface ConversationOut {
  id: number
  title: string
  function: string | null
  created_at: string
  updated_at: string
}

export interface MessageOut {
  id: number
  role: string
  content: string
  tool_calls: unknown[] | null
  created_at: string
}

export interface ConversationDetail extends ConversationOut {
  messages: MessageOut[]
}

export const conversationsApi = {
  list: () => request.get<ConversationOut[]>('/conversations'),

  create: (title?: string, func?: string) =>
    request.post<ConversationOut>('/conversations', { title: title || '新对话', function: func }),

  get: (id: number) => request.get<ConversationDetail>(`/conversations/${id}`),

  update: (id: number, data: { title?: string; function?: string }) =>
    request.patch<ConversationOut>(`/conversations/${id}`, data),

  delete: (id: number) => request.delete(`/conversations/${id}`),
}
