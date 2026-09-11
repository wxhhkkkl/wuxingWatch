import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { mockResult } from './fixtures'

const back = vi.fn()
const push = vi.fn()
vi.mock('vue-router', () => ({ useRouter: () => ({ back, push }) }))

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
    { key: 'total', title: '第 7 段 · 动态旺度与定级',
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

  it('判定依据含规则、口径裁定编号与算式', () => {
    const w = mountWith(withV2)
    expect(w.findAll('[data-testid="v2-step-rulings"]').length).toBeGreaterThan(0)
    expect(w.text()).toContain('O-5')
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
    expect(w.text()).toContain('第 7 段 · 动态旺度与定级')
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

  it('口径裁定编号直接展示在卡片内', () => {
    const w = mountWith(withV2)
    const rulings = w.findAll('[data-testid="v2-step-rulings"]')
    expect(rulings.length).toBeGreaterThan(0)
    expect(rulings[0].text()).toContain('O-5')
  })
})
