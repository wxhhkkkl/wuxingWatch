/**
 * 命盘图派生逻辑：五行流通关系、宫位映射、四柱节点/藏干视图数据、十神↔六亲图例。
 * 全部为纯函数，复用既有 ChartResult 数据，无后端依赖。
 */

import type { ChartResult, Pillar } from '../types'
import { GAN_WUXING } from './wuxing'

export type PillarKey = 'year' | 'month' | 'day' | 'time'
export type FlowType = 'sheng' | 'ke' | 'bi'

// 五行相生：木→火→土→金→水→木（与 backend constants.py 一致）
const SHENG: Record<string, string> = { 木: '火', 火: '土', 土: '金', 金: '水', 水: '木' }
// 五行相克：木→土→水→火→金→木
const KE: Record<string, string> = { 木: '土', 土: '水', 水: '火', 火: '金', 金: '木' }

/**
 * 判定两个五行的无向关系：相生/相克/比和。
 * 关系为元素对本身的属性，不依赖方向；未知/空五行按中性（bi）处理、不参与生克。
 */
export function wuxingRelation(a: string, b: string): FlowType {
  if (a === b) return 'bi'
  if (SHENG[a] === b || SHENG[b] === a) return 'sheng'
  if (KE[a] === b || KE[b] === a) return 'ke'
  return 'bi'
}

const PALACE: Record<PillarKey, string> = {
  year: '祖上宫',
  month: '父母宫',
  day: '配偶宫',
  time: '子女宫',
}

/** 四柱固定宫位：年=祖上宫、月=父母宫、日支=配偶宫、时=子女宫。 */
export function palaceOf(key: PillarKey): string {
  return PALACE[key]
}

export interface HiddenStemNode {
  gan: string
  wx: string
  shishen: string
}

export interface PillarNode {
  key: PillarKey
  label: string
  gan: string
  zhi: string
  ganWx: string
  zhiWx: string
  ganShishen: string
  palace: string
  hiddenStems: HiddenStemNode[]
  isDayMaster: boolean
  present: boolean
}

const LABEL: Record<PillarKey, string> = {
  year: '年柱',
  month: '月柱',
  day: '日柱',
  time: '时柱',
}

const PILLAR_KEYS: PillarKey[] = ['year', 'month', 'day', 'time']

/** 由藏干天干推导其五行。 */
export function hiddenStemsOf(pillar: Pillar): HiddenStemNode[] {
  return (pillar.detail?.cang_gan ?? []).map((c) => ({
    gan: c.gan,
    wx: GAN_WUXING[c.gan] ?? '',
    shishen: c.shishen,
  }))
}

/** 聚合四柱节点（主图数据源）。缺失的柱 present=false，藏干随 detail 折叠展示。 */
export function buildPillarNodes(result: ChartResult): PillarNode[] {
  return PILLAR_KEYS.map((key) => {
    const p = result.pillars[key]
    if (!p) {
      return {
        key, label: LABEL[key], gan: '', zhi: '',
        ganWx: '', zhiWx: '', ganShishen: '', palace: palaceOf(key),
        hiddenStems: [], isDayMaster: key === 'day', present: false,
      }
    }
    return {
      key,
      label: LABEL[key],
      gan: p.gan,
      zhi: p.zhi,
      ganWx: p.gan_wuxing,
      zhiWx: p.zhi_wuxing,
      ganShishen: p.shishen,
      palace: palaceOf(key),
      hiddenStems: hiddenStemsOf(p),
      isDayMaster: key === 'day',
      present: true,
    }
  })
}

export interface FlowArrow {
  layer: 'gan' | 'zhi'
  from: PillarKey
  to: PillarKey
  type: FlowType
  fromWx: string
  toWx: string
}

const ADJACENT: [PillarKey, PillarKey][] = [
  ['year', 'month'],
  ['month', 'day'],
  ['day', 'time'],
]

/**
 * 生成干支双层流通箭头：天干层、地支层各自连接相邻柱（年→月→日→时）。
 * 顺序按层分组（先天干层、后地支层）；任一端五行缺失或柱缺失时跳过该箭头。
 */
