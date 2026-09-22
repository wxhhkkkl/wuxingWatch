/**
 * 013 补遗 —— 岁运两页的命盘（FR-027）。
 *
 * 两页的顶部命盘卡与逐段快照要比原局页**多出四个字**：大运、流年两列，**放最左**。
 * 阶段 2 没有流年参与 → 该列出灰显占位（**不是**「取本年流年」，它在阶段 2 的判定里
 * 根本不存在）；被大运挡住的流年同理（后端不建那一列）。
 *
 * **原局页不看这个文件**：`tests/WangduV2.spec.ts` 全绿就是「原局页 DOM/testid 未变」的门，
 * 本文件只在末尾补一条「四柱输入不产生第五列」的组件级断言。
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { mockResult, mockInputs } from './fixtures'
import type { SuiyunResponse, V2ChartPillar, V2DayunStep, V2Step } from '../src/types'

const back = vi.fn()
const push = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({ back, push }),
  useRoute: () => ({ query: {} }),
}))

const fetchSuiyun = vi.fn()
vi.mock('../src/api/charts', () => ({
  fetchSuiyun: (...a: unknown[]) => fetchSuiyun(...a),
  predictChart: vi.fn(),
  fetchChartImage: vi.fn(),
  fetchLiuShi: vi.fn(),
}))
vi.mock('../src/api/records', () => ({
  getRecord: vi.fn(),
  getRecordSuiyun: vi.fn(),
  saveRecord: vi.fn(),
  updateRecord: vi.fn(),
  listRecords: vi.fn(),
  deleteRecord: vi.fn(),
}))

import { useChartStore } from '../src/stores/chart'
import DayunDetail from '../src/pages/DayunDetail.vue'
import LiunianDetail from '../src/pages/LiunianDetail.vue'
import StepList from '../src/components/StepList.vue'

// ---------------------------------------------------------------
// 造数：一张 6 列的命盘快照（四柱 + 大运 + 流年）
// ---------------------------------------------------------------

function pillar(over: Partial<V2ChartPillar> & { key: string; label: string }): V2ChartPillar {
  return {
    gan: '', gan_wx: '木', gan_original: null, gan_change: null, gan_degree: 1,
    gan_own: null, gan_root: null, zhi: '', zhi_wx: '金', zhi_effective_wx: '金',
    hidden: [], note: null, ...over,
  }
}

/** 四柱（原局页那四列的样子：第 5 段起带「自身/根」两个分量）。 */
const NATAL: V2ChartPillar[] = [
  pillar({ key: 'year', label: '年', gan: '己', gan_wx: '土', gan_degree: 2,
           gan_own: 0.8, gan_root: 1.2, zhi: '丑', zhi_wx: '土', zhi_effective_wx: '土',
           hidden: [{ gan: '己', wx: '土', degree: 3, change: null }] }),
  pillar({ key: 'month', label: '月', gan: '辛', gan_wx: '金', gan_degree: 1.5,
           gan_own: 0.6, gan_root: 0.9, zhi: '未', zhi_wx: '土', zhi_effective_wx: '土',
           hidden: [{ gan: '己', wx: '土', degree: 3, change: null }] }),
  pillar({ key: 'day', label: '日', gan: '丙', gan_wx: '火', gan_degree: 1.2,
           gan_own: 0.5, gan_root: 0.7, zhi: '子', zhi_wx: '水', zhi_effective_wx: '水',
           hidden: [{ gan: '癸', wx: '水', degree: 6, change: null }] }),
  pillar({ key: 'time', label: '时', gan: '丙', gan_wx: '火', gan_degree: 1,
           gan_own: 0.4, gan_root: 0.6, zhi: '申', zhi_wx: '金', zhi_effective_wx: '金',
           hidden: [{ gan: '庚', wx: '金', degree: 6, change: null }] }),
]

/** 大运列：干 1 度、不给自身/根；藏干取「临大运」独立档且平加（书 上 884）。 */
const DAYUN_COL = pillar({
  key: '_dayun', label: '大运', gan: '己', gan_wx: '土', gan_degree: 1,
  zhi: '巳', zhi_wx: '火', zhi_effective_wx: '火',
  hidden: [{ gan: '丙', wx: '火', degree: 3, change: null }],
})

/** 流年列（只有**真正参与**阶段 3 时才由后端给出）。 */
const LIUNIAN_COL = pillar({
  key: '_liunian', label: '流年', gan: '乙', gan_wx: '木', gan_degree: 1,
  zhi: '亥', zhi_wx: '水', zhi_effective_wx: '水',
  hidden: [{ gan: '壬', wx: '水', degree: 3, change: null }],
})

function chartOf(extra: V2ChartPillar[]): { pillars: V2ChartPillar[] } {
  return { pillars: [...NATAL, ...extra] }
}

