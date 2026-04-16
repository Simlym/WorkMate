<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const form = ref({ employeeId: '', password: '' })
const loading = ref(false)

async function handleLogin() {
  if (!form.value.employeeId || !form.value.password) {
    ElMessage.warning('请输入工号和密码')
    return
  }
  loading.value = true
  try {
    await auth.login(form.value.employeeId, form.value.password)
    router.push('/')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '登录失败，请检查工号或密码')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-box">
      <div class="login-header">
        <h1>WorkMate</h1>
        <p>企业 AI 助手</p>
      </div>

      <el-form @submit.prevent="handleLogin" label-position="top">
        <el-form-item label="工号">
          <el-input
            v-model="form.employeeId"
            placeholder="请输入工号"
            size="large"
            clearable
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-button
          type="primary"
          size="large"
          :loading="loading"
          style="width: 100%; margin-top: 8px"
          @click="handleLogin"
        >
          登录
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
}
.login-box {
  width: 380px;
  padding: 40px 36px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
}
.login-header {
  text-align: center;
  margin-bottom: 32px;
}
.login-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 4px;
}
.login-header p {
  color: #888;
  font-size: 14px;
}
</style>
