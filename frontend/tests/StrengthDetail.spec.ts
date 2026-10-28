import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { mockResult } from './fixtures'

const back = vi.fn()
const push = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({ back, push }),
  useRoute: () => ({ query: {} }),
}))

import { useChartStore } from '../src/stores/chart'
import StrengthDetail from '../src/pages/StrengthDetail.vue'

function mountWith(result: unknown = mockResult) {
  setActivePinia(createPinia())
  useChartStore().result = result as never
  return mount(StrengthDetail)
}

describe('StrengthDetail — 原局旺度（精简版）', () => {
  beforeEach(() => {
    back.mockClear()
    push.mockClear()
  })

  it('renders level, day master and five element bars', () => {
    const w = mountWith()
    const verdict = w.find('[data-testid="strength-level"]')
    expect(verdict.exists()).toBe(true)
    expect(verdict.text()).toBe('偏弱')
    expect(w.text()).toContain('日主 乙')
    expect(w.text()).toContain('木')
    expect(w.findAll('.bar-row')).toHaveLength(5)
    expect(w.text()).toContain('静态旺度')
  })

  it('renders each step and its traces', () => {
    const w = mountWith()
    expect(w.find('[data-testid="wd-step-relations"]').exists()).toBe(true)
    expect(w.find('[data-testid="wd-step-total"]').exists()).toBe(true)
    expect(w.text()).toContain('六冲成立：子午冲')
    expect(w.text()).toContain('日主 乙（木）6 度 → 偏弱')
  })

  it('renders a step-end chart snapshot when the step carries one', () => {
    const withChart = JSON.parse(JSON.stringify(mockResult))
    withChart.wan_du.steps[0].chart = {
      pillars: [
        { key: 'year', label: '年柱', gan: '庚', gan_wx: '金', gan_original: null,
          ganzhi: '庚午', zhi: '午', zhi_wx: '火', hidden: [] },
        { key: 'month', label: '月柱', gan: '辛', gan_wx: '金', gan_original: null,
          ganzhi: '辛巳', zhi: '巳', zhi_wx: '火', hidden: [] },
        { key: 'day', label: '日柱', gan: '乙', gan_wx: '木', gan_original: null,
          ganzhi: '乙酉', zhi: '酉', zhi_wx: '金', hidden: [] },
        { key: 'time', label: '时柱', gan: '辛', gan_wx: '金', gan_original: null,
          ganzhi: '辛巳', zhi: '巳', zhi_wx: '火', hidden: [] },
      ],
    }
    const w = mountWith(withChart)
    expect(w.find('[data-testid="wd-step-chart-relations"]').exists()).toBe(true)
  })

  it('marks the original day stem when 五合 swapped it', () => {
    const swapped = JSON.parse(JSON.stringify(mockResult))
    swapped.wan_du.day_master = '丙'
    swapped.wan_du.day_master_original = '戊'
    swapped.wan_du.day_master_wuxing = '火'
    const w = mountWith(swapped)
    expect(w.text()).toContain('（原戊）')
  })

  it('shows an empty state when no wan_du exists', () => {
    const w = mountWith({ ...mockResult, wan_du: undefined })
    expect(w.text()).toContain('暂无原局旺度结果')
  })

  it('does not render removed sections', () => {
    const w = mountWith()
    for (const word of ['格局', '用神', '喜神', '忌神', '调候', '喜忌']) {
      expect(w.text()).not.toContain(word)
    }
  })
})
