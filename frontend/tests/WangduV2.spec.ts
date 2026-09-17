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

/** 012 v2 结论（engine === 'wangdu-v2'）的最小可用样本。 */
const v2Strength = {
  engine: 'wangdu-v2',
  contract_version: 2,
  day_master: '戊',
  day_master_wuxing: '土',
  input_scope: 'four_pillars',
  degradations: [],
  relations: { established: [], rejected: [] },
  degrees: {
    木: { base: 0, after_relations: 0, root: 0, static: 0, final: 0, coef: 1, state: '死' },
    火: { base: 6, after_relations: 6, root: 6, static: 5.6, final: 5.6, coef: 0.8, state: '休' },
    土: { base: 10, after_relations: 10, root: 8, static: 12, final: 7.8, coef: 2, state: '旺' },
    金: { base: 8, after_relations: 8, root: 7, static: 14, final: 17.6, coef: 2, state: '旺' },
    水: { base: 4, after_relations: 4, root: 3, static: 6, final: 6, coef: 1.5, state: '相' },
  },
  level: '偏弱',
  ge_ju: { type: 'zheng', hua_shen: null, cong_targets: [], neng_duli: true, liang_qi: null,
           basis: ['不满足任何特殊格局 → 正格'] },
  yong_shen: {
    empty: false,
    theoretical: { element: '火', basis: '日主 7.8 度（偏弱）取生助。按戊之性取 火', direction: '扶抑' },
    practical: { element: '土', basis: '食伤与官杀相战', reason: '用神相战，改取通关' },
    tiaohou: { element: null, basis: '申月湿度适中，不需调候', met: true,
               quantified: '无需调候', position: null },
    xi_shen: ['土'], ji_shen: ['木'], xian_shen: ['金'],
    tier: { first: '火', second: '土', third: null },
    direction: '扶抑',
    basis: '三因素取用依据',
  },
  layers: {
    verdict: '',
    met: ['戊土得壬水围水灌溉'],
    missing: ['戊土得甲木疏松土质'],
    penalties: [{ reason: '土多晦火，掩其光华', delta: '-2级' }],
    basis: '戊（土）生于申月：特性条件满足 1/2 条',
  },
  steps: [
    { key: 'relations', title: '第 1 段 · 关系判定（十八级顺序）',
      rule: '按新书十二节顺序逐级判定', rulings: ['O-5（严格让位）'],
      traces: [{ target: '', expression: '六冲成立：子午冲', value: null }],
      result: '成立 1 条、让位 0 条' },
    { key: 'tonggen', title: '第 4 段 · 通根递减',
      rule: '天干在地支中找到同类藏干即为「通根」，按柱距递减', rulings: [],
      traces: [
        { target: '甲', expression: '根在 子，距 3 柱（远隔）：5 度 − 2 = 3 度', value: 3 },
        { target: '木', expression: '实际通根合计 3 度', value: 3 },
      ],
      result: '五行的实际通根 = 木 3；火 0；土 2；金 5；水 3' },
    // 静态与动态两段给出**全部五个五行**的度数——展示层据此渲染得分行
    // （真实引擎同样输出五项；`stepScores` 需 ≥2 项才当得分行渲染）。
    { key: 'static', title: '第 5 段 · 静态旺度',
      rule: '静态旺度 =（天干度数 + 实际通根度数）× 月令系数', rulings: ['C26-7（2.4 归比弱侧）'],
      traces: [
        { target: '木', value: 0,
          expression: '不透天干 ＋ 地支藏干 0 度 ＝ 0 度，× 月令系数 0.5（申月木为死）＝ 0 度' },
        { target: '火', value: 5.6,
          expression: '天干 1 度（月干丙） ＋ 实际通根 6 度（月干丙 6，见第 4 段） ＝ 7 度，× 月令系数 0.8（申月火为休）＝ 5.6 度' },
        { target: '土', value: 12,
          expression: '天干 2 度（年干戊；日干戊） ＋ 实际通根 4 度（2＋2，见第 4 段） ＝ 6 度，× 月令系数 2（申月土为旺）＝ 12 度' },
        { target: '金', value: 14,
          expression: '天干 1 度（时干庚） ＋ 实际通根 6 度（时干庚 6，见第 4 段） ＝ 7 度，× 月令系数 2（申月金为旺）＝ 14 度' },
        { target: '水', value: 6,
          expression: '不透天干 ＋ 地支藏干 12 度 ＝ 12 度，× 月令系数 0.5（申月水为死）＝ 6 度' },
      ],
      result: '木 0；火 5.6；土 12；金 14；水 6' },
    { key: 'total', title: '第 9 段 · 动态旺度与定级',
      rule: '按十一档定级', rulings: [],
      traces: [
        { target: '木', expression: '木：动态旺度 0 度', value: 0 },
        { target: '火', expression: '火：动态旺度 5.6 度', value: 5.6 },
        { target: '土', expression: '土：动态旺度 7.8 度', value: 7.8 },
        { target: '金', expression: '金：动态旺度 17.6 度', value: 17.6 },
        { target: '水', expression: '水：动态旺度 6 度', value: 6 },
      ],
      result: '日主 戊（土）7.8 度 → 偏弱' },
  ],
  dayun: [
    { ganzhi: '甲寅', start_year: 2000, start_age_xu: 10, level: '偏弱',
      ge_ju: { type: 'zheng' }, yong_shen: { theoretical: { element: '火' } },
      transition: '破格', deltas: [], scores_after: {} },
  ],
}

