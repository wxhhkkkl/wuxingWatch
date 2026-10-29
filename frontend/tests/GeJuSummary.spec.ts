import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { mockResult, mockInputs } from './fixtures'

const push = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({ push, replace: vi.fn() }),
}))

vi.mock('../src/api/charts', () => ({
  fetchChartImage: vi.fn(),
  fetchLiuShi: vi.fn(),
  fetchDayun2: vi.fn().mockResolvedValue({ dayun_steps: [] }),
}))
vi.mock('../src/api/records', () => ({
  saveRecord: vi.fn(), updateRecord: vi.fn(), getRecordDayun2: vi.fn(),
  getRecordGeju: vi.fn(),
}))
vi.mock('../src/api/geju', () => ({
  fetchGeju: vi.fn(),
  getRecordGeju: vi.fn(),
}))

import { fetchGeju } from '../src/api/geju'
import { useChartStore } from '../src/stores/chart'
import ChartResult from '../src/pages/ChartResult.vue'

const GE = {
  id: 'zheng_guan_pei_yin', name: '正官配印格', aliases: ['正官配印'],
  category: 'inner', big_ge: '正官格', sub_ge: '正官配印格',
}
const CIT = { chapter: '第一章', section: '第二节', condition_no: '1', page: '书 p.11' }

function gejuResp() {
  return {
    engine: 'ziping-geju', rules_version: 'abc', input_scope: 'four_pillars',
    degradations: [],
    yuanju: {
      engine: 'ziping-geju', rules_version: 'abc', input_scope: 'four_pillars',
      degradations: [], main_ge: GE, main_ge_basis: { text: '正官当令', citation: CIT },
      concurrent_ge: [], status: 'undetermined', missing_conditions: ['官星不被合'],
      shen_qiang_ruo: { value: 'weak', score: 6.4, source: 'yuanju' },
      yong_shen: null, xiang_shen: [], xi_shen: [], ji_shen: [], disease: [],
      remedy: null, gao_di: { value: '未定', reasons: [], citations: [] },
      conditions: [{ id: 'zgpy-c1', text: '正官当令', result: true, branch: null, citation: CIT, note: '' }],
      citations: [CIT], open_issues: [],
    },
    dayun_steps: [{
      ganzhi: '壬午', start_year: 1995, start_age_xu: 6,
      shen_qiang_ruo: { value: 'strong', score: 12.3, source: 'dayun' },
      ge: GE, change: { type: null, reason: '', citation: null },
      diff: { strength: 'weak→strong', xi_ji: '未定', cheng_po: '未定', ge: '同原局' },
      yun_xi_ji: { xi: [], ji: [], citation: null }, conditions: [], open_issues: [],
    }],
    open_issues: [],
  }
}

describe('GeJu summary cards', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    push.mockClear()
    vi.mocked(fetchGeju).mockResolvedValue(gejuResp() as never)
  })

  it('shows 原局 and 当前大运 summary cards', async () => {
    useChartStore().set(mockResult, mockInputs)
    const w = mount(ChartResult)
    await flushPromises()
    expect(w.find('[data-testid="geju-yuanju-card"]').text()).toContain('正官配印格')
    expect(w.find('[data-testid="geju-yuanju-card"]').text()).toContain('未定')
    expect(w.find('[data-testid="geju-dayun-card"]').text()).toContain('当前大运格局喜忌')
  })

  it('opens the detail page from the original-chart card', async () => {
    useChartStore().set(mockResult, mockInputs)
    const w = mount(ChartResult)
    await flushPromises()
    const link = w.find('[data-testid="geju-yuanju-card"] [data-testid="geju-detail-link"]')
    await link.trigger('click')
    expect(push).toHaveBeenCalledWith('/geju')
  })
})
