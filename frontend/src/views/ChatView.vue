<script setup lang="ts">
import AppSidebar from '@/components/AppSidebar.vue'
import ChatPanel from '@/components/ChatPanel.vue'
</script>

<template>
  <div class="chat-layout">
    <AppSidebar />
    <ChatPanel />
  </div>
</template>

<style scoped>
.chat-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}
</style>
