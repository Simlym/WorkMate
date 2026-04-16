import { ref } from 'vue'
import { defineStore } from 'pinia'
import { conversationsApi, type ConversationOut, type MessageOut } from '@/api/conversations'
import type { ToolCall } from '@/api/chat'

export const useConversationsStore = defineStore('conversations', () => {
  const list = ref<ConversationOut[]>([])
  const activeId = ref<number | null>(null)
  const messages = ref<MessageOut[]>([])

  async function fetchList() {
    const res = await conversationsApi.list()
    list.value = res.data
  }

  async function createConversation(func?: string) {
    const res = await conversationsApi.create('新对话', func)
    list.value.unshift(res.data)
    activeId.value = res.data.id
    messages.value = []
    return res.data
  }

  async function selectConversation(id: number) {
    activeId.value = id
    const res = await conversationsApi.get(id)
    messages.value = res.data.messages
  }

  async function deleteConversation(id: number) {
    await conversationsApi.delete(id)
    list.value = list.value.filter((c) => c.id !== id)
    if (activeId.value === id) {
      activeId.value = null
      messages.value = []
    }
  }

  async function renameConversation(id: number, title: string) {
    await conversationsApi.update(id, { title })
    const conv = list.value.find((c) => c.id === id)
    if (conv) conv.title = title
  }

  function addMessage(msg: MessageOut) {
    messages.value.push(msg)
  }

  function updateLastAssistantMessage(content: string) {
    const last = [...messages.value].reverse().find((m) => m.role === 'assistant')
    if (last) last.content = content
  }

  function appendToLastAssistantMessage(chunk: string) {
    const last = [...messages.value].reverse().find((m) => m.role === 'assistant')
    if (last) {
      last.content += chunk
    } else {
      messages.value.push({
        id: Date.now(),
        role: 'assistant',
        content: chunk,
        tool_calls: null,
        created_at: new Date().toISOString(),
      })
    }
  }

  function addToolCallToLastAssistant(tc: ToolCall) {
    const last = [...messages.value].reverse().find((m) => m.role === 'assistant')
    if (last) {
      if (!last.tool_calls) last.tool_calls = [] as unknown[]
      ;(last.tool_calls as unknown[]).push(tc)
    }
  }

  return {
    list,
    activeId,
    messages,
    fetchList,
    createConversation,
    selectConversation,
    deleteConversation,
    renameConversation,
    addMessage,
    appendToLastAssistantMessage,
    updateLastAssistantMessage,
    addToolCallToLastAssistant,
  }
})
