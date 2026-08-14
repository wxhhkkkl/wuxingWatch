import { describe, it, expect } from 'vitest'
import type { ChartResult, Pillar } from '../src/types'
import {
  wuxingRelation,
  palaceOf,
  buildPillarNodes,
  buildFlowArrows,
  hiddenStemsOf,
  relativeOf,
  PALACE_ROLE,
  findGanHe,
  findGanChong,
  findZhiChong,
  LEGEND,
} from '../src/utils/relations'

const WX = ['木', '火', '土', '金', '水'] as const

describe('wuxingRelation', () => {
  it('returns bi for identical elements', () => {
    expect(wuxingRelation('木', '木')).toBe('bi')
    expect(wuxingRelation('金', '金')).toBe('bi')
  })

  it('returns sheng when the first generates the second (木→火→土→金→水→木)', () => {
    expect(wuxingRelation('木', '火')).toBe('sheng')
    expect(wuxingRelation('火', '土')).toBe('sheng')
    expect(wuxingRelation('土', '金')).toBe('sheng')
    expect(wuxingRelation('金', '水')).toBe('sheng')
    expect(wuxingRelation('水', '木')).toBe('sheng')
  })

  it('returns sheng regardless of argument order (undirected)', () => {
    expect(wuxingRelation('火', '木')).toBe('sheng')
    expect(wuxingRelation('木', '水')).toBe('sheng')
  })

  it('returns ke when the first controls the second (木→土→水→火→金→木)', () => {
    expect(wuxingRelation('木', '土')).toBe('ke')
    expect(wuxingRelation('土', '水')).toBe('ke')
    expect(wuxingRelation('水', '火')).toBe('ke')
    expect(wuxingRelation('火', '金')).toBe('ke')
    expect(wuxingRelation('金', '木')).toBe('ke')
  })

  it('returns ke regardless of argument order (undirected)', () => {
    expect(wuxingRelation('土', '木')).toBe('ke')
    expect(wuxingRelation('木', '金')).toBe('ke')
  })

  it('is symmetric over the full 5×5 matrix and covers every pair once', () => {
    for (const a of WX) {
      for (const b of WX) {
        const r = wuxingRelation(a, b)
        expect(['sheng', 'ke', 'bi']).toContain(r)
        expect(wuxingRelation(b, a)).toBe(r)
      }
    }
  })

  it('treats unknown/empty elements as neutral (bi) and never throws', () => {
    expect(wuxingRelation('', '')).toBe('bi')
    expect(wuxingRelation('木', '')).toBe('bi')
    expect(wuxingRelation('', '金')).toBe('bi')
    expect(wuxingRelation('??', '火')).toBe('bi')
  })
})

describe('palaceOf', () => {
  it('maps each pillar to its fixed palace', () => {
    expect(palaceOf('year')).toBe('祖上宫')
    expect(palaceOf('month')).toBe('父母宫')
    expect(palaceOf('day')).toBe('配偶宫')
    expect(palaceOf('time')).toBe('子女宫')
  })
})

const mkPillar = (
  gan: string,
  zhi: string,
  ganWx: string,
  zhiWx: string,
  shishen: string,
  detail?: Pillar['detail'],
): Pillar => ({
  ganzhi: gan + zhi,
  gan,
  zhi,
  gan_wuxing: ganWx,
  zhi_wuxing: zhiWx,
  shishen,
  detail,
})

// 可预测生克关系的四柱：干 木/火/金/金，支 火/火/金/火
const fullPillars = () => ({
  year: mkPillar('庚', '午', '木', '火', '比肩'),
  month: mkPillar('丙', '午', '火', '火', '七杀'),
  day: mkPillar('庚', '申', '金', '金', '日主'),
  time: mkPillar('辛', '巳', '金', '火', '正官'),
})