export function buildFlowArrows(pillars: Record<PillarKey, Pillar | null>): FlowArrow[] {
  const arrows: FlowArrow[] = []
  for (const layer of ['gan', 'zhi'] as const) {
    for (const [from, to] of ADJACENT) {
      const f = pillars[from]
      const t = pillars[to]
      if (!f || !t) continue
      const fromWx = layer === 'gan' ? f.gan_wuxing : f.zhi_wuxing
      const toWx = layer === 'gan' ? t.gan_wuxing : t.zhi_wuxing
      if (!fromWx || !toWx) continue
      arrows.push({ layer, from, to, type: wuxingRelation(fromWx, toWx), fromWx, toWx })
    }
  }
  return arrows
}

export interface LegendItem {
  group: string
  gods: string[]
  relative: string
  genderNote: string | null
}

/** 十神 ↔ 六亲 对照图例（含男/女命性别差异备注）。 */
export const LEGEND: LegendItem[] = [
  { group: '印', gods: ['正印', '偏印'], relative: '父母（偏印亦主母）', genderNote: '男/女命通用' },
  { group: '官杀', gods: ['正官', '七杀'], relative: '丈夫（女命）/ 上级', genderNote: '男命正官主女儿、七杀主儿子' },
  { group: '财', gods: ['正财', '偏财'], relative: '妻（男命）/ 父亲', genderNote: '女命正财主父亲' },
  { group: '比劫', gods: ['比肩', '劫财'], relative: '兄弟姐妹', genderNote: null },
  { group: '食伤', gods: ['食神', '伤官'], relative: '子女', genderNote: '女命食神主女儿、伤官主儿子' },
]

/** 宫位对应的六亲角色（宫位 tab 说明）。 */
export const PALACE_ROLE: Record<PillarKey, string> = {
  year: '祖辈/长辈',
  month: '父母',
  day: '配偶',
  time: '子女',
}

/** 给定十神名，返回其对应六亲说明；日主→本人，未命中→null。 */
export function relativeOf(tenGod: string): string | null {
  if (tenGod === '日主') return '本人'
  return LEGEND.find((l) => l.gods.includes(tenGod))?.relative ?? null
}

// 天干五合：甲己合化土 / 乙庚合化金 / 丙辛合化水 / 丁壬合化木 / 戊癸合化火
const GAN_HE: Record<string, string> = {
  甲: '己', 己: '甲', 乙: '庚', 庚: '乙', 丙: '辛', 辛: '丙',
  丁: '壬', 壬: '丁', 戊: '癸', 癸: '戊',
}
const GAN_HE_HUA: Record<string, string> = {
  甲: '土', 己: '土', 乙: '金', 庚: '金', 丙: '水', 辛: '水',
  丁: '木', 壬: '木', 戊: '火', 癸: '火',
}
// 天干相冲：甲庚 / 乙辛 / 丙壬 / 丁癸（戊己无冲）
const GAN_CHONG: Record<string, string> = {
  甲: '庚', 庚: '甲', 乙: '辛', 辛: '乙', 丙: '壬', 壬: '丙', 丁: '癸', 癸: '丁',
}
// 地支六冲：子午 / 丑未 / 寅申 / 卯酉 / 辰戌 / 巳亥
const ZHI_CHONG: Record<string, string> = {
  子: '午', 午: '子', 丑: '未', 未: '丑', 寅: '申', 申: '寅',
  卯: '酉', 酉: '卯', 辰: '戌', 戌: '辰', 巳: '亥', 亥: '巳',
}

export interface GanHePair {
  a: string
  b: string
  hua: string
}

export interface ChongPair {
  a: string
  b: string
}

/** 在一组天干中找所有五合对（每字至多配对一次，去重）。 */
export function findGanHe(gans: string[]): GanHePair[] {
  const out: GanHePair[] = []
  const used = new Set<number>()
  for (let i = 0; i < gans.length; i++) {
    if (used.has(i)) continue
    for (let j = i + 1; j < gans.length; j++) {
      if (used.has(j)) continue
      if (GAN_HE[gans[i]] === gans[j]) {
        out.push({ a: gans[i], b: gans[j], hua: GAN_HE_HUA[gans[i]] })
        used.add(i)
        used.add(j)
        break
      }
    }
  }
  return out
}

/** 在一组天干中找所有相冲对（每字至多配对一次）。 */
export function findGanChong(gans: string[]): ChongPair[] {
  const out: ChongPair[] = []
  const used = new Set<number>()
  for (let i = 0; i < gans.length; i++) {
    if (used.has(i)) continue
    for (let j = i + 1; j < gans.length; j++) {
      if (used.has(j)) continue
      if (GAN_CHONG[gans[i]] === gans[j]) {
        out.push({ a: gans[i], b: gans[j] })
        used.add(i)
        used.add(j)
        break
      }
    }
  }
  return out
}

