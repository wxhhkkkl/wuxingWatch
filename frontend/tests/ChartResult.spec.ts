import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { mockResult, mockInputs } from './fixtures'

const push = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push, replace: vi.fn() }),
}))

vi.mock('../src/api/records', () => ({ saveRecord: vi.fn() }))
vi.mock('../src/api/charts', () => ({ fetchChartImage: vi.fn() }))

import { useChartStore } from '../src/stores/chart'
import { useAuthStore } from '../src/stores/auth'
import ChartResult from '../src/pages/ChartResult.vue'

describe('ChartResult', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    push.mockClear()
  })

  it('renders chart sections when a result exists', () => {
    useChartStore().set(mockResult, mockInputs)
    const wrapper = mount(ChartResult)
    expect(wrapper.text()).toContain('四柱')
    expect(wrapper.text()).toContain('喜忌分析')
    expect(wrapper.text()).toContain('庚午')
    expect(wrapper.text()).toContain('身强')
  })

  it('shows an empty state when no result', () => {
    const wrapper = mount(ChartResult)
    expect(wrapper.text()).toContain('暂无排盘结果')
  })

  it('redirects to login when saving while logged out', async () => {
    useChartStore().set(mockResult, mockInputs)
    expect(useAuthStore().isLoggedIn).toBe(false)
    const wrapper = mount(ChartResult)
    await wrapper.findAll('button')[0].trigger('click')
    expect(push).toHaveBeenCalledWith('/login')
  })
})
