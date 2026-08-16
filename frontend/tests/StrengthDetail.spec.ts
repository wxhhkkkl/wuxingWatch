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

const wangduSteps = [
  {
    key: 'static', title: '静态旺度', rule: '藏干度数×月令系数',
    traces: [{ target: '火', expression: '天干丁×2 = 2 度；巳中丙 3 度', value: 6 }],
    result: '火：6 度 × 0.7 = 4.2 度',
  },
  {
    key: 'zhichong', title: '地支刑冲合害修正', rule: '相邻方论',
    traces: [{ target: '', expression: '巳申合绊：巳−1', value: null }],
    result: '巳申合绊：巳−1',
  },
  {
    key: 'final', title: '最终旺度与旺衰等级', rule: '对照分类表',
    traces: [{ target: '火', expression: '火 4.2 度 → 较弱', value: 4.2 }],
    result: '日主丁（火）4.2 度 → 较弱',
  },
  {
    key: 'dayun', title: '当前大运介入', rule: '运支状态增减',
    traces: [], result: '随当前选中大运展示',
  },
  {
    key: 'yongshen', title: '取用神与喜忌结论', rule: '正格扶抑',
    traces: [{ target: '格局用神', expression: '身弱取生扶', value: '木' }],
    result: '用神 木',
  },
]

const dayunAdjustments = [
  {
    ganzhi: '癸亥', start_year: 2030, start_age_xu: 5,
    deltas: [{ target: '木', expression: '运支亥为木之相地 +1', value: 1 }],
    scores_after: { 木: 12, 火: 4.2, 土: 2, 金: 3, 水: 1 },
    level_after: '偏旺',
  },
  {
    ganzhi: '壬戌', start_year: 2040, start_age_xu: 15,
    deltas: [{ target: '木', expression: '运支戌为木之囚地 −1.5', value: -1.5 }],
    scores_after: { 木: 7.5, 火: 4.2, 土: 2, 金: 3, 水: 1 },
    level_after: '偏弱',
  },
]

const withWangdu = {
  ...mockResult,
  xi_yong: {
    ...mockResult.xi_yong,
    conclusion: {
      ...mockResult.xi_yong.conclusion,
      tiaohou_yong_shen: { element: null, basis: '八月不需调候' },
      summary: '较弱·正格',
      basis: { yong_shen: '身弱取生扶', tiaohou: '八月不需调候' },
    },
    strength: {
      method: 'sizhu-jingsui',
      level: '较弱',
      day_master: '丁',
      day_master_wuxing: '火',
      static_scores: { 木: 3.5, 火: 4.9, 土: 2.0, 金: 3.0, 水: 1.0 },
      final_scores: { 木: 3.5, 火: 4.2, 土: 2.0, 金: 3.0, 水: 1.0 },
      ge_ju: { type: 'zheng', hua_shen: null, basis: ['日主丁火 4.2 度（较弱），有根能独立'], neng_duli: true },
      steps: wangduSteps,
      dayun_adjustments: dayunAdjustments,
    },
  },
} as never

describe('StrengthDetail（旺度法）', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    back.mockClear()
    push.mockClear()
  })

  it('renders verdict and step cards with full numeric traces', () => {
    useChartStore().set(withWangdu as never, mockInputs)
    const wrapper = mount(StrengthDetail)
    expect(wrapper.find('[data-testid="strength-level"]').text()).toBe('较弱')
    expect(wrapper.text()).toContain('正格')
    // 步骤卡片含完整数值轨迹
    expect(wrapper.text()).toContain('静态旺度')
    expect(wrapper.text()).toContain('巳申合绊：巳−1')
    expect(wrapper.text()).toContain('4.2')
  })

  it('renders dayun step from the selected dayun adjustment and updates on switch', async () => {
    const store = useChartStore()
    store.set(withWangdu as never, mockInputs)
    store.setViewingDayun('癸亥')
    const wrapper = mount(StrengthDetail)
    expect(wrapper.text()).toContain('癸亥')
    expect(wrapper.text()).toContain('运支亥为木之相地 +1')
    expect(wrapper.text()).toContain('偏旺')
    // 切换大运 → 该步内容更新
    store.setViewingDayun('壬戌')
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('壬戌')
    expect(wrapper.text()).toContain('运支戌为木之囚地 −1.5')
    // 喜忌结论不随大运变化（结论区不在本页改动，等级标签仍为原局判定）
    expect(wrapper.find('[data-testid="strength-level"]').text()).toBe('较弱')
  })

  it('falls back to current-year dayun when none selected', () => {
    const store = useChartStore()
    store.set(withWangdu as never, mockInputs)
    store.setViewingDayun(null)
    const wrapper = mount(StrengthDetail)
    // 当前年份(2026)不在任何 step 区间 → 回退第一步
    expect(wrapper.text()).toContain('癸亥')
  })

  it('shows legacy hint for old-format strength data', () => {
    const withLegacy = {
      ...mockResult,
      xi_yong: {
        ...mockResult.xi_yong,
        strength: {
          level: '偏旺', classification: '身强', cong_ge: false,
          day_master: '乙', day_master_wuxing: '木', day_master_score: 132.4, balance_line: 109,
          scores: { 木: 132.4 }, steps: [],
        },
      },
    } as never
    useChartStore().set(withLegacy as never, mockInputs)
    const wrapper = mount(StrengthDetail)
    expect(wrapper.text()).toContain('旧版口径')
  })

  it('shows an empty state when no strength data', () => {
    const wrapper = mount(StrengthDetail)
    expect(wrapper.text()).toContain('暂无强弱分析数据')
  })
})
