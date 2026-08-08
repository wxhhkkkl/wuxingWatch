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
    async loginPassword(phone: string, password: string) {
      const data = await request<{ access_token: string; user: User }>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ phone, password }),
      })
      setAccessToken(data.access_token)
      this.user = data.user
    },
    async register(phone: string, code: string, password: string) {
      const data = await request<{ access_token: string; user: User }>('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify({ phone, code, password }),
      })
      setAccessToken(data.access_token)
      this.user = data.user
    },
    async resetPassword(phone: string, code: string, password: string) {
      await request<void>('/api/auth/reset-password', {
        method: 'POST',
        body: JSON.stringify({ phone, code, password }),
      })
    },
    async sendCode(phone: string, intent: 'login' | 'register' | 'reset' = 'login') {
      await request<{ masked_phone: string; expires_in: number }>('/api/auth/send-code', {
        method: 'POST',
        body: JSON.stringify({ phone, intent }),
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