const withV2 = {
  ...mockResult,
  xi_yong: { ...mockResult.xi_yong, strength: v2Strength },
} as never

const withLegacy = {
  ...mockResult,
  xi_yong: { ...mockResult.xi_yong, strength: { score: 288, level: '中和' } },
} as never

function mountWith(result: unknown) {
  setActivePinia(createPinia())
  const store = useChartStore()
  store.result = result as never
  return mount(StrengthDetail)
}

describe('StrengthDetail — v2 渲染路径（012）', () => {
  beforeEach(() => { back.mockClear(); push.mockClear() })

  it('engine=wangdu-v2 时走 v2 分支：显示档位/格局', () => {
    const w = mountWith(withV2)
    expect(w.find('[data-testid="v2-level"]').text()).toContain('偏弱')
    expect(w.find('[data-testid="v2-level"]').text()).toContain('正格')
  })

  it('显示理论用神与实际用神（含反转原因）', () => {
    const w = mountWith(withV2)
    expect(w.find('[data-testid="v2-yong"]').text()).toBe('火')
    expect(w.find('[data-testid="v2-practical"]').text()).toContain('土')
    expect(w.find('[data-testid="v2-practical"]').text()).toContain('通关')
  })

  it('显示调候量化结论', () => {
    const w = mountWith(withV2)
    expect(w.find('[data-testid="v2-tiaohou"]').text()).toContain('无需调候')
  })

  it('显示格局层次的条件清单与扣减项', () => {
    const w = mountWith(withV2)
    const text = w.text()
    expect(w.find('[data-testid="v2-layers-basis"]').text()).toContain('戊（土）')
    expect(text).toContain('戊土得壬水围水灌溉')
    expect(text).toContain('土多晦火')
    expect(text).toContain('-2级')
  })

  it('显示逐步大运的用神变化与成格/破格', () => {
    const w = mountWith(withV2)
    const row = w.find('[data-testid="v2-dayun-row"]')
    expect(row.exists()).toBe(true)
    expect(row.text()).toContain('甲寅')
    expect(row.text()).toContain('破格')
  })

  it('判定依据含规则与算式（口径裁定不在页面展示）', () => {
    const w = mountWith(withV2)
    expect(w.findAll('.step-rule').length).toBeGreaterThan(0)
    expect(w.findAll('.step-trace').length).toBeGreaterThan(0)
    // 口径裁定只留在数据里（`s.rulings`），页面不渲染
    expect(w.findAll('[data-testid="v2-step-rulings"]').length).toBe(0)
    expect(w.text()).not.toContain('O-5')
  })

  it('命盘卡片显示各柱藏干（干 · 十神）', () => {
    const withCang = JSON.parse(JSON.stringify(mockResult))
    withCang.xi_yong.strength = v2Strength
    withCang.pillars.month.detail = {
      gan_shishen: '七杀',
      zhi_shishen: '伤官',
      cang_gan: [
        { gan: '丙', shishen: '伤官' },
        { gan: '庚', shishen: '正官' },
        { gan: '戊', shishen: '正财' },
      ],
      xing_yun: '', zi_zuo: '', xun_kong: '', na_yin: '', shen_sha: [],
    }
    const w = mountWith(withCang)
    const month = w.find('[data-testid="v2-canggan-month"]')
    expect(month.exists()).toBe(true)
    expect(month.findAll('.pillar-cang-row').length).toBe(3)
    expect(month.text()).toContain('丙')
    expect(month.text()).toContain('伤官')
    // 只加在月柱：其余三柱无 detail，不渲染藏干块
    expect(w.find('[data-testid="v2-canggan-year"]').exists()).toBe(false)
  })

  it('旧记录无 detail 时不渲染藏干块，也不报错', () => {
    const w = mountWith(withV2)
    expect(w.findAll('.pillar-cang').length).toBe(0)
  })

  it('缺时柱时显示降级提示', () => {
    const degraded = JSON.parse(JSON.stringify(mockResult))
    degraded.xi_yong.strength = {
      ...v2Strength,
      input_scope: 'three_pillars',
      degradations: ['缺时柱：取用候选位仅余月干、日支'],
    }
    const w = mountWith(degraded)
    expect(w.find('[data-testid="v2-degradations"]').text()).toContain('缺时柱')
  })
})

