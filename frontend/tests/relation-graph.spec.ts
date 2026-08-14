import { describe, it, expect } from 'vitest'
import { buildRelationPairs, REL_TYPES, type RelType } from '../src/utils/relations'
import { GAN_WUXING, ZHI_WUXING } from '../src/utils/wuxing'

const col = (id: string, label: string, gan: string, ganWx: string, zhi: string, zhiWx: string) => ({
  id, label, gan, ganWx, zhi, zhiWx, canggan: [],
})

const layerOf = (id: string) => id.split('-')[0]
const ganPairs = (cols: ReturnType<typeof col>[]) =>
  buildRelationPairs(cols).filter((p) => layerOf(p.a) === 'gan')
const zhiPairs = (cols: ReturnType<typeof col>[]) =>
  buildRelationPairs(cols).filter((p) => layerOf(p.a) === 'zhi')

describe('天干关系（仅天干层）', () => {
  it('五合（甲己/乙庚/丙辛/丁壬/戊癸）', () => {
    expect(ganPairs([col('a', 'a', '甲', '木', '子', '水'), col('b', 'b', '己', '土', '丑', '土')])).toContainEqual(
      expect.objectContaining({ type: '合', detail: '甲己合' }),
    )
    expect(ganPairs([col('a', 'a', '乙', '木', '子', '水'), col('b', 'b', '庚', '金', '丑', '土')])[0].detail).toBe('乙庚合')
  })
  it('合化（甲己化土/乙庚化金/丙辛化水/丁壬化木/戊癸化火）', () => {
    expect(ganPairs([col('a', 'a', '甲', '木', '子', '水'), col('b', 'b', '己', '土', '丑', '土')])).toContainEqual(
      expect.objectContaining({ type: '合化', detail: '甲己合化土' }),
    )
    expect(ganPairs([col('a', 'a', '丙', '火', '子', '水'), col('b', 'b', '辛', '金', '丑', '土')]).find((p) => p.type === '合化')!.detail).toBe('丙辛合化水')
    expect(ganPairs([col('a', 'a', '丁', '火', '子', '水'), col('b', 'b', '壬', '水', '丑', '土')]).find((p) => p.type === '合化')!.detail).toBe('丁壬合化木')
    expect(ganPairs([col('a', 'a', '戊', '土', '子', '水'), col('b', 'b', '癸', '水', '丑', '土')]).find((p) => p.type === '合化')!.detail).toBe('戊癸合化火')
  })
  it('相冲（甲庚/乙辛/丙壬/丁癸；戊己无冲）', () => {
    expect(ganPairs([col('a', 'a', '甲', '木', '子', '水'), col('b', 'b', '庚', '金', '丑', '土')])).toContainEqual(
      expect.objectContaining({ type: '冲', detail: '甲庚相冲' }),
    )
    expect(ganPairs([col('a', 'a', '戊', '土', '子', '水'), col('b', 'b', '己', '土', '丑', '土')]).some((p) => p.type === '冲')).toBe(false)
  })
  it('相生（木火/火土/土金/金水/水木）', () => {
    expect(ganPairs([col('a', 'a', '甲', '木', '子', '水'), col('b', 'b', '丙', '火', '丑', '土')])).toContainEqual(
      expect.objectContaining({ type: '生', detail: '甲丙相生' }),
    )
  })
  it('相克（金木/木土/土水/水火/火金）', () => {
    expect(ganPairs([col('a', 'a', '庚', '金', '子', '水'), col('b', 'b', '甲', '木', '丑', '土')])).toContainEqual(
      expect.objectContaining({ type: '克', detail: '庚甲相克' }),
    )
    expect(ganPairs([col('a', 'a', '甲', '木', '子', '水'), col('b', 'b', '戊', '土', '丑', '土')]).some((p) => p.type === '克')).toBe(true) // 木克土
  })
  it('天干层不含 刑/破/害/三合/三会', () => {
    const g = ganPairs([
      col('a', 'a', '甲', '木', '寅', '木'),
      col('b', 'b', '丙', '火', '巳', '火'),
      col('c', 'c', '戊', '土', '申', '金'),
    ])
    expect(g.every((p) => !['刑', '破', '害', '三合', '三会'].includes(p.type))).toBe(true)
  })
})

