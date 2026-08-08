import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import type { RecordSummary } from '../src/types'

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
}))

vi.mock('../src/api/records', () => ({
  listRecords: vi.fn(),
  deleteRecord: vi.fn(),
}))

import Records from '../src/pages/Records.vue'
import { listRecords } from '../src/api/records'

const flush = () => new Promise((r) => setTimeout(r))

const sample: RecordSummary[] = [
  {
    id: 1,
    person_name: '儿子',
    relationship: 'CHILD',
    birth_solar: '1990-05-20T10:30:00',
    created_at: '2026-08-08T00:00:00',
    summary: { year: null, month: null, day: null, time: null },
  },
]

describe('Records', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.mocked(listRecords).mockReset()
  })

  it('lists saved records', async () => {
    vi.mocked(listRecords).mockResolvedValue(sample)
    const wrapper = mount(Records)
    await flush()
    expect(wrapper.text()).toContain('儿子')
    expect(wrapper.text()).toContain('子女')
  })

  it('shows empty state when no records', async () => {
    vi.mocked(listRecords).mockResolvedValue([])
    const wrapper = mount(Records)
    await flush()
    expect(wrapper.text()).toContain('还没有保存的排盘记录')
  })
})