/** 判定依据的一个普通段（带段末命盘快照）。 */
function chartStep(key: string, extra: V2ChartPillar[]): V2Step {
  return {
    key, title: `第 1 段 · ${key}`, rule: '规则', rulings: [],
    chart: chartOf(extra),
    traces: [{ target: '', expression: '算式', value: null }],
    result: '结论',
  }
}

/** 五行速览段：只有**段末**那张快照（无逐实例），速览格须紧邻它。 */
function staticStep(extra: V2ChartPillar[]): V2Step {
  const ch: V2Step = chartStep('static', extra)
  ch.traces = [
    { target: '木', expression: '不透天干', value: 0 },
    { target: '火', expression: '天干 2 度', value: 5.6 },
    { target: '土', expression: '天干 2 度', value: 12 },
    { target: '金', expression: '天干 1 度', value: 14 },
    { target: '水', expression: '地支藏干', value: 6 },
  ]
  return ch
}

/** 第 7 段：逐实例快照 + 五行速览（速览格须与快照**直接相邻**）。 */
function settleStep(extra: V2ChartPillar[]): V2Step {
  return {
    key: 'stem_shengke', title: '第 7 段 · 生克结算（按实例）', rule: '规则', rulings: [],
    chart: chartOf(extra),
    charts: [
      { label: '结算 年', after: 1, chart: chartOf(extra) },
      { label: '结算 日', after: 2, chart: chartOf(extra) },
    ],
    traces: [
      { target: '丙', expression: '受克', value: 1 },
      { target: '木', expression: '合计', value: 0 },
      { target: '火', expression: '合计', value: 5.6 },
      { target: '土', expression: '合计', value: 12 },
    ],
    result: '实例层结算完成',
  }
}

function step(over: Partial<V2DayunStep>): V2DayunStep {
  return {
    source: 'dayun', ganzhi: '己巳', start_year: 1995, start_age_xu: 5,
    level: '偏弱',
    ge_ju: { type: 'zheng', hua_shen: null, cong_targets: [], neng_duli: true,
             liang_qi: null, basis: [] },
    yong_shen: {
      empty: false, theoretical: { element: '水', basis: '' }, practical: null,
      tiaohou: null, xi_shen: ['金'], ji_shen: ['土'], xian_shen: [],
      tier: { first: null, second: null, third: null }, direction: null, basis: '',
    },
    relations: { established: [], rejected: [] },
    transition: null, deltas: [], scores_after: {},
    ...over,
  } as V2DayunStep
}

const STAGE2: SuiyunResponse = {
  engine: 'wangdu-v2', contract_version: 2, stage: 2, degradations: [],
  dayun: step({
    // 阶段 2：后端**只建大运列**（流年不存在）
    steps: [chartStep('relations', [DAYUN_COL]), staticStep([DAYUN_COL]),
            settleStep([DAYUN_COL])],
  }),
  liunian: null, pairs: null,
}

const STAGE3: SuiyunResponse = {
  ...STAGE2, stage: 3,
  liunian: step({
    source: 'liunian', liunian: '乙亥',
    steps: [chartStep('relations', [DAYUN_COL, LIUNIAN_COL]),
            staticStep([DAYUN_COL, LIUNIAN_COL])],
  }),
  pairs: null,
}

/** 阶段 3 但**该年流年被大运挡住**：后端不建流年列，`liunian` 字段仍带着干支。 */
const STAGE3_GATED: SuiyunResponse = {
  ...STAGE2, stage: 3,
  degradations: ['该年流年被大运以「午未六合」挡住，作用不到原局（书 下 4430「运制约岁」/ 下 4468）'],
  liunian: step({
    source: 'liunian', liunian: '乙亥',
    steps: [chartStep('relations', [DAYUN_COL]), staticStep([DAYUN_COL])],
  }),
  pairs: null,
}

// ---------------------------------------------------------------
// 挂载
// ---------------------------------------------------------------

function mountPage(cmp: unknown, res: SuiyunResponse, chart?: Record<string, unknown>) {
  setActivePinia(createPinia())
  const store = useChartStore()
  const result = structuredClone(mockResult) as unknown as Record<string, unknown>
  // 该步的逐年流年（顶部卡的流年列要用它取干支/十神/藏干）
  Object.assign(result, chart ?? {})
  store.set(result as never, { ...mockInputs })
  fetchSuiyun.mockResolvedValue(structuredClone(res))
  return mount(cmp as never)
}