describe('地支关系（仅地支层）', () => {
  it('六合（子丑合土/寅亥合木…）', () => {
    expect(zhiPairs([col('a', 'a', '甲', '木', '子', '水'), col('b', 'b', '甲', '木', '丑', '土')])).toContainEqual(
      expect.objectContaining({ type: '六合', detail: '子丑合土' }),
    )
    expect(zhiPairs([col('a', 'a', '甲', '木', '寅', '木'), col('b', 'b', '甲', '木', '亥', '水')])[0].detail).toBe('寅亥合木')
    expect(zhiPairs([col('a', 'a', '甲', '木', '卯', '木'), col('b', 'b', '甲', '木', '戌', '土')])[0].detail).toBe('卯戌合火')
    expect(zhiPairs([col('a', 'a', '甲', '木', '辰', '土'), col('b', 'b', '甲', '木', '酉', '金')])[0].detail).toBe('辰酉合金')
    expect(zhiPairs([col('a', 'a', '甲', '木', '巳', '火'), col('b', 'b', '甲', '木', '申', '金')])[0].detail).toBe('巳申合水')
    expect(zhiPairs([col('a', 'a', '甲', '木', '午', '火'), col('b', 'b', '甲', '木', '未', '土')])[0].detail).toBe('午未合土')
  })
  it('相冲（子午/丑未/寅申/卯酉/辰戌/巳亥）', () => {
    expect(zhiPairs([col('a', 'a', '甲', '木', '子', '水'), col('b', 'b', '甲', '木', '午', '火')])).toContainEqual(
      expect.objectContaining({ type: '相冲', detail: '子午相冲' }),
    )
    expect(zhiPairs([col('a', 'a', '甲', '木', '巳', '火'), col('b', 'b', '甲', '木', '亥', '水')])[0].detail).toBe('巳亥相冲')
  })
  it('相刑（子卯/寅巳申/丑戌未/辰午酉亥自刑）', () => {
    expect(zhiPairs([col('a', 'a', '甲', '木', '子', '水'), col('b', 'b', '甲', '木', '卯', '木')])).toContainEqual(
      expect.objectContaining({ type: '刑', detail: '子卯相刑' }),
    )
    expect(zhiPairs([col('a', 'a', '甲', '木', '寅', '木'), col('b', 'b', '甲', '木', '巳', '火')]).some((p) => p.type === '刑')).toBe(true)
    expect(zhiPairs([col('a', 'a', '甲', '木', '丑', '土'), col('b', 'b', '甲', '木', '戌', '土')]).some((p) => p.type === '刑')).toBe(true)
    expect(zhiPairs([col('a', 'a', '甲', '木', '午', '火'), col('b', 'b', '甲', '木', '午', '火')]).some((p) => p.type === '刑')).toBe(true) // 自刑
  })
  it('六害（子未/丑午/寅巳/卯辰/申亥/酉戌）', () => {
    expect(zhiPairs([col('a', 'a', '甲', '木', '子', '水'), col('b', 'b', '甲', '木', '未', '土')])).toContainEqual(
      expect.objectContaining({ type: '害', detail: '子未相害' }),
    )
  })
  it('相破（子酉/午卯/巳申/亥寅/辰丑/戌未）', () => {
    expect(zhiPairs([col('a', 'a', '甲', '木', '子', '水'), col('b', 'b', '甲', '木', '酉', '金')])).toContainEqual(
      expect.objectContaining({ type: '破', detail: '子酉相破' }),
    )
    expect(zhiPairs([col('a', 'a', '甲', '木', '午', '火'), col('b', 'b', '甲', '木', '卯', '木')]).some((p) => p.type === '破')).toBe(true)
  })
  it('三合（申子辰/亥卯未/寅午戌/巳酉丑）', () => {
    expect(zhiPairs([
      col('a', 'a', '甲', '木', '申', '金'),
      col('b', 'b', '甲', '木', '子', '水'),
      col('c', 'c', '甲', '木', '辰', '土'),
    ])).toContainEqual(expect.objectContaining({ type: '三合', detail: '申子辰合水' }))
    expect(zhiPairs([
      col('a', 'a', '甲', '木', '申', '金'),
      col('b', 'b', '甲', '木', '子', '水'),
    ]).some((p) => p.type === '三合')).toBe(false) // 缺辰不成局
  })
  it('三会（亥子丑/寅卯辰/巳午未/申酉戌）', () => {
    expect(zhiPairs([
      col('a', 'a', '甲', '木', '亥', '水'),
      col('b', 'b', '甲', '木', '子', '水'),
      col('c', 'c', '甲', '木', '丑', '土'),
    ])).toContainEqual(expect.objectContaining({ type: '三会', detail: '亥子丑会水' }))
  })
  it('地支层不含 生/克/合化', () => {
    const z = zhiPairs([col('a', 'a', '甲', '木', '子', '水'), col('b', 'b', '甲', '木', '丑', '土')])
    expect(z.every((p) => !['生', '克', '合化'].includes(p.type))).toBe(true)
  })
})