describe('StrengthDetail — 旧路径兼容（FR-052/054）', () => {
  it('旧契约（sizhu-jingsui）仍走既有分支，不报错', () => {
    const w = mountWith({ ...mockResult, xi_yong: { ...mockResult.xi_yong,
      strength: { method: 'sizhu-jingsui', level: '较弱', day_master: '丁',
                  day_master_wuxing: '火', static_scores: {}, final_scores: {},
                  ge_ju: { type: 'zheng', hua_shen: null, basis: [], neng_duli: true },
                  steps: [], dayun_adjustments: [] } } } as never)
    expect(w.find('[data-testid="strength-level"]').exists()).toBe(true)
    expect(w.find('[data-testid="v2-level"]').exists()).toBe(false)
  })

  it('改造前保存的旧记录（无 strength）正常显示兜底', () => {
    const w = mountWith(withLegacy)
    expect(w.find('[data-testid="v2-level"]').exists()).toBe(false)
    expect(w.text()).toContain('旧')
  })
})

// ---------------------------------------------------------------
// ChartDisplay：v2 结果必须走「查看计算过程」，不得显示旧版口径提示
// ---------------------------------------------------------------

import ChartDisplay from '../src/components/ChartDisplay.vue'

function mountChart(strength: unknown) {
  setActivePinia(createPinia())
  const result = JSON.parse(JSON.stringify(mockResult))
  result.xi_yong.strength = strength
  return mount(ChartDisplay, { props: { result } })
}

describe('ChartDisplay — 喜忌推演入口', () => {
  it('v2 结果显示「查看计算过程」，**不**显示旧版口径提示', () => {
    const w = mountChart(v2Strength)
    expect(w.find('[data-testid="strength-link"]').exists()).toBe(true)
    expect(w.text()).not.toContain('旧版口径')
  })

  it('005 期遗留形状的结果才显示旧版口径提示（与「被识别的旧引擎」区分）', () => {
    // 注意：`method: 'sizhu-jingsui'` 是**被识别**的旧引擎结论，仍走「查看计算过程」；
    // 「旧版口径」分支留给 005 期评分法那样的**更早形状**（无 method）。
    const w = mountChart({ score: 288, level: '中和' })
    expect(w.text()).toContain('旧版口径')
  })
})

