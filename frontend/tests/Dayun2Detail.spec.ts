/**
 * 014 期 T032 / T037 —— **大运引擎2** 页。
 *
 * 裁定依据：spec FR-002（三层数）、FR-003（逐步依据）、FR-006（单独入口、标明是引擎2 的数）、
 * **FR-007（MUST NOT 提供并排视图与差异标记 —— 裁定④）**、FR-008（按需实时算、不落库）。
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { mockResult, mockInputs } from './fixtures'
import type { Dayun2Response } from '../src/types'

const back = vi.fn()
const push = vi.fn()
let routeQuery: Record<string, string> = {}

vi.mock('vue-router', () => ({
  useRouter: () => ({ back, push }),
  useRoute: () => ({ query: routeQuery }),
}))

const fetchDayun2 = vi.fn()
const getRecordDayun2 = vi.fn()
const getRecord = vi.fn()
vi.mock('../src/api/charts', () => ({
  fetchDayun2: (...a: unknown[]) => fetchDayun2(...a),
  fetchSuiyun: vi.fn(),
  predictChart: vi.fn(),
  fetchChartImage: vi.fn(),
  fetchLiuShi: vi.fn(),
}))
vi.mock('../src/api/records', () => ({
  getRecord: (...a: unknown[]) => getRecord(...a),
  getRecordDayun2: (...a: unknown[]) => getRecordDayun2(...a),
  getRecordSuiyun: vi.fn(),
  saveRecord: vi.fn(),
  updateRecord: vi.fn(),
  listRecords: vi.fn(),
  deleteRecord: vi.fn(),
}))

import { useChartStore } from '../src/stores/chart'
import Dayun2Detail from '../src/pages/Dayun2Detail.vue'

const WX = ['木', '火', '土', '金', '水']
const WX_VAL: Record<string, number> = { 木: 1, 火: 0, 土: 7.5, 金: 5.25, 水: 24.4 }

/** 段末五柱快照——与后端 `_snapshot` 同形（四柱 ＋ 大运，各含藏干度数）。 */
function chartStub() {
  const mk = (key: string, label: string, gan: string, zhi: string, hidden: [string, number][]) => ({
    key, label, gan, gan_wx: '水', gan_original: null, gan_change: null,
    gan_degree: 1, gan_own: null, gan_root: null, zhi, zhi_wx: '金',
    zhi_effective_wx: '金', note: null,
    hidden: hidden.map(([g, d]) => ({ gan: g, wx: '金', degree: d, change: null })),
  })
  return { pillars: [
    mk('year', '年', '壬', '申', [['庚', 3]]),
    mk('month', '月', '癸', '丑', [['辛', 2]]),
    mk('day', '日', '壬', '子', [['癸', 5]]),
    mk('time', '时', '丙', '午', [['丁', 4]]),
    mk('_dayun', '运', '辛', '亥', [['壬', 5]]),
  ] }
}

/** 「五行 + 数值」这类 traces 会让 `StepList` 自动出速览格。 */
const wxRows = (v: (wx: string) => number, tpl: (wx: string, n: number) => string) =>
  WX.map((wx) => ({ target: wx, expression: tpl(wx, v(wx)), value: v(wx) }))

