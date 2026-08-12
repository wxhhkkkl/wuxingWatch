import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import FortuneStrip from '../src/components/FortuneStrip.vue'
import {
  defaultDayunIndex,
  defaultLiunianYear,
  defaultLiuriDate,
  defaultLiuyueBranch,
  shichenZhiOf,
} from '../src/utils/selection'
import type { DaYunStep } from '../src/types'

const mkLn = (year: number) => ({
  year,
  gan: '丙',
  zhi: '午',
  ganzhi: '丙午',
  gan_shishen: '七杀',
  zhi_shishen: '正官',
})

const step = (ganzhi: string, start: number, age: number): DaYunStep => ({
  ganzhi,
  start_year: start,
  end_year: start + 9, // 含端点：共 10 年
  gan: ganzhi[0],
  zhi: ganzhi[1],
  gan_shishen: '偏财',
  zhi_shishen: '偏印',
  start_age_xu: age,
  liu_nian: Array.from({ length: 10 }, (_, i) => mkLn(start + i)),
})

const steps = [step('甲辰', 1995, 9), step('癸卯', 2005, 19), step('壬寅', 2015, 29)]
const currentYear = new Date().getFullYear()
// 保证有一步覆盖当前年
const stepsWithCurrent = [
  step('甲辰', currentYear - 20, 9),
  step('癸卯', currentYear - 10, 19),
  step('壬寅', currentYear, 29),
]

describe('FortuneStrip', () => {
  it('renders all dayun steps with years and 虚岁', () => {
    const wrapper = mount(FortuneStrip, {
      props: { steps, selectedDayunIndex: 0, selectedLiunianYear: 1995 },
    })
    expect(wrapper.findAll('.fs-dayun-item').length).toBe(3)
    expect(wrapper.text()).toContain('甲辰')
    expect(wrapper.text()).toContain('1995')
    expect(wrapper.text()).toContain('9岁')
  })

  it('emits select-dayun on click and shows that step liunian years', async () => {
    const wrapper = mount(FortuneStrip, {
      props: { steps, selectedDayunIndex: 0, selectedLiunianYear: 1995 },
    })
    expect(wrapper.findAll('.fs-liunian-item')[0].text()).toContain('1995')
    await wrapper.findAll('.fs-dayun-item')[1].trigger('click')
    expect(wrapper.emitted('select-dayun')![0]).toEqual([1])
    // 父组件更新选中后，流年横条切换
    await wrapper.setProps({ selectedDayunIndex: 1, selectedLiunianYear: 2005 })
    expect(wrapper.findAll('.fs-liunian-item')[0].text()).toContain('2005')
    expect(wrapper.findAll('.fs-liunian-item').length).toBe(10)
  })

  it('highlights selected dayun and current year', () => {
    const wrapper = mount(FortuneStrip, {
      props: {
        steps: stepsWithCurrent,
        selectedDayunIndex: 2,
        selectedLiunianYear: currentYear,
      },
    })
    expect(wrapper.findAll('.fs-dayun-item')[2].classes()).toContain('active')
    const current = wrapper.findAll('.fs-liunian-item').find((el) => el.text().includes(String(currentYear)))
    expect(current!.classes()).toContain('current')
  })

  it('emits select-liunian when a year cell is clicked', async () => {
    const wrapper = mount(FortuneStrip, {
      props: { steps, selectedDayunIndex: 0, selectedLiunianYear: 1995 },
    })
    await wrapper.findAll('.fs-liunian-item')[2].trigger('click')
    expect(wrapper.emitted('select-liunian')![0]).toEqual([1997])
  })

  it('degrades gracefully in sizhu mode (no years)', () => {
    const sizhuSteps = [{ ganzhi: '甲辰', start_year: null, end_year: null }]
    const wrapper = mount(FortuneStrip, {
      props: { steps: sizhuSteps, selectedDayunIndex: 0, selectedLiunianYear: null },
    })
    expect(wrapper.text()).toContain('甲辰')
    expect(wrapper.findAll('.fs-liunian-item').length).toBe(0)
  })

  // ---------- US3: 起运描述与当前虚岁 ----------

  it('shows 起运描述 precise to hour and 交运信息', () => {
    const wrapper = mount(FortuneStrip, {
      props: {
        steps,
        selectedDayunIndex: 0,
        selectedLiunianYear: 1995,
        startAge: 8,
        startMonth: 4,
        startDay: 10,
        startHour: 0,
        birthYear: 1987,
        jiaoYun: { year_gan: '乙', jie: '寒露', days: 1, hours: 23, first_year: 2005 },
      },
    })
    expect(wrapper.text()).toMatch(/出生后 8 年 4 月\s*10 天 0 时起运/)
    expect(wrapper.text()).toContain(`${currentYear - 1987 + 1}岁`)
    expect(wrapper.text()).toContain('交运：逢乙年 寒露后1天23小时交大运')
  })

  it('hides 起运行 when birth year unknown (四柱输入)', () => {
    const wrapper = mount(FortuneStrip, {
      props: { steps, selectedDayunIndex: 0, selectedLiunianYear: 1995 },
    })
    expect(wrapper.text()).not.toContain('起运')
  })

  // ---------- 流月/流日/流时下钻横条 ----------

  const liuyue = [
    {
      branch: '寅', label: '寅月', ganzhi: '庚寅', gan: '庚', zhi: '寅',
      gan_shishen: '比肩', zhi_shishen: '偏财',
      start: '2026-02-04T04:02:08', end: '2026-03-05T21:59:00',
    },
    {
      branch: '卯', label: '卯月', ganzhi: '辛卯', gan: '辛', zhi: '卯',
      gan_shishen: '劫财', zhi_shishen: '正财',
      start: '2026-03-05T21:59:00', end: '2026-04-05T02:40:00',
    },
  ]
  const p2 = (n: number) => String(n).padStart(2, '0')
  const now = new Date()
  const todayStr = `${now.getFullYear()}-${p2(now.getMonth() + 1)}-${p2(now.getDate())}`
  const liuri = [
    { date: '2026-02-04', ganzhi: '己酉', gan: '己', zhi: '酉', gan_shishen: '正印', hours: [] },
    { date: todayStr, ganzhi: '庚戌', gan: '庚', zhi: '戌', gan_shishen: '比肩', hours: [] },
  ]
  const liushi = [
    { zhi: '子', ganzhi: '甲子', gan_shishen: '偏财' },
    { zhi: '丑', ganzhi: '乙丑', gan_shishen: '正财' },
  ]
  const baseProps = { steps, selectedDayunIndex: 0, selectedLiunianYear: 1995 }

  it('renders 流月 strip and emits select-liuyue', async () => {
    const wrapper = mount(FortuneStrip, {
      props: { ...baseProps, liuyue, selectedLiuyueBranch: '寅' },
    })
    const items = wrapper.findAll('.fs-liuyue-item')
    expect(items.length).toBe(2)
    expect(items[0].text()).toContain('寅月')
    expect(items[0].classes()).toContain('active')
    await items[1].trigger('click')
    expect(wrapper.emitted('select-liuyue')![0]).toEqual(['卯'])
  })

  it('renders 流日 strip with today highlighted and emits select-liuri', async () => {
    const wrapper = mount(FortuneStrip, {
      props: { ...baseProps, liuri, selectedLiuriDate: '2026-02-04' },
    })
    const items = wrapper.findAll('.fs-liuri-item')
    expect(items.length).toBe(2)
    expect(items[0].classes()).toContain('active')
    expect(items[1].classes()).toContain('current')
    await items[1].trigger('click')
    expect(wrapper.emitted('select-liuri')![0]).toEqual([todayStr])
  })

  it('renders 流时 strip and emits select-liushi', async () => {
    const wrapper = mount(FortuneStrip, {
      props: { ...baseProps, liushi, selectedLiushiZhi: '子' },
    })
    const items = wrapper.findAll('.fs-liushi-item')
    expect(items.length).toBe(2)
    expect(items[0].text()).toContain('子时')
    expect(items[0].text()).toContain('甲子')
    await items[1].trigger('click')
    expect(wrapper.emitted('select-liushi')![0]).toEqual(['丑'])
  })

  it('shows loading hint instead of the strip being fetched', () => {
    const wrapper = mount(FortuneStrip, {
      props: { ...baseProps, loadingLevel: 'month', liuyue },
    })
    expect(wrapper.text()).toContain('流月加载中')
    expect(wrapper.findAll('.fs-liuyue-item').length).toBe(0)
  })

  it('renders no cascade strips when lists are absent', () => {
    const wrapper = mount(FortuneStrip, { props: baseProps })
    expect(wrapper.findAll('.fs-liuyue-item, .fs-liuri-item, .fs-liushi-item').length).toBe(0)
  })
})