describe('StrengthDetail — 推演分步展示', () => {
  it('各步骤**平铺展开**，不需要点开折叠面板', () => {
    const w = mountWith(withV2)
    // 每段都有独立的卡片，且步骤标题直接可见
    expect(w.find('[data-testid="v2-step-relations"]').exists()).toBe(true)
    expect(w.find('[data-testid="v2-step-tonggen"]').exists()).toBe(true)
    expect(w.find('[data-testid="v2-step-total"]').exists()).toBe(true)
    expect(w.text()).toContain('第 1 段 · 关系判定')
    expect(w.text()).toContain('第 4 段 · 通根递减')
    expect(w.text()).toContain('第 9 段 · 动态旺度与定级')
    // 不得再依赖 van-collapse 才能看到内容
    expect(w.findAll('.van-collapse-item').length).toBe(0)
  })

  it('静态旺度段展示**五行得分行**（木火土金水五格）', () => {
    const w = mountWith(withV2)
    const rows = w.findAll('[data-testid="v2-step-scores"]')
    expect(rows.length).toBeGreaterThan(0)
    const cells = rows[0].findAll('.score-cell')
    expect(cells.length).toBe(5)
    expect(cells.map((c) => c.find('.score-wx').text()).join('')).toBe('木火土金水')
  })

  it('静态旺度段除速览格外，还逐行给出每个五行的算式', () => {
    const w = mountWith(withV2)
    const step = w.find('[data-testid="v2-step-static"]')
    // 速览格照旧（五行 + 数值）
    expect(step.findAll('.score-cell').length).toBe(5)
    // 算式行：五项都要能看到来路，不能只留一个数
    const lines = step.findAll('.step-trace').map((l) => l.text())
    expect(lines.length).toBe(5)
    for (const line of lines) {
      expect(line).toContain('月令系数')
      expect(line).toMatch(/实际通根|地支藏干/)
    }
    expect(lines[2]).toContain('天干 2 度')
  })

  it('得分行的数值与后端 final_scores 一致', () => {
    const w = mountWith(withV2)
    const total = w.find('[data-testid="v2-step-total"]')
    const vals = total.findAll('.score-val').map((c) => c.text())
    expect(vals).toEqual(['0', '5.6', '7.8', '17.6', '6'])
  })

  it('规则与结果直接可见，无需交互', () => {
    const w = mountWith(withV2)
    const step = w.find('[data-testid="v2-step-total"]')
    expect(step.find('.step-rule').text()).toContain('十一档')
    expect(step.find('.step-result').text()).toContain('偏弱')
  })

  it('五行速览格紧邻命盘上方（都在段尾）', () => {
    const w = mountWith(withChart('static'))
    const step = w.find('[data-testid="v2-step-static"]')
    const scores = step.find('[data-testid="v2-step-scores"]')
    const chart = step.find('[data-testid="v2-step-chart-static"]')
    expect(scores.exists()).toBe(true)
    expect(chart.exists()).toBe(true)
    // 速览格在命盘之前，且两者之间只隔一个兄弟节点（相邻）
    const kids = Array.from((step.element as HTMLElement).children)
    const si = kids.indexOf(scores.element as HTMLElement)
    const ci = kids.indexOf(chart.element as HTMLElement)
    expect(ci).toBe(si + 1)            // 直接相邻，中间不夹别的节点
    // 结果行在速览格之前
    const ri = kids.findIndex((k) => k.classList.contains('step-result'))
    expect(ri).toBeLessThan(si)
  })
})

// ---------------------------------------------------------------
// 判定依据里的逐段命盘快照（steps[].chart）
// ---------------------------------------------------------------

