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

const CIT = { chapter: '第九章', section: '第二节', condition_no: null, page: '书 p.392' }
const GE = {
  id: 'qu_zhi_ren_shou', name: '曲直仁寿格', aliases: ['曲直格'],
  category: 'outer', big_ge: '专旺格', sub_ge: '曲直仁寿格',
}

function resp() {
  return {
    engine: 'ziping-geju', rules_version: 'abc', input_scope: 'four_pillars',
    degradations: [],
    yuanju: {
      engine: 'ziping-geju', rules_version: 'abc', input_scope: 'four_pillars',
      degradations: [], main_ge: GE, main_ge_basis: { text: '比劫当令，有印', citation: CIT },
      concurrent_ge: [], status: 'undetermined', missing_conditions: ['无财官食可用'],
      shen_qiang_ruo: { value: 'strong', score: 20, source: 'yuanju' },
      yong_shen: null, xiang_shen: [], xi_shen: [], ji_shen: [],
      disease: [], remedy: null,
      gao_di: { value: '未定', reasons: ['成格条件未完整/存疑'], citations: [] },
      conditions: [], citations: [CIT],
      open_issues: [{
        id: 'OI-1', location: CIT, kind: 'unspecified',
        texts: [{ source: CIT, text: '无财官食可用，或虽有一点不能立足' }],
        status: 'open', resolution: null,
      }],
    },
    dayun_steps: [], open_issues: [],
  }
}

describe('GeJu 外格展示', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.mocked(fetchGeju).mockResolvedValue(resp() as never)
  })

  it('renders an outer ge with its open issue', async () => {
    useChartStore().set(mockResult, mockInputs)
    const w = mount(GeJuDetail)
    await flushPromises()
    expect(w.find('[data-testid="geju-main"]').text()).toContain('曲直仁寿格')
    expect(w.find('[data-testid="geju-open-issues"]').text()).toContain('无财官食可用')
    expect(w.text()).toContain('第九章')
  })
})
