import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

import GeJuSummaryCard from '../src/components/GeJuSummaryCard.vue'

const GE = {
  id: 'zheng_guan_pei_yin', name: '正官配印格', aliases: ['正官配印'],
  category: 'inner', big_ge: '正官格', sub_ge: '正官配印格',
}

function mountWith(value: 'strong' | 'weak' | 'unknown', score: number) {
  return mount(GeJuSummaryCard, {
    props: {
      title: '原局格局喜忌', ge: GE as never, status: 'cheng',
      strength: { value, score, source: 'yuanju' } as never, to: '/geju',
    },
  })
}

describe('GeJu strength display', () => {
  it('shows 身弱 with score', () => {
    expect(mountWith('weak', 6.4).text()).toContain('身弱 · 6.4 度')
  })

  it('shows 身强 with score', () => {
    expect(mountWith('strong', 12.3).text()).toContain('身强 · 12.3 度')
  })

  it('shows 未知 when strength is unknown', () => {
    expect(mountWith('unknown', 0).text()).toContain('身强弱未知')
  })
})