describe('default selection (utils/selection)', () => {
  it('picks the step containing the current year', () => {
    expect(defaultDayunIndex(stepsWithCurrent, currentYear)).toBe(2)
    expect(defaultDayunIndex(stepsWithCurrent, currentYear - 10)).toBe(1)
  })

  it('falls back to the first step when not yet 起运 (U2)', () => {
    expect(defaultDayunIndex(steps, currentYear)).toBe(0) // steps 止于 2025，当前年不在区间
  })

  it('defaults liunian year to current year within the step, else first year', () => {
    expect(defaultLiunianYear(stepsWithCurrent[2], currentYear)).toBe(currentYear)
    expect(defaultLiunianYear(steps[0], currentYear)).toBe(1995)
  })

  it('defaultLiuyueBranch picks the 节气月 containing now', () => {
    const months = [
      { branch: '寅', start: '2026-02-04T04:02:08', end: '2026-03-05T21:59:00' },
      { branch: '卯', start: '2026-03-05T21:59:00', end: '2026-04-05T02:40:00' },
    ]
    expect(defaultLiuyueBranch(months, new Date('2026-02-04T04:02:08'))).toBe('寅')
    expect(defaultLiuyueBranch(months, new Date('2026-03-05T21:59:00'))).toBe('卯')
    expect(defaultLiuyueBranch(months, new Date('2026-05-01T00:00:00'))).toBeNull()
  })

  it('defaultLiuriDate picks today when listed, else null', () => {
    const p = (n: number) => String(n).padStart(2, '0')
    const now = new Date()
    const today = `${now.getFullYear()}-${p(now.getMonth() + 1)}-${p(now.getDate())}`
    expect(defaultLiuriDate([{ date: '1990-01-01' }, { date: today }], now)).toBe(today)
    expect(defaultLiuriDate([{ date: '1990-01-01' }], now)).toBeNull()
  })

  it('shichenZhiOf maps hours to 时支', () => {
    expect(shichenZhiOf(0)).toBe('子')
    expect(shichenZhiOf(23)).toBe('子')
    expect(shichenZhiOf(1)).toBe('丑')
    expect(shichenZhiOf(13)).toBe('未')
    expect(shichenZhiOf(22)).toBe('亥')
  })
})
