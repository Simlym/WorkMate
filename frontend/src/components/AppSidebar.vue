<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { useConversationsStore } from '@/stores/conversations'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const store = useConversationsStore()
const router = useRouter()

const renameId = ref<number | null>(null)
const renameValue = ref('')

onMounted(async () => {
  await auth.fetchMe().catch(() => {})
  await store.fetchList()
})

async function handleNew() {
  await store.createConversation()
}

async function handleSelect(id: number) {
  if (store.activeId !== id) {
    await store.selectConversation(id)
  }
}

function startRename(conv: { id: number; title: string }) {
  renameId.value = conv.id
  renameValue.value = conv.title
}

async function submitRename(id: number) {
  if (renameValue.value.trim()) {
    await store.renameConversation(id, renameValue.value.trim())
  }
  renameId.value = null
}

async function handleDelete(id: number) {
  await ElMessageBox.confirm('确认删除这个对话？', '提示', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning',
  })
  await store.deleteConversation(id)
  ElMessage.success('已删除')
}

async function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="sidebar">
    <div class="sidebar-header">
      <span class="brand">WorkMate</span>
      <el-button type="primary" plain size="small" @click="handleNew">+ 新对话</el-button>
    </div>

    <div class="conv-list">
      <div
        v-for="conv in store.list"
        :key="conv.id"
        class="conv-item"
        :class="{ active: store.activeId === conv.id }"
        @click="handleSelect(conv.id)"
      >
        <template v-if="renameId === conv.id">
          <el-input
            v-model="renameValue"
            size="small"
            @blur="submitRename(conv.id)"
            @keyup.enter="submitRename(conv.id)"
            @click.stop
            autofocus
          />
        </template>
        <template v-else>
          <span class="conv-title">{{ conv.title }}</span>
          <div class="conv-actions" @click.stop>
            <el-button
              text
              size="small"
              @click="startRename(conv)"
            >✏️</el-button>
            <el-button
              text
              size="small"
              @click="handleDelete(conv.id)"
            >🗑️</el-button>
          </div>
        </template>
      </div>

      <div v-if="store.list.length === 0" class="empty-conv">
        <p>暂无对话</p>
      </div>
    </div>

    <div class="sidebar-footer">
      <div class="user-info">
        <el-avatar size="small" style="background:#409eff;flex-shrink:0">
          {{ auth.user?.display_name?.charAt(0) || '?' }}
        </el-avatar>
        <span class="username">{{ auth.user?.display_name || auth.user?.employee_id }}</span>
      </div>
      <div class="footer-actions">
        <el-button v-if="auth.user?.is_admin" text size="small" @click="router.push('/admin')" title="管理后台">⚙</el-button>
        <el-button text size="small" @click="handleLogout">退出</el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sidebar {
  width: 260px;
  height: 100%;
  background: #f7f7f8;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}
.sidebar-header {
  padding: 16px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e8e8e8;
}
.brand {
  font-weight: 700;
  font-size: 16px;
  color: #1a1a1a;
}
.conv-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 6px;
}
.conv-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: #333;
  transition: background 0.15s;
  margin-bottom: 2px;
  min-height: 36px;
}
.conv-item:hover {
  background: #ebebec;
}
.conv-item.active {
  background: #e1e3e8;
  font-weight: 500;
}
.conv-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.conv-actions {
  display: none;
  gap: 2px;
}
.conv-item:hover .conv-actions,
.conv-item.active .conv-actions {
  display: flex;
}
.empty-conv {
  text-align: center;
  color: #aaa;
  font-size: 13px;
  padding: 24px 0;
}
.sidebar-footer {
  padding: 12px;
  border-top: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.footer-actions {
  display: flex;
  align-items: center;
  gap: 2px;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow: hidden;
}
.username {
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
