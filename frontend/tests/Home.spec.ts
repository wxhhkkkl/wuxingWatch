import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

const push = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push, replace: vi.fn() }),
}))

vi.mock('../src/api/charts', () => ({
  predictChart: vi.fn(),
}))

import Home from '../src/pages/Home.vue'
import { predictChart } from '../src/api/charts'

const flush = () => new Promise((r) => setTimeout(r))

describe('Home', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    push.mockClear()
    vi.mocked(predictChart).mockReset()
  })

  it('renders the title and input form', () => {
    const wrapper = mount(Home)
    expect(wrapper.text()).toContain('五行 · 八字排盘')
    expect(wrapper.find('button').exists()).toBe(true)
  })

  it('shows leap-month option when switching to lunar', async () => {
    const wrapper = mount(Home)
    expect(wrapper.text()).not.toContain('闰月')
    ;(wrapper.vm as unknown as { calendar: string }).calendar = 'lunar'
    await flush()
    expect(wrapper.text()).toContain('闰月')
  })

  it('submits the form and navigates to the result page', async () => {
    vi.mocked(predictChart).mockResolvedValue({ day_master: '乙' } as never)
    const wrapper = mount(Home)
    await wrapper.find('button').trigger('click')
    await flush()
    expect(predictChart).toHaveBeenCalledTimes(1)
    expect(push).toHaveBeenCalledWith('/result')
  })

  it('shows an error toast when prediction fails', async () => {
    vi.mocked(predictChart).mockRejectedValue(new Error('排盘失败'))
    const wrapper = mount(Home)
    await wrapper.find('button').trigger('click')
    await flush()
    expect(push).not.toHaveBeenCalled()
  })

  // ---------- T103: 精确时辰开关 ----------

  it('shows the precise-shichen toggle in solar mode with known time', () => {
    const wrapper = mount(Home)
    expect(wrapper.text()).toContain('精确时辰')
  })

  it('hides the toggle in sizhu mode or when birth time is unknown', async () => {
    const wrapper = mount(Home)
    ;(wrapper.vm as unknown as { calendar: string }).calendar = 'sizhu'
    await flush()
    expect(wrapper.text()).not.toContain('精确时辰')
    ;(wrapper.vm as unknown as { calendar: string }).calendar = 'solar'
    ;(wrapper.vm as unknown as { unknownTime: boolean }).unknownTime = true
    await flush()
    expect(wrapper.text()).not.toContain('精确时辰')
  })

  it('submits precise_shichen: true when the toggle is on', async () => {
    vi.mocked(predictChart).mockResolvedValue({ day_master: '乙' } as never)
    const wrapper = mount(Home)
    ;(wrapper.vm as unknown as { preciseShichen: boolean }).preciseShichen = true
    await flush()
    await wrapper.find('button').trigger('click')
    await flush()
    const payload = vi.mocked(predictChart).mock.calls[0][0] as { precise_shichen?: boolean }
    expect(payload.precise_shichen).toBe(true)
  })

  it('omits precise_shichen when the toggle is off', async () => {
    vi.mocked(predictChart).mockResolvedValue({ day_master: '乙' } as never)
    const wrapper = mount(Home)
    await wrapper.find('button').trigger('click')
    await flush()
    const payload = vi.mocked(predictChart).mock.calls[0][0] as { precise_shichen?: boolean }
    expect(payload.precise_shichen).toBeFalsy()
  })

  it('persists the toggle for logged-in users and restores on reload', async () => {
    const { useAuthStore } = await import('../src/stores/auth')
    useAuthStore().user = { id: 1, phone: '13800000000' }
    vi.mocked(predictChart).mockResolvedValue({ day_master: '乙' } as never)
    const wrapper = mount(Home)
    ;(wrapper.vm as unknown as { preciseShichen: boolean }).preciseShichen = true
    await flush()
    expect(localStorage.getItem('precise_shichen')).toBe('true')
    wrapper.unmount()
    const wrapper2 = mount(Home)
    expect((wrapper2.vm as unknown as { preciseShichen: boolean }).preciseShichen).toBe(true)
  })

  it('does not persist the toggle for guests', async () => {
    localStorage.removeItem('precise_shichen')
    const wrapper = mount(Home)
    ;(wrapper.vm as unknown as { preciseShichen: boolean }).preciseShichen = true
    await flush()
    expect(localStorage.getItem('precise_shichen')).toBeNull()
  })
})