/** 第 2 段（关系对藏干度数的影响）的快照：一支变纯 + 一支藏干减力，用来验标记。 */
const CHART = {
  pillars: [
    { key: 'year', label: '年', gan: '戊', gan_wx: '土', gan_degree: 2,
      gan_own: 0.8, gan_root: 1.2, gan_original: null, gan_change: null,
      zhi: '申', zhi_wx: '金', zhi_effective_wx: '金',
      hidden: [{ gan: '庚', wx: '金', degree: 6, change: null },
               { gan: '壬', wx: '水', degree: 3, change: null }],
      note: null },
    { key: 'month', label: '月', gan: '丙', gan_wx: '火', gan_degree: 1.5,
      gan_original: null, gan_change: null,
      zhi: '寅', zhi_wx: '木', zhi_effective_wx: '火',
      hidden: [{ gan: '丙', wx: '火', degree: 6, change: '变纯' }],
      note: '合化火成功：寅变纯火 6 度（书《下》第六节 半三合）；原藏 甲3、丙2、戊1' },
    { key: 'day', label: '日', gan: '戊', gan_wx: '土', gan_degree: 1.2,
      gan_original: null, gan_change: null,
      zhi: '辰', zhi_wx: '土', zhi_effective_wx: '土',
      hidden: [{ gan: '戊', wx: '土', degree: 1, change: null },
               { gan: '乙', wx: '木', degree: 0, change: '归零' },
               { gan: '癸', wx: '水', degree: 4, change: '减力' }],
      note: null },
    { key: 'time', label: '时', gan: '庚', gan_wx: '金', gan_degree: 0.7,
      gan_original: null, gan_change: null,
      zhi: '午', zhi_wx: '火', zhi_effective_wx: '火',
      hidden: [{ gan: '丁', wx: '火', degree: 4, change: null },
               { gan: '己', wx: '土', degree: 2, change: '新增' }],
      note: null },
  ],
}

/** 把 `chart` 挂到指定段上（不动其他段的 fixture）。
 *
 *  必须**深拷贝** `v2Strength`——直接引用会让 `s.chart = …` 写回共享对象，
 *  后跑的用例就带上前面用例挂过的图（曾经因此假红过一条）。 */
function withChart(...keys: string[]) {
  const result = JSON.parse(JSON.stringify(mockResult))
  result.xi_yong.strength = JSON.parse(JSON.stringify(v2Strength))
  for (const s of result.xi_yong.strength.steps) {
    if (keys.includes(s.key)) s.chart = CHART
  }
  return result
}

