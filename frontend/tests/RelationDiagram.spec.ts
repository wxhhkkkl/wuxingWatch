import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import type { ChartResult, Pillar } from '../src/types'
import RelationDiagram from '../src/components/RelationDiagram.vue'

const mkPillar = (
  gan: string,
  zhi: string,
  ganWx: string,
  zhiWx: string,
  shishen: string,
  detail?: Pillar['detail'],
): Pillar => ({
  ganzhi: gan + zhi,
  gan,
  zhi,
  gan_wuxing: ganWx,
  zhi_wuxing: zhiWx,
  shishen,
  detail,
})

const mkResult = (opts: { time?: Pillar | null; day?: Pillar; year?: Pillar; month?: Pillar } = {}): ChartResult => {
  const time = opts.time !== undefined ? opts.time : mkPillar('辛', '巳', '金', '火', '正官')
  const day = opts.day ?? mkPillar('乙', '酉', '木', '金', '日主')
  const year = opts.year ?? mkPillar('庚', '午', '木', '火', '比肩')
  const month = opts.month ?? mkPillar('丙', '午', '火', '火', '七杀')
  return {
    solar_birth: '',
    true_solar_time: '',
    lunar_birth: '',
    pillars: { year, month, day, time },
    day_master: '乙',
    hidden_stems: { branch: '巳', hidden_stems: ['丙'], ruling_stem: '丙', source: '' },
    tai_yuan: '',
    ming_gong: null,
    shen_gong: null,
    da_yun: { start_age: null, start_month: null, steps: [] },
    liu_nian: [],
    xi_yong: {
      conclusion: { yong_shen: '', xi_shen: [], ji_shen: [], summary: '' },
      favorable_elements: [],
      avoid_elements: [],
      reasoning: '',
      ten_gods: {},
      direction: {},
      disclaimer: '',
    },
    missing_parts: [],
  } as ChartResult
}

const dayWithHidden = () =>
  mkPillar('乙', '酉', '木', '金', '日主', {
    gan_shishen: '日主',
    zhi_shishen: '七杀',
    cang_gan: [
      { gan: '辛', shishen: '七杀' },
      { gan: '丁', shishen: '食神' },
    ],
    xing_yun: '',
    zi_zuo: '',
    xun_kong: '',
    na_yin: '',
    shen_sha: [],
  })

// 关系夹具：年柱 甲(木)子(水)、月柱 己(土)亥(水)、日柱 乙(木)酉(金)、时柱 庚(金)巳(火)
const guanxiResult = (): ChartResult =>
  mkResult({
    year: mkPillar('甲', '子', '木', '水', '比肩'),
    month: mkPillar('己', '亥', '土', '水', '正财'),
    day: mkPillar('乙', '酉', '木', '金', '日主'),
    time: mkPillar('庚', '巳', '金', '火', '正官'),
  })

// ---------- 四 tab 结构 ----------

describe('RelationDiagram 四 tab', () => {
  it('renders the four tabs (关系/流通/宫位/六亲) and defaults to 关系', () => {
    const wrapper = mount(RelationDiagram, { props: { result: mkResult() } })
    for (const t of ['guanxi', 'liutong', 'gongwei', 'liuqin']) {
      expect(wrapper.find(`[data-testid="tab-${t}"]`).exists()).toBe(true)
    }
    expect(wrapper.find('[data-testid="tab-guanxi"]').text()).toBe('关系')
    expect(wrapper.find('[data-testid="panel-guanxi"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="panel-liutong"]').exists()).toBe(false)
  })
})

// ---------- 关系 tab：干支/藏干 连线图 ----------

