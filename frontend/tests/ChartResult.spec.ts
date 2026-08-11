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
    expect(wrapper.text()).toContain('庚') // 年柱天干（明细表格分列渲染）
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
    const saveButton = wrapper.findAll('button').find((b) => b.text().includes('保存记录'))
    await saveButton!.trigger('click')
    expect(push).toHaveBeenCalledWith('/login')
  })

  it('真太阳时 row is clickable only when precise shichen applied', async () => {
    // 未开启精确时辰：不可点
    useChartStore().set(mockResult, mockInputs) // mockResult 无 shichen
    const wrapper = mount(ChartResult)
    const row = wrapper.find('[data-testid="row-true-solar"]')
    expect(row.classes()).not.toContain('is-link')
    await row.trigger('click')
    expect(push).not.toHaveBeenCalledWith('/shichen')

    // 开启后可点击跳转
    const withShichen = {
      ...mockResult,
      shichen: { applied: true, shichen: '巳', traditional_shichen: '巳' },
    } as never
    useChartStore().set(withShichen, mockInputs)
    const wrapper2 = mount(ChartResult)
    const row2 = wrapper2.find('[data-testid="row-true-solar"]')
    expect(row2.classes()).toContain('is-link')
    await row2.trigger('click')
    expect(push).toHaveBeenCalledWith('/shichen')
  })

  it('shows 出生节气/星座/星宿 rows when present, omits otherwise', () => {
    useChartStore().set(mockResult, mockInputs)
    const wrapper = mount(ChartResult)
    expect(wrapper.text()).not.toContain('出生节气')

    const withJieqi = {
      ...mockResult,
      jieqi: {
        prev: { name: '惊蛰', time: '1990-03-06T04:19:18', days: 25, hours: 19 },
        next: { name: '清明', time: '1990-04-05T09:12:56', days: 4, hours: 9 },
      },
      xing_zuo: '白羊座',
      xing_xiu: '虚宿北方玄武',
    } as never
    useChartStore().set(withJieqi, mockInputs)
    const wrapper2 = mount(ChartResult)
    expect(wrapper2.text()).toContain('出生于惊蛰后')
    expect(wrapper2.text()).toContain('清明前')
    expect(wrapper2.text()).toContain('白羊座')
    expect(wrapper2.text()).toContain('虚宿北方玄武')
    // 日出日落行已移除
    expect(wrapper2.text()).not.toContain('日出')
  })
})