function stepStub(ganzhi = '辛亥', over: Partial<Dayun2Response['dayun_steps'][0]> = {}) {
  return {
    ganzhi,
    start_year: 1993,
    start_age_xu: 3,
    elements: {
      木: { static: 1, dynamic: 1, delta: 0 },
      火: { static: 0, dynamic: 0, delta: -1.5 },
      土: { static: 7.5, dynamic: 7.5, delta: -1 },
      金: { static: 5.25, dynamic: 2.25, delta: 0 },
      水: { static: 24.4, dynamic: 25.45, delta: 2 },
    },
    day_master: {
      stem: '壬', wx: '水',
      members: ['年干壬', '月干癸', '日干壬'],
      static: 24.4, dynamic: 25.45, level: '比旺',
    },
    instances: [
      { key: 'g1', kind: 'stem_group' as const, wx: '水',
        label: '年干壬、月干癸、日干壬', static: 24.4, dynamic: 25.45 },
      { key: '大运干辛', kind: 'dayun_stem' as const, wx: '金',
        label: '大运干辛', static: 5.25, dynamic: 5.25 },
    ],
    phases: [
      { key: 'relations', rule: '', result: '本步大运 辛亥 参与的关系判定如上', chart: chartStub(),
        title: '第 1 步 · 十八层判断（大运作为每一柱的邻柱；**与现引擎共用同一份判定**）',
        shared: true, traces: [{ target: '六害', expression: '【成立】申亥害', value: null }] },
      { key: 'month_coef', rule: '', result: '月令系数：木 0.7、火 0.5、土 2、金 1.5、水 1.6',
        chart: chartStub(), title: '第 2 步 · 月令系数',
        traces: wxRows(() => 1.5, (wx) => `${wx} 在丑月为相（系数 1.5）`) },
      { key: 'tonggen5', rule: '', result: '五柱通根：木 0、火 2、土 4.5、金 3.5、水 11',
        chart: chartStub(), title: '第 3 步 · 五柱通根（含大运柱）',
        traces: wxRows((wx) => WX_VAL[wx], (wx, n) => `通根 ＝ ${n} 度`) },
      { key: 'static', rule: '', result: '大运静态旺度：木 1、火 0、土 7.5、金 5.25、水 24.4',
        chart: chartStub(), title: '第 4 步 · 大运静态旺度',
        traces: wxRows((wx) => WX_VAL[wx], (wx, n) =>
          `天干 0 度 ＋ 通根 3.5 度 ＝ 3.5 度，× 月令系数 1.5 ＝ 5.25 度；` +
          `＋ 运支亥（${wx}为休）-1 度 ＋ 运干辛同类相助 +1 ＝ ${n} 度`) },
      { key: 'stem_he', rule: '', result: '丙辛合而不化（合绊）：时干丙 −2 成、大运干辛 −4 成',
        chart: chartStub(), title: '第 5 步 · 天干五合（合化换字 ＋ 合而不化的合绊之力）',
        traces: [{ target: '天干五合', expression: '丙辛合而不化（合绊）', value: null }] },
      { key: 'dayun_pair', rule: '', result: '辛 10.13 度；亥 25.45 度', chart: chartStub(),
        title: '第 6 步 · 运干与运支',
        traces: [{ target: '辛亥', expression: '同柱同性相生', value: null }] },
      { key: 'dayun_to_pillars', rule: '', result: '运干 辛 各次均以 5.25 度出场',
        chart: chartStub(), title: '第 7 步 · 运干对四柱分别生克',
        traces: [{ target: '年干壬、月干癸、日干壬',
                   expression: '运干辛（5.25 度——每次分别计算均取此值，裁定②）', value: 25.45 },
                 { target: '时干丙', expression: '与运干异性克：丙是主方，成数 +0.000', value: 0 }],
        // 逐实例快照：`after` = 该组最后一行依据之后
        charts: [
          { label: '年干壬、月干癸、日干壬', after: 1, chart: chartStub() },
          { label: '时干丙', after: 2, chart: chartStub() },
        ] },
      { key: 'natal_internal', rule: '', result: '大运动态旺度：木 1、火 0、土 7.5、金 5.25、水 25.45',
        chart: chartStub(), title: '第 8 步 · 剩余分数与动态旺度',
        traces: [
          { target: '壬·丙', expression: '四柱内部异性化', value: null },
          ...wxRows((wx) => ({ 木: 1, 火: 0, 土: 7.5, 金: 5.25, 水: 25.45 }[wx] ?? 0),
                    (wx, n) => `${wx}：动态旺度 ${n} 度`),
        ],
        charts: [{ label: '壬·丙', after: 1, chart: chartStub() }] },
    ],
    ...over,
  }
}

function response(steps = [stepStub()]): Dayun2Response {
  return {
    engine: 'dayun-engine2', engine_version: 1,
    input_scope: 'four_pillars', degradations: [], dayun_steps: steps,
  }
}

async function mountPage() {
  const w = mount(Dayun2Detail, { global: { stubs: { 'van-nav-bar': true, 'van-icon': true } } })
  await flushPromises()
  return w
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
  routeQuery = {}
  fetchDayun2.mockResolvedValue(response())
  const store = useChartStore()
  store.result = mockResult
  store.inputs = mockInputs
})

