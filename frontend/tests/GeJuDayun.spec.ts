import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { mockResult, mockInputs } from './fixtures'

const back = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({ back, push: vi.fn() }),
  useRoute: () => ({ query: {} }),
}))
vi.mock('../src/api/geju', () => ({
  fetchGeju: vi.fn(), getRecordGeju: vi.fn(),
}))
vi.mock('../src/api/records', () => ({ getRecord: vi.fn() }))

import { fetchGeju } from '../src/api/geju'
import { useChartStore } from '../src/stores/chart'
import GeJuDayunDetail from '../src/pages/GeJuDayunDetail.vue'

const CIT = { chapter: '第一章', section: '第二节', condition_no: null, page: '书 p.11' }
const GE = {
  id: 'zheng_guan_pei_yin', name: '正官配印格', aliases: ['正官配印'],
  category: 'inner', big_ge: '正官格', sub_ge: '正官配印格',
}

function step(ganzhi: string, value: string, score: number, change: unknown) {
  return {
    ganzhi, start_year: 1995, start_age_xu: 6,
    shen_qiang_ruo: { value, score, source: 'dayun' },
    ge: GE, change,
    diff: { strength: 'weak→strong', xi_ji: '同原局', cheng_po: '成格', ge: '同原局' },
    yun_xi_ji: { xi: ['木'], ji: ['土'], citation: CIT },
    conditions: [], open_issues: [],
  }
}

function resp() {
  return {
    engine: 'ziping-geju', rules_version: 'abc', input_scope: 'four_pillars',
    degradations: [],
    yuanju: {
      engine: 'ziping-geju', rules_version: 'abc', input_scope: 'four_pillars',
      degradations: [], main_ge: GE, main_ge_basis: null, concurrent_ge: [],
      status: 'undetermined', missing_conditions: [],
      shen_qiang_ruo: { value: 'weak', score: 6.4, source: 'yuanju' },
      yong_shen: null, xiang_shen: [], xi_shen: [], ji_shen: [], disease: [],
      remedy: null, gao_di: { value: '未定', reasons: [], citations: [] },
      conditions: [], citations: [], open_issues: [],
    },
    dayun_steps: [
      step('壬午', 'strong', 12.3, { type: null, reason: '', citation: null }),
      step('癸未', 'weak', 5.1, { type: '变格', reason: '假从变真从', citation: CIT }),
    ],
    open_issues: [],
  }
}

describe('GeJuDayunDetail', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    back.mockClear()
    vi.mocked(fetchGeju).mockResolvedValue(resp() as never)
  })

  it('switches steps and shows 变格 / diff', async () => {
    useChartStore().set(mockResult, mockInputs)
    const w = mount(GeJuDayunDetail)
    await flushPromises()
    expect(w.find('[data-testid="geju-step-壬午"]').exists()).toBe(true)
    await w.find('[data-testid="geju-step-癸未"]').trigger('click')
    expect(w.find('[data-testid="geju-dayun-verdict"]').text()).toContain('变格')
    expect(w.find('[data-testid="geju-dayun-verdict"]').text()).toContain('假从变真从')
    expect(w.find('[data-testid="geju-dayun-verdict"]').text()).toContain('weak→strong')
  })
})
