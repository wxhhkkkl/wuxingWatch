/**
 * T021 — 命盘图关系条件判定（008：《四柱精髓》口径）。
 * 对拍基准 specs/008-yongshen-steps/fixtures/relation-cases.json（与后端 test_wangdu.py 共读）。
 */
import { describe, it, expect } from 'vitest'
import { buildRelationJudgments, type Judgment, type RelCol } from '../src/utils/relations'
import { GAN_WUXING, ZHI_WUXING } from '../src/utils/wuxing'
import fixtures from '../../specs/008-yongshen-steps/fixtures/relation-cases.json'

function mkCol(id: string, gan: string, zhi: string): RelCol {
  return {
    id, label: id, gan, ganWx: GAN_WUXING[gan] ?? '', zhi, zhiWx: ZHI_WUXING[zhi] ?? '', canggan: [],
  }
}

function mkCols(pillars: string[], dayun?: string): RelCol[] {
  const cols: RelCol[] = []
  if (dayun) cols.push(mkCol('dayun', dayun.length > 1 ? dayun[0] : '', dayun[dayun.length - 1]))
  const ids = ['year', 'month', 'day', 'time']
  pillars.forEach((gz, i) => cols.push(mkCol(ids[i], gz[0], gz[1])))
  return cols
}

interface FixturePair {
  a: string
  b: string
  layer: string
  type: string
  detail?: string
  reason?: string
  positions?: string[]
  involves?: string
}

function norm(pairs: (Judgment | FixturePair)[]): Set<string> {
  const out = new Set<string>()
  for (const p of pairs) {
    const [a, b] = [p.a, p.b].sort()
    const key = [
      a, b, p.layer, p.type,
      ('detail' in p && p.detail) || ('reason' in p && p.reason) || '',
      [...(p.positions ?? [])].sort().join(','),
      p.involves ?? '',
    ].join('|')
    out.add(key)
  }
  return out
}

describe('关系条件判定 · fixtures 对拍', () => {
  for (const c of fixtures.cases) {
    it(c.name, () => {
      const result = buildRelationJudgments(mkCols(c.pillars, c.dayun))
      expect(norm(result.established)).toEqual(norm(c.expected_established as FixturePair[]))
      expect(norm(result.rejected)).toEqual(norm(c.expected_rejected as FixturePair[]))
    })
  }
})

describe('关系判定 · 结构与交互约束', () => {
  const cols = () => [
    mkCol('dayun', '己', '卯'),
    mkCol('year', '戊', '酉'),
    mkCol('month', '戊', '戌'),
    mkCol('day', '戊', '子'),
    mkCol('time', '戊', '午'),
  ]

  it('天干层与地支层互不混入', () => {
    const { established, rejected } = buildRelationJudgments(cols())
    const all = [...established, ...rejected]
    expect(all.every((p) => p.layer === 'stem' || p.layer === 'branch')).toBe(true)
    expect(established.filter((p) => p.layer === 'stem').every((p) => ['五合', '冲', '生', '克'].includes(p.type))).toBe(true)
    expect(
      [...established, ...rejected]
        .filter((p) => p.layer === 'branch')
        .every((p) => ['六合', '相冲', '半三合', '三合', '三会', '三刑', '刑', '害', '破'].includes(p.type)),
    ).toBe(true)
  })

  it('excludeColIds：排除大运/流年后只按四柱判定', () => {
    const withAll = buildRelationJudgments(cols())
    const without = buildRelationJudgments(cols(), { excludeColIds: ['dayun', 'liunian'] })
    expect(withAll.established.some((p) => p.involves === 'dayun')).toBe(true) // 运卯与戌六合（合绊）
    expect(without.established.every((p) => !p.involves)).toBe(true)
    expect(without.rejected.every((p) => !p.involves)).toBe(true)
  })

  it('三支齐备时成局只报一次并携带 members', () => {
    const c = [mkCol('year', '甲', '申'), mkCol('month', '壬', '子'), mkCol('day', '戊', '辰'), mkCol('time', '庚', '午')]
    const { established } = buildRelationJudgments(c)
    const sanhe = established.filter((p) => p.type === '三合')
    expect(sanhe.length).toBe(1)
    expect(new Set(sanhe[0].members)).toEqual(new Set(['申', '子', '辰']))
    // 子月水旺 + 壬透 → 合化水
    expect(sanhe[0].detail).toBe('合化水')
  })

  it('缺时柱（time 列缺失）不报错且涉及时柱关系不出现', () => {
    const c = [mkCol('year', '戊', '子'), mkCol('month', '戊', '寅'), mkCol('day', '戊', '丑')]
    const { established, rejected } = buildRelationJudgments(c)
    expect([...established, ...rejected].every((p) => p.aColId !== 'time' && p.bColId !== 'time')).toBe(true)
  })
})

// ---------- 009 两阶段（2026-08-19）：地支论处先后按书原文分层（与后端 BRANCH_TIER 对拍） ----------

describe('009 地支论处先后分层', () => {
  it('六冲让位六合（书 §9：六冲先于六合）', () => {
    // 午子冲 与 子丑合 共享子支 → 论冲不论合
    const { established } = buildRelationJudgments(mkCols(['庚午', '戊子', '己丑', '庚寅']))
    const chong = established.filter((p) => p.type === '相冲' && new Set([p.a, p.b]).size === 2)
    const he = established.filter((p) => p.type === '六合')
    expect(chong.some((p) => new Set([p.a, p.b]).has('子') && new Set([p.a, p.b]).has('午'))).toBe(true)
    expect(he.filter((p) => new Set([p.a, p.b]).has('子'))).toHaveLength(0)
  })

  it('字面多关系只保留最高层：巳申=六合（非刑）、寅申=相冲（非刑）、寅巳=刑（非害）', () => {
    const siShen = buildRelationJudgments([mkCol('year', '甲', '巳'), mkCol('month', '壬', '申')])
    expect(siShen.established.filter((p) => p.type === '六合' && new Set([p.a, p.b]).has('巳'))).toHaveLength(1)
    expect(siShen.established.filter((p) => p.type === '刑' && new Set([p.a, p.b]).has('巳'))).toHaveLength(0)
    const yinShen = buildRelationJudgments([mkCol('year', '甲', '寅'), mkCol('month', '壬', '申')])
    expect(yinShen.established.filter((p) => p.type === '相冲' && new Set([p.a, p.b]).has('寅'))).toHaveLength(1)
    const yinSi = buildRelationJudgments([mkCol('year', '甲', '寅'), mkCol('month', '壬', '巳')])
    expect(yinSi.established.filter((p) => p.type === '刑' && new Set([p.a, p.b]).has('寅'))).toHaveLength(1)
    expect(yinSi.established.filter((p) => p.type === '害' && new Set([p.a, p.b]).has('寅'))).toHaveLength(0)
  })
})