describe('buildPillarNodes', () => {
  it('builds four pillar nodes with palace, shishen and day-master flag', () => {
    const nodes = buildPillarNodes({ pillars: fullPillars() } as unknown as ChartResult)
    expect(nodes).toHaveLength(4)
    const year = nodes[0]
    expect(year).toMatchObject({
      key: 'year', label: '年柱', gan: '庚', zhi: '午',
      ganWx: '木', zhiWx: '火', ganShishen: '比肩', palace: '祖上宫', present: true, isDayMaster: false,
    })
    expect(nodes.find((n) => n.key === 'day')).toMatchObject({
      palace: '配偶宫', isDayMaster: true, ganShishen: '日主',
    })
    expect(nodes.find((n) => n.key === 'time')).toMatchObject({ palace: '子女宫' })
  })

  it('marks a missing time pillar as not present', () => {
    const nodes = buildPillarNodes({
      pillars: { ...fullPillars(), time: null },
    } as unknown as ChartResult)
    const time = nodes.find((n) => n.key === 'time')
    expect(time).toMatchObject({ present: false, gan: '', zhi: '' })
    expect(time).not.toBeUndefined()
  })
})

describe('buildFlowArrows', () => {
  it('builds gan-layer and zhi-layer arrows between adjacent pillars with correct types', () => {
    const arrows = buildFlowArrows(fullPillars())
    expect(arrows).toHaveLength(6)
    expect(arrows[0]).toEqual({ layer: 'gan', from: 'year', to: 'month', type: 'sheng', fromWx: '木', toWx: '火' })
    expect(arrows[1]).toEqual({ layer: 'gan', from: 'month', to: 'day', type: 'ke', fromWx: '火', toWx: '金' })
    expect(arrows[2]).toEqual({ layer: 'gan', from: 'day', to: 'time', type: 'bi', fromWx: '金', toWx: '金' })
    expect(arrows[3]).toEqual({ layer: 'zhi', from: 'year', to: 'month', type: 'bi', fromWx: '火', toWx: '火' })
    expect(arrows[4]).toEqual({ layer: 'zhi', from: 'month', to: 'day', type: 'ke', fromWx: '火', toWx: '金' })
    expect(arrows[5]).toEqual({ layer: 'zhi', from: 'day', to: 'time', type: 'ke', fromWx: '金', toWx: '火' })
  })

  it('skips arrows involving a missing time pillar', () => {
    const arrows = buildFlowArrows({ ...fullPillars(), time: null })
    expect(arrows).toHaveLength(4)
    expect(arrows.every((a) => a.to !== 'time' && a.from !== 'time')).toBe(true)
  })

  it('skips a layer arrow when either wuxing is empty', () => {
    const pillars = fullPillars()
    pillars.day = mkPillar('庚', '申', '', '金', '日主')
    const arrows = buildFlowArrows(pillars)
    // day 干五行缺失：month→day、day→time 两条 gan 箭头均被跳过，只剩 year→month
    expect(arrows).toHaveLength(4)
    expect(arrows.filter((a) => a.layer === 'gan')).toHaveLength(1)
    expect(arrows.filter((a) => a.layer === 'zhi')).toHaveLength(3)
  })
})

describe('hiddenStemsOf', () => {
  it('derives wuxing for each hidden stem from its gan', () => {
    const pillar = mkPillar('乙', '巳', '木', '火', '日主', {
      gan_shishen: '日主',
      zhi_shishen: '正官',
      cang_gan: [
        { gan: '丙', shishen: '伤官' },
        { gan: '庚', shishen: '正官' },
        { gan: '戊', shishen: '偏财' },
      ],
      xing_yun: '', zi_zuo: '', xun_kong: '', na_yin: '', shen_sha: [],
    })
    expect(hiddenStemsOf(pillar)).toEqual([
      { gan: '丙', wx: '火', shishen: '伤官' },
      { gan: '庚', wx: '金', shishen: '正官' },
      { gan: '戊', wx: '土', shishen: '偏财' },
    ])
  })

  it('returns empty array when no detail or no cang_gan', () => {
    expect(hiddenStemsOf(mkPillar('乙', '巳', '木', '火', '日主'))).toEqual([])
    expect(
      hiddenStemsOf(mkPillar('乙', '巳', '木', '火', '日主', {
        gan_shishen: '日主', zhi_shishen: '', cang_gan: [], xing_yun: '', zi_zuo: '', xun_kong: '', na_yin: '', shen_sha: [],
      })),
    ).toEqual([])
  })
})

describe('LEGEND', () => {
  it('covers the five ten-god groups with relatives and gender notes', () => {
    expect(LEGEND.map((l) => l.group)).toEqual(['印', '官杀', '财', '比劫', '食伤'])
    for (const item of LEGEND) {
      expect(item.gods.length).toBeGreaterThan(0)
      expect(item.relative.length).toBeGreaterThan(0)
    }
    expect(LEGEND[1].genderNote).toContain('男命') // 官杀：男命正官主女儿
    expect(LEGEND[3].genderNote).toBeNull() // 比劫：男/女命通用
  })
})