const withDayunMeta = {
  da_yun: {
    start_age: 5, start_month: 7,
    steps: [{
      ganzhi: '己巳', start_year: 1995, end_year: 2004, gan: '己', zhi: '巳',
      gan_shishen: '伤官', zhi_shishen: '比肩',
      detail: { gan_shishen: '伤官', zhi_shishen: '比肩', cang_gan: [
        { gan: '丙', shishen: '比肩' }, { gan: '庚', shishen: '偏财' },
        { gan: '戊', shishen: '食神' }] },
      liu_nian: [
        { year: 1995, gan: '乙', zhi: '亥', ganzhi: '乙亥', gan_shishen: '正印',
          zhi_shishen: '七杀',
          detail: { gan_shishen: '正印', zhi_shishen: '七杀', cang_gan: [
            { gan: '壬', shishen: '七杀' }, { gan: '甲', shishen: '偏印' }] } },
      ],
    }],
  },
}

/** 能 `findAll` 的东西——页面 wrapper 与某个元素 wrapper 都满足（只需这一条）。 */
type FindAll = { findAll(sel: string): { attributes(k: string): string | undefined }[] }

/** 取某容器内所有列 testid（按 DOM 顺序）。 */
function colIds(w: FindAll, prefix: string): string[] {
  return w.findAll(`[data-testid^="${prefix}-chart-"]`)
    .map((el) => el.attributes('data-testid') as string)
    .filter((id) => !id.includes('-chart-hidden-') && !id.includes('-chart-note-'))
}

beforeEach(() => {
  fetchSuiyun.mockReset()
  back.mockReset()
  push.mockReset()
})

// ---------------------------------------------------------------
// 逐段命盘快照
// ---------------------------------------------------------------

describe('「加入大运」页 —— 逐段命盘快照', () => {
  it('每张快照 6 列、大运/流年**居左**', async () => {
    const w = mountPage(DayunDetail, STAGE2, withDayunMeta)
    await flushPromises()
    const chart = w.get('[data-testid="sy-dayun-step-chart-relations"]')
    expect(colIds(chart, 'sy-dayun')).toEqual([
      'sy-dayun-chart-_dayun', 'sy-dayun-chart-_liunian',
      'sy-dayun-chart-year', 'sy-dayun-chart-month',
      'sy-dayun-chart-day', 'sy-dayun-chart-time',
    ])
  })

  it('阶段 2 的流年列是**灰显占位**：有位置、没有度数', async () => {
    const w = mountPage(DayunDetail, STAGE2, withDayunMeta)
    await flushPromises()
    const ln = w.get('[data-testid="sy-dayun-chart-_liunian"]')
    expect(ln.text()).toContain('—')
    expect(ln.classes()).toContain('is-dim')
    expect(ln.find('[data-testid="sy-dayun-chart-hidden-_liunian"]').exists()).toBe(false)
    // 大运列是**真列**，不灰显
    expect(w.get('[data-testid="sy-dayun-chart-_dayun"]').classes()).not.toContain('is-dim')
  })

  it('岁运两列的度数照后端给的显示（天干 1 度、藏干平加）', async () => {
    const w = mountPage(DayunDetail, STAGE2, withDayunMeta)
    await flushPromises()
    const dy = w.get('[data-testid="sy-dayun-chart-_dayun"]')
    expect(dy.find('.pillar-deg').text()).toBe('1')
    const rows = dy.findAll('[data-testid="sy-dayun-chart-hidden-_dayun"]')
    expect(rows).toHaveLength(1)
    expect(rows[0].find('.cang-deg').text()).toBe('3')
    // 岁运之干不给「自身/根」——那两个小字在宣示一个对它不成立的等式
    expect(dy.find('[data-testid="sy-dayun-gan-own-_dayun"]').exists()).toBe(false)
  })

  it('第 7 段逐实例快照按后端给的 `after` 插在算式行之后', async () => {
    const w = mountPage(DayunDetail, STAGE2, withDayunMeta)
    await flushPromises()
    const li = w.get('[data-testid="sy-dayun-step-stem_shengke"]')
    expect(li.find('[data-testid="sy-dayun-step-chart-stem_shengke-1"]').exists()).toBe(true)
    expect(li.find('[data-testid="sy-dayun-step-chart-stem_shengke-2"]').exists()).toBe(true)
    // 逐实例出图时，段末那张不再重复贴
    expect(li.find('[data-testid="sy-dayun-step-chart-stem_shengke"]').exists()).toBe(false)
    const kids = Array.from(li.element.children) as HTMLElement[]
    const c1 = kids.findIndex((k) =>
      k.getAttribute('data-testid') === 'sy-dayun-step-chart-stem_shengke-1')
    const res = kids.findIndex((k) => k.classList.contains('step-result'))
    expect(c1).toBeGreaterThan(0)
    expect(c1).toBeLessThan(res)
  })

  it('五行速览格与命盘**直接相邻**（与原局页同一套次序规则）', async () => {
    const w = mountPage(DayunDetail, STAGE2, withDayunMeta)
    await flushPromises()
    const li = w.get('[data-testid="sy-dayun-step-static"]')
    const scores = li.get('[data-testid="sy-dayun-step-scores"]')
    const chart = li.get('[data-testid="sy-dayun-step-chart-static"]')
    const kids = Array.from(li.element.children) as HTMLElement[]
    const si = kids.indexOf(scores.element as HTMLElement)
    const ci = kids.indexOf(chart.element as HTMLElement)
    expect(ci).toBe(si + 1)            // 直接相邻，中间不夹别的节点
    // 结果行在速览格之前
    const ri = kids.findIndex((k) => k.classList.contains('step-result'))
    expect(ri).toBeLessThan(si)
  })
})

