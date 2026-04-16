import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'

vi.mock('@/api/auth', () => ({
  authApi: {
    login: vi.fn(),
    me: vi.fn(),
  },
}))

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('isLoggedIn is false when no token in localStorage', () => {
    const store = useAuthStore()
    expect(store.isLoggedIn).toBe(false)
  })

  it('isLoggedIn is true when access_token exists', () => {
    localStorage.setItem('access_token', 'fake-token')
    const store = useAuthStore()
    expect(store.isLoggedIn).toBe(true)
  })

  it('login stores tokens and sets user', async () => {
    vi.mocked(authApi.login).mockResolvedValue({
      data: { access_token: 'acc', refresh_token: 'ref', token_type: 'bearer' },
    } as any)
    vi.mocked(authApi.me).mockResolvedValue({
      data: { id: 1, employee_id: 'emp001', display_name: 'Alice', is_admin: false },
    } as any)

    const store = useAuthStore()
    await store.login('emp001', 'password')

    expect(localStorage.getItem('access_token')).toBe('acc')
    expect(localStorage.getItem('refresh_token')).toBe('ref')
    expect(store.user?.employee_id).toBe('emp001')
  })

  it('logout clears tokens and user', async () => {
    localStorage.setItem('access_token', 'tok')
    const store = useAuthStore()

    store.logout()

    expect(localStorage.getItem('access_token')).toBeNull()
    expect(store.user).toBeNull()
  })
})
