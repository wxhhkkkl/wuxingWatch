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
import GeJuDetail from '../src/pages/GeJuDetail.vue'

const CIT = { chapter: '第一章', section: '第二节', condition_no: '1', page: '书 p.11' }
const GE = {
  id: 'zheng_guan_pei_yin', name: '正官配印格', aliases: ['正官配印'],
  category: 'inner', big_ge: '正官格', sub_ge: '正官配印格',
}

function resp() {
  return {
    engine: 'ziping-geju', rules_version: 'abc', input_scope: 'four_pillars',
    degradations: [],
    yuanju: {
      engine: 'ziping-geju', rules_version: 'abc', input_scope: 'four_pillars',
      degradations: [], main_ge: GE, main_ge_basis: { text: '正官当令', citation: CIT },
      concurrent_ge: [], status: 'undetermined', missing_conditions: ['官星不被合'],
      shen_qiang_ruo: { value: 'weak', score: 6.4, source: 'yuanju' },
      yong_shen: { element: '土', ten_god: '正官', book_term: '正官',
                    role: '格神', reason: '正官配印格：格神取正官', citation: CIT },
      xiang_shen: [{ element: '金', ten_god: '正印', book_term: '印绶',
                     role: '相神', reason: '辅佐格神正官', citation: CIT }],
      xi_shen: [{ element: '金', ten_god: '正印', book_term: '印绶',
                  reason: '生助格神/相神', citation: CIT }],
      ji_shen: [{ element: '木', ten_god: '食伤', book_term: '食伤',
                  reason: '克破/耗泄格神', citation: CIT }],
      remedy: { text: '印伏伤', element: '', path: '印伏伤', result: '复成', citation: CIT },
      disease: [{ text: '伤官透干克官', element: '', citation: CIT }],
      gao_di: { value: '中', reasons: ['破而复成：印伏伤'], citations: [CIT] },
      conditions: [{ id: 'zgpy-c1', text: '正官当令', result: true, branch: null, citation: CIT, note: '' }],
      citations: [CIT],
      open_issues: [{
        id: 'OI-1', location: CIT, kind: 'unspecified',
        texts: [{ source: CIT, text: '官星不被合' }], status: 'open', resolution: null,
      }],
    },
    dayun_steps: [], open_issues: [],
  }
}

describe('GeJuDetail', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.mocked(fetchGeju).mockResolvedValue(resp() as never)
  })

  it('renders main ge, conditions and open issues', async () => {
    useChartStore().set(mockResult, mockInputs)
    const w = mount(GeJuDetail)
    await flushPromises()
    expect(w.find('[data-testid="geju-main"]').text()).toContain('正官配印格')
    expect(w.find('[data-testid="cond-zgpy-c1"]').text()).toContain('正官当令')
    expect(w.find('[data-testid="geju-open-issues"]').text()).toContain('官星不被合')
    expect(w.find('[data-testid="geju-yongxi"]').text()).toContain('土（正官）')
    expect(w.find('[data-testid="geju-yongxi"]').text()).toContain('金（印绶）')
    expect(w.find('[data-testid="geju-chengpo"]').text()).toContain('印伏伤')
    expect(w.find('[data-testid="geju-chengpo"]').text()).toContain('层次 中')
    expect(w.text()).toContain('第一章')
  })
})
