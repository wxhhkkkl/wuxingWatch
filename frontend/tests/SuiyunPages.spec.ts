/**
 * 013 期 T032 —— 两个岁运页面（「加入大运」/「加入流年」）。
 *
 * 裁定依据：spec FR-016c（两阶段**成对呈现**）、FR-016a（**引擎不合成吉凶**）、
 * FR-021b（阶段 2 须含调候与格局层次）、FR-021c（阶段 3 按该年同口径重判）、
 * FR-024（**来源阶段三元标注**）、FR-025（三类降级）、FR-026（按需实时算、不落库）。
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { mockResult, mockInputs } from './fixtures'
import type { SuiyunResponse, V2DayunStep } from '../src/types'

const back = vi.fn()
const push = vi.fn()
let routeQuery: Record<string, string> = {}

vi.mock('vue-router', () => ({
  useRouter: () => ({ back, push }),
  useRoute: () => ({ query: routeQuery }),
}))

const fetchSuiyun = vi.fn()
const getRecordSuiyun = vi.fn()
const getRecord = vi.fn()
vi.mock('../src/api/charts', () => ({
  fetchSuiyun: (...a: unknown[]) => fetchSuiyun(...a),
  predictChart: vi.fn(),
  fetchChartImage: vi.fn(),
  fetchLiuShi: vi.fn(),
}))
vi.mock('../src/api/records', () => ({
  getRecord: (...a: unknown[]) => getRecord(...a),
  getRecordSuiyun: (...a: unknown[]) => getRecordSuiyun(...a),
  saveRecord: vi.fn(),
  updateRecord: vi.fn(),
  listRecords: vi.fn(),
  deleteRecord: vi.fn(),
}))

import { useChartStore } from '../src/stores/chart'
import DayunDetail from '../src/pages/DayunDetail.vue'
import LiunianDetail from '../src/pages/LiunianDetail.vue'

// ---------------------------------------------------------------
// 后端形状的样板（依 contracts/suiyun-v2.md §3/§4/§5）
// ---------------------------------------------------------------

const GE_JU = {
  type: 'zheng' as const, hua_shen: null, cong_targets: [],
  neng_duli: true, liang_qi: null, basis: [],
}

function step(over: Partial<V2DayunStep>): V2DayunStep {
  return {
    source: 'dayun', ganzhi: '壬午', start_year: 1995, start_age_xu: 5,
    level: '偏弱', ge_ju: GE_JU,
    yong_shen: {
      empty: false, theoretical: { element: '水', basis: '' }, practical: null,
      tiaohou: null, xi_shen: ['金'], ji_shen: ['土'], xian_shen: [],
      tier: { first: null, second: null, third: null }, direction: null,
      basis: '取用依据',
    },
    relations: { established: [], rejected: [] },
    transition: null, deltas: [], scores_after: {},
    ...over,
  } as V2DayunStep
}

const PAIRS = [
  { key: 'yong_shen.theoretical.element', label: '用神' },
  { key: 'yong_shen.xi_shen', label: '喜神' },
  { key: 'yong_shen.ji_shen', label: '忌神' },
  { key: 'level', label: '旺度档位' },
  { key: 'ge_ju.type', label: '格局' },
  { key: 'tiaohou', label: '调候' },
  { key: 'layers', label: '格局层次' },
].map((p) => ({
  ...p,
  dayun: { value: '大运值', source: 'dayun' as const },
  liunian: { value: '流年值', source: 'liunian' as const },
  changed: true,
}))

const STAGE2: SuiyunResponse = {
  engine: 'wangdu-v2', contract_version: 2, stage: 2, degradations: [],
  dayun: step({
    tiaohou: { element: '水', basis: '阶段 2 调候依据', met: true, quantified: '已有水', position: null },
    layers: { verdict: '中', met: [], missing: [], penalties: [], basis: '阶段 2 层次依据' },
  }),
  liunian: null, pairs: null,
}

const STAGE3: SuiyunResponse = {
  ...STAGE2,
  stage: 3,
  liunian: step({ source: 'liunian', liunian: '丙午', ganzhi: '壬午', level: '中和' }),
  pairs: PAIRS as SuiyunResponse['pairs'],
}

function mountPage(cmp: unknown, chart?: Record<string, unknown>) {
  setActivePinia(createPinia())
  const store = useChartStore()
  const result = structuredClone(mockResult) as unknown as Record<string, unknown>
  if (chart) Object.assign(result, chart)
  store.set(result as never, { ...mockInputs })
  return mount(cmp as never)
}

beforeEach(() => {
  routeQuery = {}
  fetchSuiyun.mockReset().mockResolvedValue(structuredClone(STAGE2))
  getRecordSuiyun.mockReset().mockResolvedValue(structuredClone(STAGE3))
  getRecord.mockReset().mockImplementation(async (id: number) =>
    ({ id, chart_result: structuredClone(mockResult) }))
  back.mockReset()
  push.mockReset()
})

// ---------------------------------------------------------------
// 阶段 2 —— 「加入大运」页
// ---------------------------------------------------------------

describe('DayunDetail（加入大运）', () => {
  it('按当前选中大运取**阶段 2** 结论，并标出「属大运」', async () => {
    const w = mountPage(DayunDetail)
    await flushPromises()
    expect(fetchSuiyun).toHaveBeenCalledTimes(1)
    expect(fetchSuiyun.mock.calls[0][0]).toMatchObject({ dayun_ganzhi: '壬午' })
    expect(fetchSuiyun.mock.calls[0][0].liunian_year).toBeUndefined()
    expect(w.get('[data-testid="sy-stage"]').text()).toContain('大运')
    expect(w.get('[data-testid="sy-dayun-source"]').text()).toContain('属大运')
  })

  it('含**调候量化**与**格局层次**两项（FR-021b），且按该步同口径重判', async () => {
    const w = mountPage(DayunDetail)
    await flushPromises()
    expect(w.get('[data-testid="sy-dayun-tiaohou"]').text()).toContain('阶段 2 调候依据')
    expect(w.get('[data-testid="sy-dayun-layers"]').text()).toContain('阶段 2 层次依据')
  })

  it('切换大运步 → 按**新那一步**重新请一次', async () => {
    const w = mountPage(DayunDetail, {
      da_yun: { start_age: 5, start_month: 7, steps: [
        { ganzhi: '癸巳', start_year: 1995, end_year: 2004 },
        { ganzhi: '甲午', start_year: 2005, end_year: 2014 },
      ] },
    })
    await flushPromises()
    expect(fetchSuiyun.mock.calls[0][0].dayun_ganzhi).toBe('癸巳')
    await w.get('[data-testid="sy-dayun-select"]').setValue('1')
    await flushPromises()
    expect(fetchSuiyun.mock.calls.at(-1)![0].dayun_ganzhi).toBe('甲午')
  })

  it('无出生日期（四柱输入）→ 降级提示，且**不发请求**（FR-025）', async () => {
    setActivePinia(createPinia())
    const store = useChartStore()
    store.set({ ...structuredClone(mockResult), solar_birth: null,
                da_yun: { start_age: 0, start_month: 0, steps: [] } } as never,
              { ...mockInputs })
    const w = mount(DayunDetail)
    await flushPromises()
    expect(fetchSuiyun).not.toHaveBeenCalled()
    expect(w.get('[data-testid="sy-degrade"]').text()).toContain('出生')
  })

  it('尚未起运（无大运步）→ 降级提示，且**不发请求**（FR-025）', async () => {
    const w = mountPage(DayunDetail, { da_yun: { start_age: null, start_month: null, steps: [] } })
    await flushPromises()
    expect(fetchSuiyun).not.toHaveBeenCalled()
    expect(w.get('[data-testid="sy-degrade"]').text()).toContain('起运')
  })

  it('时辰不详 → **不阻断**推导，仅明示该维缺失（FR-025）', async () => {
    const w = mountPage(DayunDetail, { missing_parts: ['hour_pillar'] })
    await flushPromises()
    expect(fetchSuiyun).toHaveBeenCalledTimes(1)
    expect(w.text()).toContain('时辰不详')
    expect(w.find('[data-testid="sy-degrade"]').exists()).toBe(false)
  })

  it('记录路径：带 ?record=<id> 时走记录端点（当场重推，FR-021a）', async () => {
    routeQuery = { record: '7' }
    const w = mountPage(DayunDetail)
    await flushPromises()
    expect(getRecordSuiyun.mock.calls[0][0]).toBe(7)
    expect(fetchSuiyun).not.toHaveBeenCalled()
  })
})

// ---------------------------------------------------------------
// 阶段 3 —— 「加入流年」页（成对呈现）
// ---------------------------------------------------------------

describe('LiunianDetail（加入流年）', () => {
  // 该页要的是**阶段 3**（带 pairs），故本组默认换成 STAGE3
  beforeEach(() => { fetchSuiyun.mockResolvedValue(structuredClone(STAGE3)) })

  it('取**阶段 3**——既带大运阶段也带流年阶段', async () => {
    const w = mountPage(LiunianDetail)
    await flushPromises()
    expect(fetchSuiyun).toHaveBeenCalledTimes(1)
    expect(fetchSuiyun.mock.calls[0][0].liunian_year).toBe(1995)
    expect(w.get('[data-testid="sy-stage"]').text()).toContain('流年')
  })

  it('**7 类同名判断成对罗列**，每对两侧齐备并各标来源（FR-016c / SC-009）', async () => {
    const w = mountPage(LiunianDetail)
    await flushPromises()
    const rows = w.findAll('[data-testid^="sy-pair-"]')
      .filter((r) => !/-dayun$|-liunian$/.test(r.attributes('data-testid')!))
    expect(rows).toHaveLength(7)
    for (const p of PAIRS) {
      const row = w.get(`[data-testid="sy-pair-${p.key}"]`)
      expect(row.get(`[data-testid="sy-pair-${p.key}-dayun"]`).text())
        .toContain('属大运')
      expect(row.get(`[data-testid="sy-pair-${p.key}-liunian"]`).text())
        .toContain('属流年')
    }
    expect(w.text()).toContain('调候')
    expect(w.text()).toContain('格局层次')
  })

  it('页面**不出现吉凶结论**（FR-016a）——只做同名项对照，不出档位/断语', async () => {
    const w = mountPage(LiunianDetail)
    await flushPromises()
    const text = w.text()
    // 注：页面自己有「引擎不合成吉凶」这句**说明**，那是 FR-016a 的声明本身，
    // 不是吉凶结论——故这里查的是**结论性**字样，不是「吉凶」二字。
    for (const bad of ['大吉', '大凶', '吉凶等级', '断语', '宜忌', '宜：', '忌：']) {
      expect(text).not.toContain(bad)
    }
    // 每对只渲染「名目 + 属大运一侧 + 属流年一侧」三格——没有被塞进吉凶档位的余地
    for (const p of PAIRS) {
      const row = w.get(`[data-testid="sy-pair-${p.key}"]`)
      expect(row.element.children).toHaveLength(3)
      expect(row.text()).toContain('属大运')
      expect(row.text()).toContain('属流年')
    }
  })

  it('切换年份 → 按新年重新请一次（用神随流年重判，FR-016b）', async () => {
    const w = mountPage(LiunianDetail)
    await flushPromises()
    fetchSuiyun.mockResolvedValue(structuredClone(STAGE3))
    await w.get('[data-testid="sy-year-select"]').setValue('2000')
    await flushPromises()
    expect(fetchSuiyun.mock.calls.at(-1)![0]).toMatchObject({ liunian_year: 2000 })
  })

  it('记录路径：带 ?record=<id> 时走记录端点', async () => {
    routeQuery = { record: '9' }
    const w = mountPage(LiunianDetail)
    await flushPromises()
    expect(getRecordSuiyun.mock.calls[0][0]).toBe(9)
  })
})