describe('关系 tab', () => {
  it('renders bazi gan/zhi for the four pillars (干支 node text)', () => {
    const wrapper = mount(RelationDiagram, { props: { result: mkResult() } })
    for (const key of ['year', 'month', 'day', 'time']) {
      expect(wrapper.find(`[data-testid="node-gan-${key}"]`).exists()).toBe(true)
      expect(wrapper.find(`[data-testid="node-zhi-${key}"]`).exists()).toBe(true)
    }
    expect(wrapper.find('[data-testid="node-gan-year"]').text()).toBe('庚')
    expect(wrapper.find('[data-testid="node-zhi-year"]').text()).toBe('午')
  })

  it('includes 大运/流年 columns when selected, alongside the four pillars', () => {
    const dayun = { ganzhi: '庚午', start_year: 2020, end_year: 2029, gan: '庚', zhi: '午' }
    const liunian = { year: 2026, gan: '丙', zhi: '午', ganzhi: '丙午', gan_shishen: '七杀', zhi_shishen: '正官' }
    const wrapper = mount(RelationDiagram, {
      props: { result: mkResult(), selectedDayun: dayun as never, selectedLiunian: liunian as never },
    })
    // 六列：大运/流年/年/月/日/时 全部有干支节点
    for (const key of ['dayun', 'liunian', 'year', 'month', 'day', 'time']) {
      expect(wrapper.find(`[data-testid="node-gan-${key}"]`).exists()).toBe(true)
      expect(wrapper.find(`[data-testid="node-zhi-${key}"]`).exists()).toBe(true)
    }
    expect(wrapper.find('[data-testid="node-gan-dayun"]').text()).toBe('庚')
    expect(wrapper.find('[data-testid="node-gan-liunian"]').text()).toBe('丙')
    // 大运/流年干支按五行着色（庚=金、午=火）
    expect(wrapper.find('[data-testid="node-gan-dayun"]').attributes('style')).toContain('--wx-jin')
    expect(wrapper.find('[data-testid="node-zhi-liunian"]').attributes('style')).toContain('--wx-huo')
  })

  it('hides edges by default and shows them only for selected types', async () => {
    const wrapper = mount(RelationDiagram, { props: { result: guanxiResult() } })
    expect(wrapper.findAll('[data-testid^="edge-"]').length).toBe(0)
    // 勾选「五合」：显示 甲己合（天干合）等，隐藏其它
    await wrapper.find('[data-testid="filter-gan-合"]').trigger('click')
    const he = wrapper.findAll('[data-type="合"]')
    expect(he.length).toBeGreaterThan(0)
    expect(wrapper.findAll('[data-type="冲"]').length).toBe(0)
    // 取消勾选「五合」：连线全部隐藏
    await wrapper.find('[data-testid="filter-gan-合"]').trigger('click')
    expect(wrapper.findAll('[data-testid^="edge-"]').length).toBe(0)
  })

  it('supports multi-select of relation types', async () => {
    const wrapper = mount(RelationDiagram, { props: { result: guanxiResult() } })
    await wrapper.find('[data-testid="filter-gan-合"]').trigger('click')
    await wrapper.find('[data-testid="filter-gan-冲"]').trigger('click')
    expect(wrapper.findAll('[data-type="合"]').length).toBeGreaterThan(0)
    expect(wrapper.findAll('[data-type="冲"]').length).toBeGreaterThan(0)
  })

  it('shows 相冲 edge between 甲 and 庚 after selecting 相冲', async () => {
    const wrapper = mount(RelationDiagram, { props: { result: guanxiResult() } })
    await wrapper.find('[data-testid="filter-gan-冲"]').trigger('click')
    const chong = wrapper.findAll('[data-type="冲"]')
    expect(chong.length).toBeGreaterThan(0)
    expect(chong.map((e) => e.text()).join('')).toContain('甲庚')
  })

  it('draws 相克 edge between 庚(金) and 乙(木) after selecting 相克', async () => {
    const wrapper = mount(RelationDiagram, { props: { result: guanxiResult() } })
    await wrapper.find('[data-testid="filter-gan-克"]').trigger('click')
    expect(wrapper.findAll('[data-type="克"]').length).toBeGreaterThan(0)
  })

  it('draws 六冲/六合 edges after selecting 相冲 and 六合', async () => {
    const withZhi = mkResult({
      year: mkPillar('甲', '子', '木', '水', '比肩'),
      month: mkPillar('己', '午', '土', '火', '正财'),
      day: mkPillar('乙', '丑', '木', '土', '日主'),
      time: mkPillar('庚', '寅', '金', '木', '正官'),
    })
    const wrapper = mount(RelationDiagram, { props: { result: withZhi } })
    await wrapper.find('[data-testid="filter-zhi-相冲"]').trigger('click')
    expect(wrapper.findAll('[data-type="相冲"]').length).toBeGreaterThan(0) // 子午冲
    await wrapper.find('[data-testid="filter-zhi-六合"]').trigger('click')
    expect(wrapper.findAll('[data-type="六合"]').length).toBeGreaterThan(0) // 子丑合
  })

  it('lists present relations in the summary below', () => {
    const wrapper = mount(RelationDiagram, { props: { result: guanxiResult() } })
    const summary = wrapper.find('[data-testid="rel-summary"]')
    expect(summary.exists()).toBe(true)
    expect(summary.find('[data-testid="summary-合"]').text()).toContain('甲己合')
    expect(summary.find('[data-testid="summary-合化"]').text()).toContain('甲己合化土')
    expect(summary.find('[data-testid="summary-冲"]').text()).toContain('相冲')
  })

  it('shows 藏干 below each 地支 (display only)', () => {
    const wrapper = mount(RelationDiagram, { props: { result: mkResult({ day: dayWithHidden() }) } })
    const zangDay = wrapper.find('[data-testid="zang-day"]')
    expect(zangDay.exists()).toBe(true)
    expect(zangDay.text()).toContain('辛')
    expect(zangDay.text()).toContain('丁')
  })

  it('spans 三会 across the columns of its three branches (巳午未会火)', async () => {
    // 月柱巳、日柱午、时柱未 → 巳午未三会火（地支在 年/月/日/时 四列，无大运流年）
    const result = mkResult({
      year: mkPillar('甲', '子', '木', '水', '比肩'),
      month: mkPillar('己', '巳', '土', '火', '正财'),
      day: mkPillar('乙', '午', '木', '火', '日主'),
      time: mkPillar('庚', '未', '金', '土', '正官'),
    })
    const wrapper = mount(RelationDiagram, { props: { result } })
    await wrapper.find('[data-testid="filter-zhi-三会"]').trigger('click')
    const edges = wrapper.findAll('[data-type="三会"]')
    expect(edges.length).toBe(1)
    const style = edges[0].attributes('style') ?? ''
    // 四列布局（无大运流年），月/日/时为第 2/3/4 列：横跨 月柱(25%) 到 时柱右端(100%)
    expect(style).toContain('left: 25%')
    expect(style).toContain('width: 75%')
  })

  it('toggle 关联大运/流年 only affects edges, not column display', async () => {
    const dayun = { ganzhi: '甲子', start_year: 2020, end_year: 2029, gan: '甲', zhi: '子' }
    // 大运 甲子 + 年柱 己丑：甲己合（含大运）；四柱之间无干合（己/丙/乙/辛 互不五合）
    const result = mkResult({ year: mkPillar('己', '丑', '土', '土', '正财'), time: mkPillar('丁', '巳', '火', '火', '伤官') })
    const wrapper = mount(RelationDiagram, { props: { result, selectedDayun: dayun as never } })
    await wrapper.find('[data-testid="filter-gan-合"]').trigger('click')
    // 默认关联：含 大运甲×年柱己 的五合连线
    expect(wrapper.findAll('[data-type="合"]').length).toBeGreaterThan(0)
    // 大运列仍显示
    expect(wrapper.find('[data-testid="node-gan-dayun"]').text()).toBe('甲')
    // 取消关联：大运列仍在，但干合连线消失（四柱间无五合）
    await wrapper.find('[data-testid="toggle-dayun"]').setValue(false)
    expect(wrapper.find('[data-testid="node-gan-dayun"]').exists()).toBe(true)
    expect(wrapper.findAll('[data-type="合"]').length).toBe(0)
  })
})