describe('relativeOf', () => {
  it('maps ten-god names to their relative groups', () => {
    expect(relativeOf('正印')).toContain('父母')
    expect(relativeOf('七杀')).toContain('丈夫')
    expect(relativeOf('正财')).toContain('妻')
    expect(relativeOf('比肩')).toBe('兄弟姐妹')
    expect(relativeOf('伤官')).toBe('子女')
  })

  it('maps 日主 to 本人 and unknown names to null', () => {
    expect(relativeOf('日主')).toBe('本人')
    expect(relativeOf('某某神')).toBeNull()
  })
})

describe('PALACE_ROLE', () => {
  it('maps each palace to its relative role', () => {
    expect(PALACE_ROLE.year).toBe('祖辈/长辈')
    expect(PALACE_ROLE.month).toBe('父母')
    expect(PALACE_ROLE.day).toBe('配偶')
    expect(PALACE_ROLE.time).toBe('子女')
  })
})

describe('天干五合 findGanHe', () => {
  it('finds 甲己合化土 / 乙庚合化金 / 丙辛合化水 / 丁壬合化木 / 戊癸合化火', () => {
    expect(findGanHe(['乙', '庚'])).toEqual([{ a: '乙', b: '庚', hua: '金' }])
    expect(findGanHe(['庚', '乙'])).toEqual([{ a: '庚', b: '乙', hua: '金' }])
    expect(findGanHe(['甲', '己'])[0].hua).toBe('土')
    expect(findGanHe(['丙', '辛'])[0].hua).toBe('水')
    expect(findGanHe(['丁', '壬'])[0].hua).toBe('木')
    expect(findGanHe(['戊', '癸'])[0].hua).toBe('火')
  })

  it('finds two disjoint pairs among four gans', () => {
    const r = findGanHe(['甲', '乙', '己', '庚'])
    expect(r).toHaveLength(2)
    expect(r.some((p) => p.a === '甲' && p.b === '己')).toBe(true)
    expect(r.some((p) => p.a === '乙' && p.b === '庚')).toBe(true)
  })

  it('reports each pairing once even with duplicate gans and returns empty for none', () => {
    expect(findGanHe(['乙', '乙', '庚'])).toEqual([{ a: '乙', b: '庚', hua: '金' }])
    expect(findGanHe(['乙', '丙'])).toEqual([])
  })
})

describe('天干相冲 findGanChong', () => {
  it('finds 甲庚 / 乙辛 / 丙壬 / 丁癸', () => {
    expect(findGanChong(['甲', '庚'])).toEqual([{ a: '甲', b: '庚' }])
    expect(findGanChong(['辛', '乙'])).toEqual([{ a: '辛', b: '乙' }])
    expect(findGanChong(['丙', '壬'])[0]).toEqual({ a: '丙', b: '壬' })
    expect(findGanChong(['丁', '癸'])[0]).toEqual({ a: '丁', b: '癸' })
  })

  it('returns empty when none (戊己无冲)', () => {
    expect(findGanChong(['甲', '乙'])).toEqual([])
    expect(findGanChong(['戊', '己'])).toEqual([])
  })
})

describe('地支六冲 findZhiChong', () => {
  it('finds 子午 / 丑未 / 寅申 / 卯酉 / 辰戌 / 巳亥', () => {
    expect(findZhiChong(['巳', '亥'])).toEqual([{ a: '巳', b: '亥' }])
    expect(findZhiChong(['子', '午'])[0]).toEqual({ a: '子', b: '午' })
    expect(findZhiChong(['丑', '未'])[0]).toEqual({ a: '丑', b: '未' })
    expect(findZhiChong(['寅', '申'])[0]).toEqual({ a: '寅', b: '申' })
    expect(findZhiChong(['卯', '酉'])[0]).toEqual({ a: '卯', b: '酉' })
    expect(findZhiChong(['辰', '戌'])[0]).toEqual({ a: '辰', b: '戌' })
  })

  it('returns empty when none and dedups duplicate 巳', () => {
    expect(findZhiChong(['巳', '午'])).toEqual([])
    expect(findZhiChong(['巳', '亥', '酉', '巳'])).toEqual([{ a: '巳', b: '亥' }])
  })
})
