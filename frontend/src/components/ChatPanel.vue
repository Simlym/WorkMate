<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import MessageList from './MessageList.vue'
import MessageInput from './MessageInput.vue'
import FunctionSelector from './FunctionSelector.vue'
import { useConversationsStore } from '@/stores/conversations'
import { streamChat } from '@/api/chat'

const store = useConversationsStore()
const selectedFunction = ref<string | null>(null)
const loading = ref(false)
const msgList = ref<InstanceType<typeof MessageList>>()

watch(
  () => store.activeId,
  () => {
    selectedFunction.value = null
  },
)

async function handleSend(message: string) {
  if (!store.activeId) {
    await store.createConversation(selectedFunction.value ?? undefined)
  }

  const convId = store.activeId!

  // Add user message optimistically
  store.addMessage({
    id: Date.now(),
    role: 'user',
    content: message,
    tool_calls: null,
    created_at: new Date().toISOString(),
  })

  loading.value = true
  let assistantStarted = false

  try {
    for await (const event of streamChat(convId, message, selectedFunction.value)) {
      if (event.type === 'text' && typeof event.content === 'string') {
        if (!assistantStarted) {
          store.addMessage({
            id: Date.now() + 1,
            role: 'assistant',
            content: event.content,
            tool_calls: null,
            created_at: new Date().toISOString(),
          })
          assistantStarted = true
        } else {
          store.appendToLastAssistantMessage(event.content)
        }
      } else if (event.type === 'tool_call' && event.content && typeof event.content === 'object') {
        store.addToolCallToLastAssistant(event.content as import('@/api/chat').ToolCall)
      } else if (event.type === 'error') {
        ElMessage.error(String(event.content) || '请求失败')
      }
    }
    // Refresh conversation list to update title/order
    await store.fetchList()
  } catch (e: any) {
    ElMessage.error(e?.message || '网络错误')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="chat-panel">
    <div v-if="!store.activeId" class="welcome">
      <div class="welcome-inner">
        <h2>你好，我是 WorkMate</h2>
        <p>选择一个功能开始对话，或直接输入问题让 AI 自动判断</p>
        <FunctionSelector v-model="selectedFunction" />
        <el-button type="primary" size="large" style="margin-top:16px" @click="store.createConversation(selectedFunction ?? undefined)">
          开始对话
        </el-button>
      </div>
    </div>

    <template v-else>
      <div class="panel-header">
        <FunctionSelector v-model="selectedFunction" />
        <span class="conv-title-hint">{{ store.list.find(c => c.id === store.activeId)?.title }}</span>
      </div>
      <MessageList ref="msgList" :messages="store.messages" />
      <MessageInput :loading="loading" @send="handleSend" />
    </template>
  </div>
</template>

<style scoped>
.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  background: #fff;
}
.welcome {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
.welcome-inner {
  text-align: center;
  max-width: 440px;
}
.welcome-inner h2 {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 8px;
  color: #1a1a1a;
}
.welcome-inner p {
  color: #666;
  margin-bottom: 20px;
  font-size: 14px;
}
.panel-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 24px;
  border-bottom: 1px solid #f0f0f0;
  background: #fff;
}
.conv-title-hint {
  font-size: 13px;
  color: #aaa;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