describe('大运引擎2 页', () => {
  it('最前面是这个人的八字 ＋ 大运命盘（四柱 ＋ 当前那一步）', async () => {
    const w = await mountPage()
    const cards = w.findAll('.wx-card')
    expect(cards[0].attributes('data-testid')).toBe('d2-board')   // 在**最前**
    expect(cards[0].text()).toContain('命盘')

    const cols = w.get('[data-testid="d2-board"]').findAll('.pillar-col')
    // 大运居左，其后四柱（与岁运两页同一列序）
    expect(cols.map((c) => c.find('.pillar-label').text()))
      .toEqual(['大运', '年', '月', '日', '时'])
    expect(cols[0].find('.pillar-gan').text()).toBe('壬')
    expect(cols[0].find('.pillar-zhi').text()).toBe('午')
    expect(cols[3].find('.pillar-gan').text()).toBe('乙')         // 日柱
  })

  it('标明这是引擎2 的数（FR-006）', async () => {
    const w = await mountPage()
    // 徽标常驻在「选择大运」卡上——原来那条 stage-line（含「复制本步」）已按用户要求撤掉
    expect(w.get('[data-testid="d2-engine-tag"]').text()).toContain('引擎2')
    expect(w.find('.stage-line').exists()).toBe(false)
    expect(fetchDayun2).toHaveBeenCalled()
  })

  it('选大运用大运横条（与现局页同一份 FortuneStrip），且不画流年那一维', async () => {
    // 大运步自带 `liu_nian`（现引擎的岁运维度）——本页只按大运步取数，不该把它画出来
    const withLiunian = {
      ...mockResult,
      da_yun: { ...mockResult.da_yun, steps: [
        { ganzhi: '壬午', start_year: 1995, end_year: 2004, start_age_xu: 5,
          gan: '壬', zhi: '午', gan_shishen: '正印',
          liu_nian: [{ year: 2026, ganzhi: '丙午', gan: '丙', zhi: '午', gan_shishen: '伤官' }] },
      ] },
    }
    const store = useChartStore()
    store.result = withLiunian as typeof mockResult

    const w = await mountPage()
    expect(w.find('[data-testid="d2-dayun-select"]').exists()).toBe(false)   // 下拉已撤
    const items = w.get('[data-testid="d2-picker"]').findAll('.fs-dayun-item')
    expect(items).toHaveLength(1)
    expect(items[0].text()).toContain('1995')
    expect(items[0].text()).toContain('壬')          // 干支与十神照常
    expect(items[0].classes()).toContain('active')
    expect(w.find('.fs-liunian-item').exists()).toBe(false)                 // 流年横条不画
  })

  it('三层数全部在场（FR-002 / SC-004）', async () => {
    const w = await mountPage()
    // 五行合计：静动两张汇总各一格五行
    for (const id of ['d2-static-sum', 'd2-dynamic-sum']) {
      expect(w.get(`[data-testid="${id}"]`).findAll('.score-cell')).toHaveLength(5)
    }
    expect(w.get('[data-testid="d2-day-master"]').text()).toContain('比旺')
    // 实例：静动两张汇总里各列一遍
    for (const id of ['d2-static-instances', 'd2-dynamic-instances']) {
      expect(w.findAll(`[data-testid="${id}"] tbody tr`).length).toBeGreaterThan(0)
    }
  })

  it('金那一行的静态旺度是 5.25（书 上 3123 的锚点）', async () => {
    const w = await mountPage()
    const cell = w.get('[data-testid="d2-static-sum"] [data-wx="金"]')
    expect(cell.text()).toContain('5.25')
  })

  it('三块汇总排在全页最后（选大运 → 逐步依据 → 静/动/日主）', async () => {
    const w = await mountPage()
    const cards = w.findAll('.wx-card')
    expect(cards.slice(-3).map((c) => c.attributes('data-testid')))
      .toEqual(['d2-static-sum', 'd2-dynamic-sum', 'd2-day-master-sum'])
    // 逐步依据在这三块**之前**（不是夹在中间）
    const stepsAt = cards.findIndex((c) => c.text().includes('逐步依据'))
    expect(stepsAt).toBeGreaterThanOrEqual(0)
    expect(stepsAt).toBeLessThan(cards.length - 3)
    // 静/动两张各自只带**一种**数（静态那张没有动态列，反之亦然）
    expect(w.get('[data-testid="d2-static-instances"] thead').findAll('th').map((t) => t.text()))
      .toEqual(['实例', '五行', '静态'])
    expect(w.get('[data-testid="d2-dynamic-instances"] thead').findAll('th').map((t) => t.text()))
      .toEqual(['实例', '五行', '动态'])
  })

  it('选择卡只有选大运，不摆并排/差异那段长文', async () => {
    const w = await mountPage()
    expect(w.find('[data-testid="d2-picker"]').exists()).toBe(true)
    expect(w.text()).not.toContain('不做并排与差异标记')
  })

  it('第 4 段的算式行把三项都摆出来、并给出数值列（SC-002 的验收点）', async () => {
    const w = await mountPage()
    const lines = w.get('[data-testid="d2-step-static"]').findAll('.step-trace')
    const metal = lines.find((l) => l.text().includes('金'))
    expect(metal).toBeTruthy()
    expect(metal!.text()).toContain('通根')
    expect(metal!.text()).toContain('× 月令系数')
    expect(metal!.text()).toContain('运支')
    expect(metal!.find('.step-trace-val').text()).toBe('5.25')
  })

  it('七段依据都在、且算式行直接可见（FR-003 / SC-002）', async () => {
    // 与现局页同一套渲染（`StepList`）：**不折叠**，七段全部平铺——
    // 展开/收起会让「过程是否可见」取决于用户有没有点，故共享组件本来就不做折叠。
    const w = await mountPage()
    // ⚠️ 不能按 `[data-testid^="d2-step-"]` 选——快照（`d2-step-chart-*`）与速览
    // （`d2-step-scores`）的 testid 也以它开头，会选出 18 个。段块是 `li.step-block`。
    const phases = w.findAll('li.step-block')
    expect(phases).toHaveLength(8)
    expect(phases.map((p) => p.attributes('data-testid'))).toEqual([
      'd2-step-relations', 'd2-step-month_coef', 'd2-step-tonggen5', 'd2-step-static',
      'd2-step-stem_he',                       // R30 新增：天干五合（八段；换过字时另有 static_he）
      'd2-step-dayun_pair', 'd2-step-dayun_to_pillars', 'd2-step-natal_internal'])
    for (const p of phases) {
      expect(p.findAll('.step-trace').length).toBeGreaterThan(0)   // 每段都有算式行
      expect(p.find('.step-result').exists()).toBe(true)           // 每段都有结果行
    }
  })

  it('每段都带段末五柱快照、三段以上带五行速览（对齐现局页的信息密度）', async () => {
    const w = await mountPage()
    const phases = w.findAll('li.step-block')
    for (const p of phases) {
      const charts = p.findAll('.step-chart')
      expect(charts.length).toBeGreaterThanOrEqual(1)              // 第 6/7 段会多张
      // **每一张**都是五柱：四柱＋大运（多张时总列数是 5 的倍数，不能直接比）
      for (const c of charts) expect(c.findAll('.pillar-col').length).toBe(5)
    }
    // 第 2/3/4/7 段的 traces 是「五行 + 数值」，故自动出速览格
    const withScores = phases.filter((p) => p.find('.step-scores').exists())
    expect(withScores.length).toBeGreaterThanOrEqual(4)
  })

  it('第 6、7 段把逐实例快照插在对应算式之后（与原局页的生克段同机制）', async () => {
    const w = await mountPage()
    for (const key of ['dayun_to_pillars', 'natal_internal']) {
      const block = w.get(`[data-testid="d2-step-${key}"]`)
      const kids = Array.from(block.element.children)
      const kinds = kids.map((k) => k.className)
      // 算式行 → 快照 → 算式行 → 快照 …：快照必须**夹在**算式之间，不是全堆在段尾
      expect(kinds.filter((c) => String(c).includes('step-chart')).length)
        .toBeGreaterThanOrEqual(1)
      const firstChart = kinds.findIndex((c) => String(c).includes('step-chart'))
      expect(kinds.slice(0, firstChart).some((c) => String(c).includes('step-trace')))
        .toBe(true)
    }
  })

  it('第 1 段注明与现引擎共用同一份判定（澄清①）', async () => {
    const w = await mountPage()
    const first = w.get('[data-testid="d2-step-relations"]')
    expect(first.text()).toContain('共用')
  })

  it('**不提供**并排视图或差异标记（FR-007 / 裁定④）', async () => {
    // 查的是**结构与元素**（字面查「并排/差异」不算数——说明文字是可以删的，
    // 下面那条测试就专门钉住「那段长文已撤」）：没有第二个引擎的列、没有差异类节点。
    const w = await mountPage()
    expect(w.find('[class*="diff"]').exists()).toBe(false)
    expect(w.find('[class*="compare"]').exists()).toBe(false)
    expect(w.find('[data-testid*="diff"]').exists()).toBe(false)
    expect(w.find('[data-testid*="compare"]').exists()).toBe(false)
    // 每一张表都只有引擎2 一家的数（静/动分表，故没有「两套数并排」的表）
    for (const id of ['d2-static-instances', 'd2-dynamic-instances']) {
      expect(w.get(`[data-testid="${id}"]`).findAll('th').length).toBe(3)
    }
  })

  it('切换大运步：取一次全部、本地切换，且**页面上的数确实换成那一步**', async () => {
    // 这条是回归测试：改前是「切一步取一步」，后端被 `dayun_ganzhi` 过滤后只回 1 条，
    // 而 `current` 按 `selectedIndex` 取 → 切到第 2 步就是 `steps[1]` → undefined
    // → 整块结果空白。旧测试只断言了「请求带上了新干支」，**没断言页面内容变了**，
    // 所以没抓到。两个断言都要在。
    const twoSteps = {
      ...mockResult,
      da_yun: { ...mockResult.da_yun, steps: [
        { ganzhi: '辛亥', start_year: 1995, end_year: 2004 },
        { ganzhi: '壬子', start_year: 2005, end_year: 2014 },
      ] },
    }
    const store = useChartStore()
    store.result = twoSteps as typeof mockResult

    const second = stepStub('壬子', {
      elements: {
        木: { static: 2, dynamic: 2, delta: 0 },
        火: { static: 3, dynamic: 3, delta: 1 },
        土: { static: 4, dynamic: 4, delta: 0 },
        金: { static: 9.75, dynamic: 9.75, delta: 0 },
        水: { static: 5, dynamic: 5, delta: 0 },
      },
    })
    // ⚠️ mock 必须**照真实后端的行为过滤**：传了 `dayun_ganzhi` 就只回那一条。
    // 若让 mock 无论如何都回全部，这条测试就抓不到「切一步取一步 → 只回 1 条 →
    // `steps[selectedIndex]` 越界」那个 bug 了。
    fetchDayun2.mockImplementation((input: { dayun_ganzhi?: string }) => {
      const all = [stepStub('辛亥'), second]
      return Promise.resolve(response(input?.dayun_ganzhi
        ? all.filter((s) => s.ganzhi === input.dayun_ganzhi)
        : all))
    })

    const w = await mountPage()
    expect(fetchDayun2).toHaveBeenCalledTimes(1)           // 一次取回全部
    expect(fetchDayun2.mock.calls[0][0].dayun_ganzhi).toBeUndefined()
    const active = () => w.get('[data-testid="d2-picker"] .fs-dayun-item.active').text()
    expect(active()).toContain('辛亥')
    expect(w.get('[data-testid="d2-static-sum"] [data-wx="金"]').text()).toContain('5.25')

    await w.findAll('[data-testid="d2-picker"] .fs-dayun-item')[1].trigger('click')
    await flushPromises()

    expect(fetchDayun2).toHaveBeenCalledTimes(1)           // 切换**不再发请求**
    expect(active()).toContain('壬子')
    // 页首命盘的大运列跟着换字（四柱那四列不动）
    const cols = w.get('[data-testid="d2-board"]').findAll('.pillar-col')
    expect(cols[0].find('.pillar-gan').text()).toBe('壬')
    expect(cols[0].find('.pillar-zhi').text()).toBe('子')
    // ★ 关键：三层数与逐步依据都换成了第 2 步的
    expect(w.get('[data-testid="d2-static-sum"] [data-wx="金"]').text()).toContain('9.75')
    expect(w.findAll('li.step-block')).toHaveLength(8)
  })

  it('降级说明照常渲染（FR-009）', async () => {
    fetchDayun2.mockResolvedValue({ ...response(), degradations: ['缺时柱：可靠度下降'] })
    const w = await mountPage()
    expect(w.text()).toContain('缺时柱')
  })

  it('来源命盘不可得时出空态，不发请求', async () => {
    const store = useChartStore()
    store.result = null
    const w = await mountPage()
    expect(w.find('[data-testid="d2-empty"]').exists()).toBe(true)
    expect(fetchDayun2).not.toHaveBeenCalled()
  })

  it('带 ?record= 时走记录端点（FR-006 的第二条入口）', async () => {
    routeQuery = { record: '7' }
    getRecord.mockResolvedValue({ id: 7, chart_result: mockResult })
    getRecordDayun2.mockResolvedValue(response())
    await mountPage()
    // 不传 `dayun_ganzhi`——一次取回全部步（端点仍支持按步过滤，页面用不上）
    expect(getRecordDayun2).toHaveBeenCalledWith(7)
    expect(fetchDayun2).not.toHaveBeenCalled()
  })
})