describe('层隔离', () => {
  it('天干与地支的关系互不混入', () => {
    const cols = [col('a', 'a', '甲', '木', '子', '水'), col('b', 'b', '己', '土', '丑', '土')]
    // 天干层只含干关系
    expect(ganPairs(cols).every((p) => ['合', '合化', '冲', '生', '克'].includes(p.type))).toBe(true)
    // 地支层只含支关系
    expect(zhiPairs(cols).every((p) => ['六合', '相冲', '刑', '破', '害', '三合', '三会'].includes(p.type))).toBe(true)
    // 无藏干
    expect(buildRelationPairs(cols).some((p) => layerOf(p.a) === 'zang')).toBe(false)
  })
})

describe('按列子集判定（excludeColIds：不关联大运/流年）', () => {
  const withDayun = [
    col('dayun', '大运', '甲', '木', '子', '水'),
    col('year', '年柱', '己', '土', '丑', '土'),
    col('month', '月柱', '丙', '火', '寅', '木'),
  ]

  it('默认（不排他）包含大运/流年相关的关系', () => {
    const pairs = buildRelationPairs(withDayun)
    expect(pairs.some((p) => p.a === 'gan-dayun' || p.b === 'gan-dayun')).toBe(true) // 甲己合含大运
  })

  it('排除大运后，只剩四柱之间的关系', () => {
    const pairs = buildRelationPairs(withDayun, { excludeColIds: ['dayun'] })
    expect(pairs.every((p) => p.a !== 'gan-dayun' && p.b !== 'gan-dayun')).toBe(true)
    expect(pairs.every((p) => !p.a.includes('dayun') && !p.b.includes('dayun'))).toBe(true)
    // 四柱之间的关系仍在
    expect(pairs.length).toBeGreaterThan(0)
  })

  it('排除大运/流年后，成局只按四柱判定', () => {
    // 大运申 + 年子 + 月辰 凑成申子辰三合；排除大运后四柱无三合
    const cols = [
      col('dayun', '大运', '庚', '金', '申', '金'),
      col('year', '年柱', '甲', '木', '子', '水'),
      col('month', '月柱', '丙', '火', '辰', '土'),
      col('day', '日柱', '戊', '土', '午', '火'),
      col('time', '时柱', '壬', '水', '戌', '土'),
    ]
    expect(buildRelationPairs(cols).some((p) => p.type === '三合')).toBe(true) // 含大运成局
    expect(buildRelationPairs(cols, { excludeColIds: ['dayun'] }).some((p) => p.type === '三合')).toBe(false) // 仅四柱无三合
  })
})

describe('REL_TYPES', () => {
  it('covers all 12 relation types', () => {
    expect(REL_TYPES).toEqual(['生', '克', '合', '合化', '冲', '三会', '三合', '六合', '相冲', '刑', '害', '破'])
  })
})

describe('干支五行固定映射', () => {
  it('天干/地支五行固定映射', () => {
    expect(GAN_WUXING['庚']).toBe('金')
    expect(ZHI_WUXING['午']).toBe('火')
  })
})
