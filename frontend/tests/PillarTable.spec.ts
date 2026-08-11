import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import PillarTable from '../src/components/PillarTable.vue'
import type { DaYunStep, LiuNianStep, Pillar, PillarDetail } from '../src/types'

const detail = (over: Partial<PillarDetail> = {}): PillarDetail => ({
  gan_shishen: '正官',
  zhi_shishen: '正财',
  cang_gan: [{ gan: '乙', shishen: '正财' }],
  xing_yun: '胎',
  zi_zuo: '病',
  xun_kong: '戌亥',
  na_yin: '炉中火',
  shen_sha: ['太极贵人', '飞刃'],
  ...over,
})

const pillar = (ganzhi: string, shishen: string, d?: PillarDetail): Pillar => ({
  ganzhi,
  gan: ganzhi[0],
  zhi: ganzhi[1],
  gan_wuxing: '火',
  zhi_wuxing: '木',
  shishen,
  detail: d,
})

const pillars = {
  year: pillar('丁卯', '正官', detail()),
  month: pillar('乙巳', '正财', detail({ gan_shishen: '正财' })),
  day: pillar('庚辰', '日主', detail({ gan_shishen: '元男' })),
  time: pillar('壬午', '食神', detail({ gan_shishen: '食神' })),
}

describe('PillarTable', () => {
  it('renders 4 pillars × full dimension rows', () => {
    const wrapper = mount(PillarTable, { props: { pillars } })
    const text = wrapper.text()
    for (const label of ['年柱', '月柱', '日柱', '时柱']) expect(text).toContain(label)
    for (const row of ['主星', '天干', '地支', '藏干', '星运', '自坐', '空亡', '纳音', '神煞']) {
      expect(text).toContain(row)
    }
    expect(text).toContain('元男') // 日柱主星
    expect(text).toContain('炉中火')
    expect(text).toContain('太极贵人')
    expect(text).toContain('戌亥')
  })

  it('colors 天干/地支 by wuxing', () => {
    const wrapper = mount(PillarTable, { props: { pillars } })
    const ganCell = wrapper.find('[data-testid="gan-day"]')
    expect(ganCell.attributes('style')).toContain('var(--wx-jin)') // 庚=金
    const zhiCell = wrapper.find('[data-testid="zhi-month"]')
    expect(zhiCell.attributes('style')).toContain('var(--wx-huo)') // 巳=火
  })

  it('shows placeholders when time pillar is null (时辰不详)', () => {
    const wrapper = mount(PillarTable, { props: { pillars: { ...pillars, time: null } } })
    const timeCells = wrapper.findAll('[data-testid^="main-time"]')
    expect(timeCells.length).toBeGreaterThan(0)
    expect(timeCells[0].text()).toBe('—')
  })

  it('falls back to — for legacy records without detail', () => {
    const legacy = pillar('庚午', '正官') // 无 detail
    const wrapper = mount(PillarTable, { props: { pillars: { ...pillars, year: legacy } } })
    expect(wrapper.find('[data-testid="main-year-xingyun"]').text()).toBe('—')
    expect(wrapper.find('[data-testid="main-year-shensha"]').text()).toBe('—')
    expect(wrapper.find('[data-testid="gan-year"]').text()).toBe('庚') // 干支仍显示
  })

  it('shows — when shen_sha is empty', () => {
    const noSs = pillar('癸未', '七杀', detail({ shen_sha: [] }))
    const wrapper = mount(PillarTable, { props: { pillars: { ...pillars, year: noSs } } })
    expect(wrapper.find('[data-testid="main-year-shensha"]').text()).toBe('—')
  })

  // ---------- 6 列联动（US2） ----------

  const dayun: DaYunStep = {
    ganzhi: '甲辰',
    start_year: 1995,
    end_year: 2005,
    gan: '甲',
    zhi: '辰',
    gan_shishen: '偏财',
    zhi_shishen: '偏印',
    start_age_xu: 9,
    detail: detail({ gan_shishen: '偏财' }),
  }
  const liunian: LiuNianStep = {
    year: 2026,
    gan: '丙',
    zhi: '午',
    ganzhi: '丙午',
    gan_shishen: '七杀',
    zhi_shishen: '正官',
    detail: detail({ gan_shishen: '七杀', na_yin: '天河水' }),
  }

  it('renders 6 columns with selected dayun/liunian', () => {
    const wrapper = mount(PillarTable, {
      props: { pillars, selectedDayun: dayun, selectedLiunian: liunian },
    })
    const headers = wrapper.findAll('.pt-col-header')
    expect(headers.map((h) => h.text())).toEqual(['流年', '大运', '年柱', '月柱', '日柱', '时柱'])
    expect(wrapper.text()).toContain('天河水') // 流年列内容
    expect(wrapper.find('[data-testid="gan-liunian"]').text()).toBe('丙')
    expect(wrapper.find('[data-testid="gan-dayun"]').text()).toBe('甲')
  })

  it('stays 4 columns when no selection provided (四柱输入模式)', () => {
    const wrapper = mount(PillarTable, { props: { pillars } })
    expect(wrapper.findAll('.pt-col-header').length).toBe(4)
  })
})
