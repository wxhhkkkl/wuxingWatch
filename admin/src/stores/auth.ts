import { defineStore } from 'pinia'
import { login as apiLogin, type AdminUser } from '../api/auth'
import { request, setAccessToken } from '../api/client'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as AdminUser | null,
  }),
  getters: {
    isAdmin: (s) => s.user !== null,
  },
  actions: {
    async login(phone: string, password: string) {
      const data = await apiLogin(phone, password)
      const me = await request<{ role: string }>('/api/me')
      if (me.role !== 'admin') throw new Error('该账号无管理员权限')
      this.user = data.user
    },
    logout() {
      setAccessToken(null)
      this.user = null
    },
  },
})
