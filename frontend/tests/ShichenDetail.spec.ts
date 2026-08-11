import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import type { ShichenDetail } from '../src/types'
import { mockResult } from './fixtures'

const push = vi.fn()
const back = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push, back, replace: vi.fn() }),
}))

import ShichenDetailPage from '../src/pages/ShichenDetail.vue'
import { useChartStore } from '../src/stores/chart'
import { mockInputs } from './fixtures'

const mkSegments = (): ShichenDetail['segments'] => {
  // 2020-06-21 北京：日出 04:46 → 次日日出 04:46，每段 60 分钟（测试简化）
  const base = new Date('2020-06-21T04:46:00').getTime()
  const order = ['卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑', '寅']
  return Array.from({ length: 24 }, (_, i) => ({
    index: i,
    start: new Date(base + i * 3600_000).toISOString(),
    end: new Date(base + (i + 1) * 3600_000).toISOString(),
    shichen: order[Math.floor(((i + 1) % 24) / 2)],
    alt_start: i * 2.5,
    alt_end: (i + 1) * 2.5,
  }))
}

const mkShichen = (over: Partial<ShichenDetail> = {}): ShichenDetail => ({
  applied: true,
  fallback: false,
  shichen: '卯',
  traditional_shichen: '卯',
  segment_index: 0,
  day_offset: 0,
  moments: {
    sunrise: '2020-06-21T04:46:00',
    sunset: '2020-06-21T19:46:00',
    solar_noon: '2020-06-21T12:16:00',
    solar_midnight: '2020-06-22T00:16:00',
    prev_sunrise: '2020-06-20T04:46:00',
    prev_noon: '2020-06-20T12:16:00',
    prev_sunset: '2020-06-20T19:46:00',
    next_sunrise: '2020-06-22T04:46:00',
  },
  segments: mkSegments(),
  ...over,
})

function mountWith(shichen: ShichenDetail | null) {
  const store = useChartStore()
  if (shichen) {
    store.set({ ...mockResult, shichen }, mockInputs)
  }
  return mount(ShichenDetailPage)
}

describe('ShichenDetail', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    push.mockClear()
  })

  it('renders step-by-step calculation from the store', () => {
    const wrapper = mountWith(mkShichen())
    const text = wrapper.text()
    expect(text).toContain('输入参数')
    expect(text).toContain('日出')
    expect(text).toContain('日落')
    expect(text).toContain('正午')
    expect(text).toContain('子夜')
    expect(text).toContain('四区间')
    expect(text).toContain('归属')
    // 24 段表格（含高度角列）
    expect(wrapper.findAll('.seg-row')).toHaveLength(24)
    expect(text).toContain('高度角')
  })

  it('highlights the birth segment', () => {
    const wrapper = mountWith(mkShichen({ segment_index: 7 }))
    const rows = wrapper.findAll('.seg-row')
    expect(rows[7].classes()).toContain('is-birth')
    expect(rows.filter((r) => r.classes().includes('is-birth'))).toHaveLength(1)
  })

  it('shows not-applied notice when precise mode was off', () => {
    const wrapper = mountWith(mkShichen({ applied: false }))
    expect(wrapper.text()).toContain('当前八字未采用此划分')
  })

  it('shows fallback notice for polar day/night', () => {
    const wrapper = mountWith(mkShichen({ fallback: true }))
    expect(wrapper.text()).toContain('均分模式')
  })

  it('shows night-zi day-rollover note when day_offset is 1', () => {
    const wrapper = mountWith(mkShichen({ day_offset: 1, shichen: '子' }))
    expect(wrapper.text()).toContain('夜子时')
  })

  it('shows empty state without shichen data', () => {
    const wrapper = mountWith(null)
    expect(wrapper.text()).toContain('去排盘')
  })
})