describe('StrengthDetail — 判定依据的分段命盘快照（012）', () => {
  it('带 chart 的段渲染一张快照，四柱齐全', () => {
    const w = mountWith(withChart('relations'))
    const chart = w.find('[data-testid="v2-step-chart-relations"]')
    expect(chart.exists()).toBe(true)
    expect(chart.text()).toContain('本段结束时的命盘')
    expect(chart.findAll('[data-testid^="v2-chart-"]').length).toBeGreaterThanOrEqual(4)
    expect(chart.find('[data-testid="v2-chart-year"]').text()).toContain('申')
  })

  it('不带 chart 的段不渲染快照（格局 / 取用段不改度数）', () => {
    const w = mountWith(withChart('relations'))
    expect(w.find('[data-testid="v2-step-chart-total"]').exists()).toBe(false)
    expect(w.find('[data-testid="v2-step-chart-static"]').exists()).toBe(false)
  })

  it('每个天干与藏干都显示度数', () => {
    const w = mountWith(withChart('relations'))
    const year = w.find('[data-testid="v2-chart-year"]')
    // 天干度数贴在干后面，藏干度数贴在字后面
    expect(year.find('.pillar-deg').text()).toBe('2')
    const rows = year.findAll('[data-testid="v2-chart-hidden-year"]')
    expect(rows.length).toBe(2)
    expect(rows[0].text()).toContain('庚')
    expect(rows[0].find('.cang-deg').text()).toBe('6')
  })

  it('变纯的支改按化神五行显示并标「变X」（原字说明不展示）', () => {
    const w = mountWith(withChart('relations'))
    const month = w.find('[data-testid="v2-chart-month"]')
    expect(month.find('.pillar-changed').text()).toContain('变火')
    expect(month.find('.cang-mark').text()).toBe('变纯')
    expect(w.findAll('[data-testid^="v2-chart-note-"]').length).toBe(0)
  })

  it('藏干的增/减/归零分别标出，归零加删除线', () => {
    const w = mountWith(withChart('relations'))
    const day = w.find('[data-testid="v2-chart-day"]')
    const rows = day.findAll('[data-testid="v2-chart-hidden-day"]')
    expect(rows[1].find('.cang-mark').text()).toBe('归零')
    expect(rows[1].classes()).toContain('is-off')
    expect(rows[2].find('.cang-mark').text()).toBe('减力')
    const time = w.find('[data-testid="v2-chart-time"]')
    expect(time.findAll('[data-testid="v2-chart-hidden-time"]')[1].find('.cang-mark').text()).toBe('新增')
  })

  it('第 5 段起天干只在小字里补「自身」，不显示「根」', () => {
    const w = mountWith(withChart('static'))
    const year = w.find('[data-testid="v2-chart-year"]')
    expect(year.find('[data-testid="v2-gan-own-year"]').text()).toBe('自身 0.8')
    expect(year.text()).not.toContain('根')
    // 主数仍是组旺度
    expect(year.find('.pillar-deg').text()).toBe('2')
  })

  it('天干显示该干本身的度数（生度数或乘过月令系数的旺度数），不显示通根/组合计', () => {
    const w = mountWith(withChart('tonggen'))
    const day = w.find('[data-testid="v2-chart-day"]')
    // 干下不再挂「通根 X 度」小注（只在有字变时才有一行）
    expect(day.find('.pillar-sub').exists()).toBe(false)
    // 度数就是那个干自己的——静态旺度起已是乘过月令系数的旺度数
    expect(day.find('.pillar-deg').text()).toBe('1.2')
  })

  it('生克结算段按次序逐实例贴命盘，且不再重复贴段末那张', () => {
    const w = mountWith(withPoints())
    const step = w.find('[data-testid="v2-step-stem_shengke"]')
    expect(step.find('[data-testid="v2-step-chart-stem_shengke-1"]').exists()).toBe(true)
    expect(step.find('[data-testid="v2-step-chart-stem_shengke-2"]').exists()).toBe(true)
    expect(step.find('[data-testid="v2-step-chart-stem_shengke"]').exists()).toBe(false)
    // 图插在算式行之后，不是全堆在段尾
    const kids = Array.from((step.element as HTMLElement).children)
    const chartIdx = kids.findIndex((k) => k.getAttribute('data-testid') === 'v2-step-chart-stem_shengke-1')
    const firstTrace = kids.findIndex((k) => k.classList.contains('step-trace'))
    const resultIdx = kids.findIndex((k) => k.classList.contains('step-result'))
    expect(chartIdx).toBeGreaterThan(firstTrace)
    expect(chartIdx).toBeLessThan(resultIdx)
  })
})

// ---------------------------------------------------------------
// 第 6 段 · 天干五合（合化换字 / 合绊减力）——2026-09-16 起排在静态旺度**之后**
// ---------------------------------------------------------------

/** 带天干五合结果的快照：月干甲己合化土 → 甲变戊；时干合而不化 → 合绊。 */
const HE_CHART = {
  pillars: [
    { key: 'year', label: '年', gan: '戊', gan_wx: '土', gan_degree: 0.8,
      gan_original: '甲', gan_change: '合化', gan_note: null,
      zhi: '辰', zhi_wx: '土', zhi_effective_wx: '土',
      hidden: [{ gan: '戊', wx: '土', degree: 1, change: null }], note: null },
    { key: 'month', label: '月', gan: '戊', gan_wx: '土', gan_degree: 0.8,
      gan_original: null, gan_change: '合绊', gan_note: null,
      zhi: '寅', zhi_wx: '木', zhi_effective_wx: '木',
      hidden: [{ gan: '甲', wx: '木', degree: 3, change: null }], note: null },
    { key: 'day', label: '日', gan: '丙', gan_wx: '火', gan_degree: 1.2,
      gan_original: null, gan_change: null, gan_note: null,
      zhi: '午', zhi_wx: '火', zhi_effective_wx: '火',
      hidden: [{ gan: '丁', wx: '火', degree: 4, change: null }], note: null },
    { key: 'time', label: '时', gan: '庚', gan_wx: '金', gan_degree: 1,
      gan_original: null, gan_change: null, gan_note: null,
      zhi: '申', zhi_wx: '金', zhi_effective_wx: '金',
      hidden: [{ gan: '庚', wx: '金', degree: 3, change: null }], note: null },
  ],
}

