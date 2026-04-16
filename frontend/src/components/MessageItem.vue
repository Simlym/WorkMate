<script setup lang="ts">
import { computed, ref } from 'vue'
import MarkdownIt from 'markdown-it'
import type { MessageOut } from '@/api/conversations'
import type { ToolCall } from '@/api/chat'

const props = defineProps<{ message: MessageOut }>()

const md = new MarkdownIt({ html: false, linkify: true, typographer: true })

const renderedContent = computed(() => md.render(props.message.content || ''))
const isUser = computed(() => props.message.role === 'user')
const toolCalls = computed<ToolCall[]>(() => {
  if (!props.message.tool_calls) return []
  return (Array.isArray(props.message.tool_calls)
    ? props.message.tool_calls
    : [props.message.tool_calls]) as ToolCall[]
})

// Track which tool calls are expanded
const expanded = ref<Record<number, boolean>>({})
const toggle = (i: number) => { expanded.value[i] = !expanded.value[i] }
</script>

<template>
  <div class="message-item" :class="{ 'is-user': isUser, 'is-assistant': !isUser }">
    <div class="message-avatar">
      <el-avatar v-if="isUser" size="small" style="background:#409eff">我</el-avatar>
      <el-avatar v-else size="small" style="background:#67c23a">AI</el-avatar>
    </div>
    <div class="message-bubble">
      <!-- Tool calls (shown before the assistant reply text) -->
      <div v-if="toolCalls.length" class="tool-calls">
        <div v-for="(tc, i) in toolCalls" :key="i" class="tool-call-block">
          <div class="tool-call-header" @click="toggle(i)">
            <el-icon class="tool-icon"><Connection /></el-icon>
            <span class="tool-name">{{ tc.tool }}</span>
            <el-icon class="expand-icon" :class="{ rotated: expanded[i] }"><ArrowRight /></el-icon>
          </div>
          <div v-if="expanded[i]" class="tool-call-body">
            <div v-if="tc.tool_input" class="tool-section">
              <div class="tool-section-label">输入</div>
              <pre class="tool-pre">{{ tc.tool_input }}</pre>
            </div>
            <div v-if="tc.observation" class="tool-section">
              <div class="tool-section-label">结果</div>
              <pre class="tool-pre">{{ tc.observation }}</pre>
            </div>
          </div>
        </div>
      </div>

      <!-- Message body -->
      <div v-if="isUser" class="message-text">{{ message.content }}</div>
      <div v-else class="markdown-body" v-html="renderedContent" />
    </div>
  </div>
</template>

<style scoped>
.message-item {
  display: flex;
  gap: 12px;
  padding: 8px 0;
}
.message-item.is-user {
  flex-direction: row-reverse;
}
.message-avatar {
  flex-shrink: 0;
}
.message-bubble {
  max-width: 70%;
}
.message-text {
  background: #409eff;
  color: #fff;
  padding: 10px 14px;
  border-radius: 12px 12px 2px 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}
.is-assistant .message-bubble {
  background: #f4f4f5;
  padding: 10px 14px;
  border-radius: 12px 12px 12px 2px;
}
.markdown-body {
  line-height: 1.7;
  word-break: break-word;
}
.markdown-body :deep(p) { margin: 0 0 8px; }
.markdown-body :deep(p:last-child) { margin-bottom: 0; }
.markdown-body :deep(pre) {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  font-size: 13px;
  margin: 8px 0;
}
.markdown-body :deep(code) {
  background: rgba(0,0,0,0.06);
  padding: 2px 4px;
  border-radius: 3px;
  font-size: 13px;
}
.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
}
.markdown-body :deep(ul), .markdown-body :deep(ol) { padding-left: 20px; margin: 6px 0; }
.markdown-body :deep(li) { margin: 2px 0; }
.markdown-body :deep(table) { border-collapse: collapse; margin: 8px 0; }
.markdown-body :deep(th), .markdown-body :deep(td) {
  border: 1px solid #ddd;
  padding: 6px 10px;
}
.markdown-body :deep(th) { background: #f0f0f0; }

/* Tool calls */
.tool-calls {
  margin-bottom: 8px;
}
.tool-call-block {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  margin-bottom: 6px;
  overflow: hidden;
  background: #fff;
  font-size: 13px;
}
.tool-call-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  cursor: pointer;
  background: #fafafa;
  user-select: none;
}
.tool-call-header:hover {
  background: #f0f2f5;
}
.tool-icon {
  color: #409eff;
}
.tool-name {
  flex: 1;
  font-weight: 500;
  color: #303133;
}
.expand-icon {
  color: #909399;
  transition: transform 0.2s;
}
.expand-icon.rotated {
  transform: rotate(90deg);
}
.tool-call-body {
  padding: 8px 10px;
  border-top: 1px solid #ebeef5;
}
.tool-section {
  margin-bottom: 6px;
}
.tool-section:last-child {
  margin-bottom: 0;
}
.tool-section-label {
  font-size: 11px;
  color: #909399;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}
.tool-pre {
  margin: 0;
  padding: 6px 8px;
  background: #f4f4f5;
  border-radius: 4px;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-word;
  color: #303133;
  max-height: 200px;
  overflow-y: auto;
}
</style>
