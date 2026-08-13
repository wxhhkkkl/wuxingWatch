import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { mockResult, mockInputs } from './fixtures'

const back = vi.fn()
const push = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ back, push }),
}))

import { useChartStore } from '../src/stores/chart'
import StrengthDetail from '../src/pages/StrengthDetail.vue'

const nineSteps = [
  { title: '天干基础分', description: '同五行透干数量 × 36', values: { 木: 72, 金: 36 } },
  { title: '地支藏干基础分', description: '文档表 0', values: { 木: 120, 火: 100 } },
  { title: '天干坐支修正', description: '文档表 2', values: { 木: 66 } },
  { title: '天干间生克修正', description: '文档表 3/4', values: { 木: 1.2 } },
  { title: '有效根气（通根远近）', description: '藏干分 × 距离 × 状态', values: { 木: 96 } },
  { title: '月令权重', description: '文档表 5/6', values: { 木: 1.5 } },
  { title: '合冲刑会修正', description: '文档表 7', values: { 木: 1.0 } },
  { title: '标准化', description: 'W ÷ ΣW × 544', values: { 木: 132.4 } },
  { title: '旺衰等级判定', description: '日主分区间', values: { 木: 132.4 } },
]

const withStrength = {
  ...mockResult,
  xi_yong: {
    ...mockResult.xi_yong,
    strength: {
      level: '偏旺',
      classification: '身强',
      cong_ge: false,
      day_master: '乙',
      day_master_wuxing: '木',
      day_master_score: 132.4,
      balance_line: 109,
      scores: { 木: 132.4, 火: 98.2, 土: 120.1, 金: 95.3, 水: 98.0 },
      steps: nineSteps,
    },
  },
} as never

describe('StrengthDetail', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    back.mockClear()
    push.mockClear()
  })

  it('renders strength verdict and all nine steps', () => {
    useChartStore().set(withStrength as never, mockInputs)
    const wrapper = mount(StrengthDetail)
    expect(wrapper.find('[data-testid="strength-level"]').text()).toBe('偏旺')
    expect(wrapper.text()).toContain('身强')
    expect(wrapper.text()).toContain('日主得分'.slice(0, 2)) // 日主行
    // 9 步逐步卡片
    const cards = wrapper.findAll('.wx-card').filter((c) => c.text().includes('步'))
    expect(cards.length).toBe(9)
    expect(wrapper.text()).toContain('第 9 步 · 旺衰等级判定')
    expect(wrapper.text()).toContain('132.4')
  })

  it('navigates back when clicking the back arrow', async () => {
    useChartStore().set(withStrength as never, mockInputs)
    const wrapper = mount(StrengthDetail)
    await wrapper.find('.van-nav-bar__left').trigger('click')
    expect(back).toHaveBeenCalled()
  })

  it('shows an empty state when no strength data', () => {
    const wrapper = mount(StrengthDetail)
    expect(wrapper.text()).toContain('暂无强弱评分数据')
  })
})