/** 生克结算段（第 8 段）带**逐实例快照**的样本。 */
function withPoints() {
  const result = JSON.parse(JSON.stringify(mockResult))
  result.xi_yong.strength = v2Strength
  result.xi_yong.strength.steps = [
    { key: 'stem_shengke', title: '第 8 段 · 生克结算（按实例）',
      rule: '逐实例「先受后施」', rulings: [],
      traces: [
        { target: '', expression: '木克土：年干甲 × 月干己 → 成数 -2/1', value: null },
        { target: '', expression: '土受克：日干己 6 → 5.4 度', value: null },
      ],
      charts: [
        { label: '同柱相 · 年支子本气癸', after: 1, chart: { pillars: HE_CHART.pillars } },
        { label: '本段结算完成', after: 2, chart: { pillars: HE_CHART.pillars } },
      ],
      chart: { pillars: HE_CHART.pillars },
      result: '实例层结算完成' },
  ]
  return result
}

function withStemHe() {
  const result = JSON.parse(JSON.stringify(mockResult))
  result.xi_yong.strength = { ...v2Strength, day_master: '丙', day_master_original: '戊' }
  for (const s of result.xi_yong.strength.steps) {
    if (s.key === 'stem_he' || s.key === 'relations') s.chart = HE_CHART
  }
  const he = {
    key: 'stem_he', title: '第 6 段 · 天干五合（换字 + 合绊减力）',
    rule: '只论相邻紧贴的天干。合化成功的换成化神干支；合而不化的以合绊论。',
    rulings: ['C26-18（争合失败时的合绊减力比例）'],
    traces: [{ target: '', expression: '戊甲合化土成功：年干甲变戊', value: null }],
    result: '合化成功，换字：甲→戊',
  }
  // 新段序：五合排在 `static`（第 5 段）**之后**，不是数组最前（旧 fixture 曾 unshift）。
  const at = result.xi_yong.strength.steps.findIndex((s: { key: string }) => s.key === 'static')
  result.xi_yong.strength.steps.splice(at + 1, 0, he)
  return result
}

describe('StrengthDetail — 第 6 段 天干五合（012）', () => {
  it('换字的干显示新字并标出原字与「合化」', () => {
    const w = mountWith(withStemHe())
    const year = w.find('[data-testid="v2-chart-year"]')
    expect(year.find('.pillar-gan').text()).toContain('戊')
    expect(year.find('[data-testid="v2-gan-changed-year"]').text()).toBe('原甲·合化')
  })

  it('合而不化的干标「合绊」且不减字', () => {
    const w = mountWith(withStemHe())
    const month = w.find('[data-testid="v2-chart-month"]')
    expect(month.find('.pillar-gan').text()).toContain('戊')
    expect(month.find('[data-testid="v2-gan-changed-month"]').text()).toBe('合绊')
    expect(month.find('.pillar-deg').text()).toBe('0.8')
  })

  it('未参与合化的干不带任何标记', () => {
    const w = mountWith(withStemHe())
    expect(w.find('[data-testid="v2-chart-day"] [data-testid="v2-gan-changed-day"]').exists())
      .toBe(false)
  })

  it('日主被合化改宗时在强弱卡标出原字', () => {
    const w = mountWith(withStemHe())
    const dm = w.find('[data-testid="v2-dm"]')
    expect(dm.text()).toContain('丙')
    expect(w.find('[data-testid="v2-dm-original"]').text()).toContain('原戊')
  })

  it('日主未换字时不显示原字标记', () => {
    const w = mountWith(withV2)
    expect(w.find('[data-testid="v2-dm-original"]').exists()).toBe(false)
  })
})
