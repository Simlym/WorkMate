<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import MessageItem from './MessageItem.vue'
import type { MessageOut } from '@/api/conversations'

const props = defineProps<{ messages: MessageOut[] }>()

const container = ref<HTMLElement>()

function scrollToBottom() {
  nextTick(() => {
    if (container.value) {
      container.value.scrollTop = container.value.scrollHeight
    }
  })
}

watch(() => props.messages.length, scrollToBottom)
watch(() => props.messages[props.messages.length - 1]?.content, scrollToBottom)

defineExpose({ scrollToBottom })
</script>

<template>
  <div ref="container" class="message-list">
    <div v-if="messages.length === 0" class="empty-tip">
      <p>选择一个功能，开始对话</p>
    </div>
    <MessageItem
      v-for="msg in messages"
      :key="msg.id"
      :message="msg"
    />
  </div>
</template>

<style scoped>
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.empty-tip {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #aaa;
  font-size: 14px;
}
</style>