/** 在一组地支中找所有六冲对（每字至多配对一次）。 */
export function findZhiChong(zhis: string[]): ChongPair[] {
  const out: ChongPair[] = []
  const used = new Set<number>()
  for (let i = 0; i < zhis.length; i++) {
    if (used.has(i)) continue
    for (let j = i + 1; j < zhis.length; j++) {
      if (used.has(j)) continue
      if (ZHI_CHONG[zhis[i]] === zhis[j]) {
        out.push({ a: zhis[i], b: zhis[j] })
        used.add(i)
        used.add(j)
        break
      }
    }
  }
  return out
}

// ============================================================================
// 关系图（参考"问真/栏江"连线式）：干支/藏干 节点 + 合冲刑破害克 连线
// ============================================================================

export interface RelCol {
  id: string
  label: string
  gan: string
  ganWx: string
  zhi: string
  zhiWx: string
  canggan: { gan: string; wx: string }[]
}

export interface RelNode {
  id: string
  layer: 'gan' | 'zhi' | 'zang'
  colId: string
  char: string
  wx: string
}

export type RelType =
  | '生' | '克' | '合' | '合化' | '冲'        // 天干关系
  | '三会' | '三合' | '六合' | '相冲' | '刑' | '害' | '破'  // 地支关系

/** 可筛选的关系类型（天干/地支 分层的全部关系类型）。 */
export const REL_TYPES: RelType[] = ['生', '克', '合', '合化', '冲', '三会', '三合', '六合', '相冲', '刑', '害', '破']

export interface RelPair {
  a: string
  b: string
  type: RelType
  detail: string
  aChar: string
  bChar: string
}

// 地支六破：子酉/卯午/辰丑/戌未/寅亥/巳申
const ZHI_PO = new Set(['子酉', '酉子', '卯午', '午卯', '辰丑', '丑辰', '戌未', '未戌', '寅亥', '亥寅', '巳申', '申巳'])
// 地支六害：子未/丑午/寅巳/卯辰/申亥/酉戌
const ZHI_HAI = new Set(['子未', '未子', '丑午', '午丑', '寅巳', '巳寅', '卯辰', '辰卯', '申亥', '亥申', '酉戌', '戌酉'])
// 地支六合化气：子丑土/寅亥木/卯戌火/辰酉金/巳申水/午未土
const LIU_HE: Record<string, { with: string; hua: string }> = {
  子: { with: '丑', hua: '土' }, 丑: { with: '子', hua: '土' },
  寅: { with: '亥', hua: '木' }, 亥: { with: '寅', hua: '木' },
  卯: { with: '戌', hua: '火' }, 戌: { with: '卯', hua: '火' },
  辰: { with: '酉', hua: '金' }, 酉: { with: '辰', hua: '金' },
  巳: { with: '申', hua: '水' }, 申: { with: '巳', hua: '水' },
  午: { with: '未', hua: '土' }, 未: { with: '午', hua: '土' },
}
// 三刑：寅巳申 / 丑戌未；普通刑：子卯；自刑：辰午酉亥（同支）
const XING_SAN = [new Set(['寅', '巳', '申']), new Set(['丑', '戌', '未'])]
const XING_ZI_MAO_SET = new Set(['子卯', '卯子'])
const ZI_XING = new Set(['辰', '午', '酉', '亥'])
// 三合：申子辰水/寅午戌火/巳酉丑金/亥卯未木
const SAN_HE: { branches: Set<string>; hua: string }[] = [
  { branches: new Set(['申', '子', '辰']), hua: '水' },
  { branches: new Set(['寅', '午', '戌']), hua: '火' },
  { branches: new Set(['巳', '酉', '丑']), hua: '金' },
  { branches: new Set(['亥', '卯', '未']), hua: '木' },
]
// 三会：寅卯辰木/巳午未火/申酉戌金/亥子丑水
const SAN_HUI: { branches: Set<string>; hua: string }[] = [
  { branches: new Set(['寅', '卯', '辰']), hua: '木' },
  { branches: new Set(['巳', '午', '未']), hua: '火' },
  { branches: new Set(['申', '酉', '戌']), hua: '金' },
  { branches: new Set(['亥', '子', '丑']), hua: '水' },
]

