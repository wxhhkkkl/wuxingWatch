import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

const replace = vi.fn()
const login = vi.fn()
const loginPassword = vi.fn()
const register = vi.fn()
const resetPassword = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn(), replace }),
}))

vi.mock('../src/stores/auth', () => ({
  useAuthStore: () => ({
    sendCode: vi.fn(),
    login,
    loginPassword,
    register,
    resetPassword,
    user: null,
    isLoggedIn: false,
  }),
}))

import Login from '../src/pages/Login.vue'

const flush = () => new Promise((r) => setTimeout(r))

describe('Login', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    replace.mockClear()
    login.mockReset()
    loginPassword.mockReset()
    register.mockReset()
    resetPassword.mockReset()
  })

  it('renders phone and code fields', () => {
    const wrapper = mount(Login)
    expect(wrapper.text()).toContain('手机号登录')
  })

  it('calls sms login with phone and code', async () => {
    login.mockResolvedValue(undefined)
    const wrapper = mount(Login)
    await flush()
    ;(wrapper.vm as unknown as { phone: string; code: string }).phone = '13800138000'
    ;(wrapper.vm as unknown as { code: string }).code = '123456'
    await wrapper.find('[data-testid="sms-login-btn"]').trigger('click')
    expect(login).toHaveBeenCalledWith('13800138000', '123456')
  })

  it('calls password login when switching to password tab', async () => {
    loginPassword.mockResolvedValue(undefined)
    const wrapper = mount(Login)
    ;(wrapper.vm as unknown as { tab: string }).tab = 'password'
    await flush()
    ;(wrapper.vm as unknown as { phone: string; password: string }).phone = '13800138000'
    ;(wrapper.vm as unknown as { password: string }).password = 'CorrectHorse99'
    await wrapper.find('[data-testid="pw-login-btn"]').trigger('click')
    expect(loginPassword).toHaveBeenCalledWith('13800138000', 'CorrectHorse99')
  })
})
