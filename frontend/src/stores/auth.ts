import { defineStore } from 'pinia'
import { request, setAccessToken } from '../api/client'
import type { User } from '../types'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null,
  }),
  getters: {
    isLoggedIn: (s) => s.user !== null,
  },
  actions: {
    async login(phone: string, code: string) {
      const data = await request<{ access_token: string; user: User }>('/api/auth/verify', {
        method: 'POST',
        body: JSON.stringify({ phone, code }),
      })
      setAccessToken(data.access_token)
      this.user = data.user
    },
    async sendCode(phone: string) {
      await request<{ masked_phone: string; expires_in: number }>('/api/auth/send-code', {
        method: 'POST',
        body: JSON.stringify({ phone }),
      })
    },
    async logout() {
      try {
        await request<void>('/api/auth/logout', { method: 'POST' })
      } finally {
        setAccessToken(null)
        this.user = null
      }
    },
  },
  persist: true,
})
