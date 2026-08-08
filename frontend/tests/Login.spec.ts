import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

const replace = vi.fn()
const login = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn(), replace }),
}))

vi.mock('../src/stores/auth', () => ({
  useAuthStore: () => ({ sendCode: vi.fn(), login, user: null, isLoggedIn: false }),
}))

import Login from '../src/pages/Login.vue'

describe('Login', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    replace.mockClear()
    login.mockReset()
  })

  it('renders phone and code fields', () => {
    const wrapper = mount(Login)
    expect(wrapper.text()).toContain('手机号登录')
  })

  it('calls login with phone and code', async () => {
    login.mockResolvedValue(undefined)
    const wrapper = mount(Login)
    ;(wrapper.vm as unknown as { phone: string; code: string }).phone = '13800138000'
    ;(wrapper.vm as unknown as { code: string }).code = '123456'
    const loginButton = wrapper.findAll('button').find((b) => b.text().includes('登录'))
    await loginButton!.trigger('click')
    expect(login).toHaveBeenCalledWith('13800138000', '123456')
  })
})
