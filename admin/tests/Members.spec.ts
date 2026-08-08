import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn(), back: vi.fn(), replace: vi.fn() }),
}))

vi.mock('../src/stores/auth', () => ({
  useAuthStore: () => ({ user: { id: 1, phone: '13800000000' }, isAdmin: true, logout: vi.fn() }),
}))

vi.mock('../src/api/members', () => ({ listMembers: vi.fn() }))

import Members from '../src/pages/Members.vue'
import { listMembers } from '../src/api/members'

const flush = () => new Promise((r) => setTimeout(r))

describe('Admin Members', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.mocked(listMembers).mockReset()
  })

  it('renders member list with total and masked phone', async () => {
    vi.mocked(listMembers).mockResolvedValue({
      total: 1,
      items: [{ id: 1, phone_masked: '138****8000', created_at: '2026-08-08T00:00:00', chart_count: 2 }],
    })
    const wrapper = mount(Members)
    await flush()
    expect(wrapper.text()).toContain('会员总数：1')
    expect(wrapper.text()).toContain('138****8000')
  })

  it('calls listMembers with phone search', async () => {
    vi.mocked(listMembers).mockResolvedValue({ total: 0, items: [] })
    const wrapper = mount(Members)
    await flush()
    ;(wrapper.vm as unknown as { phone: string }).phone = '13800138000'
    await wrapper.findAll('button').find((b) => b.text() === '搜索')!.trigger('click')
    expect(listMembers).toHaveBeenCalledWith({ page: 1, page_size: 20, phone: '13800138000' })
  })
})
