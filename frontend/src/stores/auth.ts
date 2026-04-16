import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { authApi, type UserInfo } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserInfo | null>(null)
  const isLoggedIn = computed(() => !!localStorage.getItem('access_token'))

  async function login(employeeId: string, password: string) {
    const res = await authApi.login(employeeId, password)
    localStorage.setItem('access_token', res.data.access_token)
    localStorage.setItem('refresh_token', res.data.refresh_token)
    await fetchMe()
  }

  async function fetchMe() {
    const res = await authApi.me()
    user.value = res.data
  }

  function logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    user.value = null
  }

  return { user, isLoggedIn, login, fetchMe, logout }
})
