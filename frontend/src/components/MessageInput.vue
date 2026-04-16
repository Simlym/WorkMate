<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{ send: [message: string] }>()

const props = defineProps<{ loading: boolean }>()

const input = ref('')

function handleSend() {
  const msg = input.value.trim()
  if (!msg || props.loading) return
  emit('send', msg)
  input.value = ''
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}
</script>

<template>
  <div class="input-area">
    <el-input
      v-model="input"
      type="textarea"
      :rows="3"
      placeholder="输入消息，Enter 发送，Shift+Enter 换行"
      resize="none"
      :disabled="loading"
      @keydown="handleKeydown"
    />
    <div class="input-actions">
      <span class="input-tip">Enter 发送 · Shift+Enter 换行</span>
      <el-button
        type="primary"
        :loading="loading"
        :disabled="!input.trim()"
        @click="handleSend"
      >
        发送
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.input-area {
  padding: 12px 24px 20px;
  border-top: 1px solid #e8e8e8;
  background: #fff;
}
.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}
.input-tip {
  font-size: 12px;
  color: #bbb;
}
</style>
