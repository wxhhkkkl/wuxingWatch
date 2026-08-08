import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

const replace = vi.fn()
const login = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn(), replace }),
}))

vi.mock('../src/stores/auth', () => ({
  useAuthStore: () => ({ login, user: null, isAdmin: false, logout: vi.fn() }),
}))

import Login from '../src/pages/Login.vue'

const flush = () => new Promise((r) => setTimeout(r))

describe('Admin Login', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    replace.mockClear()
    login.mockReset()
  })

  it('renders admin login title', () => {
    const wrapper = mount(Login)
    expect(wrapper.text()).toContain('后台管理')
  })

  it('calls login with phone and password', async () => {
    login.mockResolvedValue(undefined)
    const wrapper = mount(Login)
    await flush()
    ;(wrapper.vm as unknown as { phone: string; password: string }).phone = '13800000000'
    ;(wrapper.vm as unknown as { password: string }).password = 'AdminPass123'
    const btn = wrapper.findAll('button').find((b) => b.text().trim() === '登录')
    await btn!.trigger('click')
    expect(login).toHaveBeenCalledWith('13800000000', 'AdminPass123')
  })
})