describe('「加入流年」页 —— 逐段命盘快照', () => {
  it('阶段 3 的流年列是**真列**（有干支与藏干），大运列同样在场', async () => {
    const w = mountPage(LiunianDetail, STAGE3, withDayunMeta)
    await flushPromises()
    const chart = w.get('[data-testid="sy-liunian-step-chart-relations"]')
    expect(colIds(chart, 'sy-liunian')[0]).toBe('sy-liunian-chart-_dayun')
    expect(colIds(chart, 'sy-liunian')[1]).toBe('sy-liunian-chart-_liunian')
    const ln = w.get('[data-testid="sy-liunian-chart-_liunian"]')
    expect(ln.classes()).not.toContain('is-dim')
    expect(ln.text()).toContain('乙')
    expect(ln.findAll('[data-testid="sy-liunian-chart-hidden-_liunian"]')).toHaveLength(1)
  })

  it('被大运挡住的流年走**同一条占位路径**——判据是「有没有这一列」，不是 `step.liunian`', async () => {
    // `analyze_step` 的门控**不清** `liunian` 字段（它仍是传入的干支），故若拿它当判据，
    // 会把一个被挡住、根本没参与判定的流年画成一个正常列。
    const w = mountPage(LiunianDetail, STAGE3_GATED, withDayunMeta)
    await flushPromises()
    const ln = w.get('[data-testid="sy-liunian-chart-_liunian"]')
    expect(ln.classes()).toContain('is-dim')
    expect(ln.text()).toContain('—')
    // 门控的原因由页面上已有的 ⚠️ 行给出，不另造文案
    expect(w.text()).toContain('挡住')
  })
})

// ---------------------------------------------------------------
// 顶部命盘卡
// ---------------------------------------------------------------

describe('两页的顶部命盘卡', () => {
  it('6 列且大运/流年居左；岁运列带十神与藏干', async () => {
    const w = mountPage(LiunianDetail, STAGE3, withDayunMeta)
    await flushPromises()
    const board = w.get('.wx-card .pillar-row')
    const ids = board.findAll('.pillar-col')
      .map((c) => c.attributes('data-testid') ?? '')
    expect(ids).toEqual(['', '', '', '', '', ''])
    expect(board.findAll('.pillar-label').map((l) => l.text()))
      .toEqual(['大运', '流年', '年', '月', '日', '时'])
    const dy = w.get('[data-testid="sy-board-canggan-_dayun"]')
    expect(dy.findAll('.pillar-cang-row')).toHaveLength(3)
    // 藏干块里的十神是**藏干**的十神（干 · 十神），不是该柱天干的十神
    expect(dy.text()).toContain('比肩')
    const ln = w.get('[data-testid="sy-board-canggan-_liunian"]')
    expect(ln.findAll('.pillar-cang-row')).toHaveLength(2)
  })

  it('「加入大运」页的流年柱是灰显占位（无藏干块）', async () => {
    const w = mountPage(DayunDetail, STAGE2, withDayunMeta)
    await flushPromises()
    const cols = w.get('.wx-card .pillar-row').findAll('.pillar-col')
    expect(cols.map((c) => c.text().startsWith('流年—'))).toContain(true)
    expect(w.find('[data-testid="sy-board-canggan-_liunian"]').exists()).toBe(false)
    // 大运柱仍是真的
    expect(w.find('[data-testid="sy-board-canggan-_dayun"]').exists()).toBe(true)
  })
})

// ---------------------------------------------------------------
// 原局页：四柱输入不得长出第五列
// ---------------------------------------------------------------

describe('原局页（四柱）', () => {
  it('只给四柱、不声明占位时不产生岁运列', () => {
    const w = mount(StepList, { props: { steps: [chartStep('relations', [])] } })
    expect(colIds(w, 'v2')).toEqual([
      'v2-chart-year', 'v2-chart-month', 'v2-chart-day', 'v2-chart-time',
    ])
    expect(w.find('[data-testid="v2-chart-_dayun"]').exists()).toBe(false)
  })
})