/**
 * 由关系列构建全部关系连线（**干↔干 / 支↔支 分层专属**，不跨层、不含藏干）。
 * - 天干层：相生 / 相克 / 五合 / 合化 / 相冲
 * - 地支层：三会 / 三合 / 六合 / 相冲 / 相刑（子卯/寅巳申/丑戌未/辰午酉亥自刑）/ 六害 / 相破
 * @param opts.excludeColIds 排除的列（如不关联大运/流年时传 ['dayun','liunian']），成局亦只按剩余列判定
 */
export function buildRelationPairs(cols: RelCol[], opts?: { excludeColIds?: string[] }): RelPair[] {
  const exclude = new Set(opts?.excludeColIds ?? [])
  const active = cols.filter((c) => !exclude.has(c.id))
  const ganNodes: RelNode[] = []
  const zhiNodes: RelNode[] = []
  for (const c of active) {
    ganNodes.push({ id: `gan-${c.id}`, layer: 'gan', colId: c.id, char: c.gan, wx: c.ganWx })
    zhiNodes.push({ id: `zhi-${c.id}`, layer: 'zhi', colId: c.id, char: c.zhi, wx: c.zhiWx })
  }

  const pairs: RelPair[] = []
  const push = (a: RelNode, b: RelNode, type: RelType, detail: string) =>
    pairs.push({ a: a.id, b: b.id, type, detail, aChar: a.char, bChar: b.char })

  // 天干层：相生 / 相克 / 五合 / 合化 / 相冲
  for (let i = 0; i < ganNodes.length; i++) {
    for (let j = i + 1; j < ganNodes.length; j++) {
      const a = ganNodes[i]
      const b = ganNodes[j]
      if (GAN_HE[a.char] === b.char) {
        push(a, b, '合', `${a.char}${b.char}合`)
        push(a, b, '合化', `${a.char}${b.char}合化${GAN_HE_HUA[a.char]}`)
      }
      if (GAN_CHONG[a.char] === b.char) {
        push(a, b, '冲', `${a.char}${b.char}相冲`)
      }
      if (a.wx && b.wx) {
        if (SHENG[a.wx] === b.wx || SHENG[b.wx] === a.wx) {
          push(a, b, '生', `${a.char}${b.char}相生`)
        } else if (KE[a.wx] === b.wx || KE[b.wx] === a.wx) {
          push(a, b, '克', `${a.char}${b.char}相克`)
        }
      }
    }
  }

  // 地支层：六合 / 相冲 / 相刑 / 六破 / 六害
  for (let i = 0; i < zhiNodes.length; i++) {
    for (let j = i + 1; j < zhiNodes.length; j++) {
      const a = zhiNodes[i]
      const b = zhiNodes[j]
      const ac = a.char
      const bc = b.char
      if (LIU_HE[ac]?.with === bc) push(a, b, '六合', `${ac}${bc}合${LIU_HE[ac].hua}`)
      if (ZHI_CHONG[ac] === bc) push(a, b, '相冲', `${ac}${bc}相冲`)
      if (XING_ZI_MAO_SET.has(ac + bc)) push(a, b, '刑', `${ac}${bc}相刑`)
      if (XING_SAN.some((g) => g.has(ac) && g.has(bc))) push(a, b, '刑', `${ac}${bc}相刑`)
      if (ac === bc && ZI_XING.has(ac)) push(a, b, '刑', `${ac}${bc}自刑`)
      if (ZHI_PO.has(ac + bc)) push(a, b, '破', `${ac}${bc}相破`)
      if (ZHI_HAI.has(ac + bc)) push(a, b, '害', `${ac}${bc}相害`)
    }
  }

  // 地支成局：三合 / 三会（三支齐备，每组只报一次，锚定到其中一支）
  const zhiChars = zhiNodes.map((n) => n.char)
  const groups = new Set<string>()
  const report = (set: Set<string>, hua: string, type: RelType) => {
    const hit = [...set].every((b) => zhiChars.includes(b))
    if (!hit) return
    const sorted = [...set].sort().join('')
    if (groups.has(type + sorted)) return
    groups.add(type + sorted)
    const anchor = zhiNodes.find((n) => set.has(n.char))!
    const label = [...set].join('')
    pairs.push({
      a: anchor.id, b: anchor.id, type,
      detail: `${label}${type === '三合' ? '合' : '会'}${hua}`,
      aChar: label, bChar: '',
    })
  }
  for (const g of SAN_HE) report(g.branches, g.hua, '三合')
  for (const g of SAN_HUI) report(g.branches, g.hua, '三会')

  return pairs
}