// ---------- 流通 tab ----------

describe('流通 tab', () => {
  it('shows gan/zhi flow arrows with types and text labels', async () => {
    const wrapper = mount(RelationDiagram, { props: { result: mkResult() } })
    await wrapper.find('[data-testid="tab-liutong"]').trigger('click')
    const ganYM = wrapper.find('[data-testid="arrow-gan-year-month"]')
    expect(ganYM.exists()).toBe(true)
    expect(ganYM.attributes('data-type')).toBe('sheng')
    expect(ganYM.text()).toContain('生')
    expect(wrapper.find('[data-testid="arrow-gan-day-time"]').attributes('data-type')).toBe('ke')
    expect(wrapper.find('[data-testid="arrow-zhi-year-month"]').attributes('data-type')).toBe('bi')
  })

  it('omits day→time arrows when the time pillar is missing', async () => {
    const wrapper = mount(RelationDiagram, { props: { result: mkResult({ time: null }) } })
    await wrapper.find('[data-testid="tab-liutong"]').trigger('click')
    expect(wrapper.find('[data-testid="arrow-gan-day-time"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="arrow-zhi-day-time"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="arrow-gan-year-month"]').exists()).toBe(true)
  })
})

// ---------- 宫位 tab ----------

describe('宫位 tab', () => {
  it('shows palace mapping and relative role per pillar', async () => {
    const wrapper = mount(RelationDiagram, { props: { result: mkResult() } })
    await wrapper.find('[data-testid="tab-gongwei"]').trigger('click')
    expect(wrapper.find('[data-testid="palace-year"]').text()).toBe('祖上宫')
    expect(wrapper.find('[data-testid="palace-day"]').text()).toBe('配偶宫')
    expect(wrapper.text()).toContain('祖辈/长辈')
    expect(wrapper.text()).toContain('配偶')
  })
})

// ---------- 六亲 tab ----------

describe('六亲 tab', () => {
  it('shows ten-god→relative mapping and the legend with gender notes', async () => {
    const wrapper = mount(RelationDiagram, { props: { result: mkResult() } })
    await wrapper.find('[data-testid="tab-liuqin"]').trigger('click')
    expect(wrapper.find('[data-testid="god-year"]').text()).toBe('比肩')
    expect(wrapper.find('[data-testid="relative-year"]').text()).toBe('兄弟姐妹')
    expect(wrapper.find('[data-testid="relative-day"]').text()).toBe('本人')
    expect(wrapper.find('[data-testid="legend"]').text()).toContain('男命正官主女儿')
  })
})
