import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import FortuneStrip from '../src/components/FortuneStrip.vue'
import { defaultDayunIndex, defaultLiunianYear } from '../src/utils/selection'
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

  it('shows 起运描述 and current 虚岁', () => {
    const wrapper = mount(FortuneStrip, {
      props: {
        steps,
        selectedDayunIndex: 0,
        selectedLiunianYear: 1995,
        startAge: 8,
        startMonth: 6,
        birthYear: 1987,
      },
    })
    expect(wrapper.text()).toContain('出生后 8 年 6 月起运')
    expect(wrapper.text()).toContain(`${currentYear - 1987 + 1}岁`)
  })

  it('hides 起运行 when birth year unknown (四柱输入)', () => {
    const wrapper = mount(FortuneStrip, {
      props: { steps, selectedDayunIndex: 0, selectedLiunianYear: 1995 },
    })
    expect(wrapper.text()).not.toContain('起运')
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
})
