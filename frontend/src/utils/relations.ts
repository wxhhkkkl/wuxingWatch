/**
 * 命盘图派生逻辑：五行流通关系、宫位映射、四柱节点/藏干视图数据、十神↔六亲图例。
 * 全部为纯函数，复用既有 ChartResult 数据，无后端依赖。
 */

import type { ChartResult, Pillar } from '../types'
import { GAN_WUXING, ZHI_WUXING } from './wuxing'

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

/** 条件判定输出（对拍口径：与后端 judge_relations 一致）。 */
export interface Judgment {
  a: string
  b: string
  layer: 'stem' | 'branch'
  type: string // 五合|冲|生|克 | 六合|相冲|半三合|三合|三会|三刑|刑|害|破
  detail?: string
  reason?: string
  positions?: string[]
  involves?: string // 'dayun' | 'liunian'
  aColId?: string
  bColId?: string
  members?: string[]
  memberColIds?: string[]
}

// ---- 藏干度数表（algorithm-reference §1.1；成立条件判定专用，不含通根递减）----
const HIDDEN_FIXED: Record<string, [string, number][]> = {
  子: [['癸', 5]], 卯: [['乙', 5]], 酉: [['辛', 5]],
  午: [['丁', 4], ['己', 2]], 亥: [['壬', 4], ['甲', 2]],
  寅: [['甲', 3], ['丙', 2], ['戊', 1]],
  巳: [['丙', 3], ['庚', 2], ['戊', 1]],
  申: [['庚', 3], ['壬', 2], ['戊', 1]],
}
const MUKU: Record<string, Record<string, [string, number][]>> = {
  丑: { 亥子: [['癸', 3], ['辛', 2], ['己', 0]], 丑: [['癸', 2], ['辛', 2], ['己', 3]], 申酉: [['癸', 2], ['辛', 2], ['己', 2]], 其他: [['癸', 1], ['辛', 2], ['己', 3]] },
  辰: { 亥子: [['癸', 3], ['乙', 2], ['戊', 0]], 申酉: [['癸', 2], ['乙', 2], ['戊', 2]], 丑: [['癸', 2], ['戊', 3], ['乙', 2]], 其他: [['癸', 1], ['乙', 2], ['戊', 3]] },
  未: { 巳午未: [['丁', 4], ['己', 2]], 申酉: [['丁', 2], ['己', 3], ['乙', 1]], 戌: [['丁', 3], ['己', 3]], 亥子丑: [['丁', 2], ['己', 3], ['乙', 1]], 辰: [['己', 3], ['乙', 2], ['丁', 1]], 其他: [['丁', 2], ['己', 3], ['乙', 1]] },
  戌: { 巳午未: [['丁', 4], ['戊', 2]], 申酉: [['丁', 2], ['戊', 2], ['辛', 2]], 戌: [['丁', 3], ['戊', 3]], 亥子丑: [['丁', 1], ['戊', 3], ['辛', 2]], 辰: [['辛', 2], ['丁', 1], ['戊', 3]], 其他: [['丁', 2], ['戊', 3], ['辛', 1]] },
}

function monthGroup(monthZhi: string): string {
  if ('亥子'.includes(monthZhi)) return '亥子'
  if ('巳午未'.includes(monthZhi)) return '巳午未'
  if ('申酉'.includes(monthZhi)) return '申酉'
  if (['丑', '戌', '辰'].includes(monthZhi)) return monthZhi
  return '其他'
}

function hiddenDegrees(zhi: string, monthZhi: string, zhiCount: Record<string, number>): [string, number][] {
  if (HIDDEN_FIXED[zhi]) return HIDDEN_FIXED[zhi]
  if ((zhi === '丑' || zhi === '辰') && '亥子'.includes(monthZhi) && (zhiCount[zhi] ?? 0) >= 3) {
    return [['癸', 2], [zhi === '丑' ? '辛' : '乙', 2], [zhi === '丑' ? '己' : '戊', 2]]
  }
  let grp = monthGroup(monthZhi)
  if ((zhi === '未' || zhi === '戌') && '亥子丑'.includes(monthZhi)) grp = '亥子丑'
  return MUKU[zhi][grp] ?? MUKU[zhi]['其他']
}

// ---- 月令状态（§1.2 + 特殊规则固定部分）----
const SHENG_INV: Record<string, string> = { 火: '木', 土: '火', 金: '土', 水: '金', 木: '水' }
const KE_INV: Record<string, string> = { 土: '木', 水: '土', 火: '水', 金: '火', 木: '金' }
const MONTH_STATE_OVERRIDE: Record<string, string> = { 辰木: '余气', 辰水: '死', 未火: '余气', 未金: '死', 丑水: '余气' }

function elementState(wx: string, el: string): string {
  if (wx === el) return '旺'
  if (SHENG[el] === wx) return '相'
  if (SHENG_INV[el] === wx) return '休'
  if (KE_INV[el] === wx) return '囚'
  return '死'
}

function monthState(wx: string, monthZhi: string): string {
  const o = MONTH_STATE_OVERRIDE[monthZhi + wx]
  if (o) return o
  return elementState(wx, ZHI_WUXING[monthZhi])
}

// ---- 关系表 ----
const PAIR_ORDER = '甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥'

function pairKey(a: string, b: string): string {
  return [a, b].sort((x, y) => PAIR_ORDER.indexOf(x) - PAIR_ORDER.indexOf(y)).join('')
}

// 对表键一律经 pairKey 规范化（避免书写顺序与规范序不一致）
const _pairMap = <T>(entries: [string, T][]): Record<string, T> =>
  Object.fromEntries(entries.map(([k, v]) => [pairKey(k[0], k[1]), v]))
const _pairSet = (keys: string[]) => new Set(keys.map((k) => pairKey(k[0], k[1])))

const GAN_HE_SET = _pairSet(['甲己', '乙庚', '丙辛', '丁壬', '戊癸'])
const GAN_HE_HUA_MAP: Record<string, string> = _pairMap([['甲己', '土'], ['乙庚', '金'], ['丙辛', '水'], ['丁壬', '木'], ['戊癸', '火']])
const GAN_ORDER = '甲乙丙丁戊己庚辛壬癸'
const LIU_HE_MAP: Record<string, string[]> = _pairMap([['子丑', ['水', '土']], ['寅亥', ['木']], ['卯戌', ['火']], ['辰酉', ['金']], ['巳申', ['水']], ['午未', ['火', '土']]])
const ZHI_HAI_SET = _pairSet(['子未', '丑午', '寅巳', '卯辰', '申亥', '酉戌'])
const ZHI_PO_SET = _pairSet(['子酉', '午卯', '辰丑', '戌未', '寅亥', '巳申'])
const XING_PAIR_SET = _pairSet(['子卯', '寅巳', '巳申', '寅申', '丑戌', '未戌', '丑未'])
const ZI_XING_SET = new Set(['辰', '午', '酉', '亥'])
const BAN_SANHE_MAP: Record<string, string> = _pairMap([['亥卯', '木'], ['卯未', '木'], ['寅午', '火'], ['午戌', '火'], ['巳酉', '金'], ['酉丑', '金'], ['申子', '水'], ['子辰', '水']])
const SAN_HE_MAP: Record<string, string> = { 亥卯未: '木', 寅午戌: '火', 巳酉丑: '金', 申子辰: '水' }
const SAN_HUI_MAP: Record<string, string> = { 寅卯辰: '木', 巳午未: '火', 申酉戌: '金', 亥子丑: '水' }
const SAN_XING_SETS = ['寅巳申', '丑未戌']
const JU_KEYS = new Set(['year', 'month', 'day', 'time'])
const POS_LABEL: Record<string, string> = { year: '年', month: '月', day: '日', time: '时', dayun: '大运', liunian: '流年' }


interface JCol {
  idx: number
  id: string
  gan: string
  zhi: string
  hidden: Record<string, number>
}

/** 轻量五行度数（无通根递减）：仅供成立条件的太旺/透出阈值判定（裁定：阈值场景与引擎精确版一致）。 */
function wxDegreesLite(cols: JCol[]): Record<string, number> {
  const deg: Record<string, number> = { 木: 0, 火: 0, 土: 0, 金: 0, 水: 0 }
  for (const c of cols) {
    if (c.gan) deg[GAN_WUXING[c.gan]] += 1
    for (const [g, d] of Object.entries(c.hidden)) deg[GAN_WUXING[g]] += d
  }
  return deg
}

function stemRelation(g1: string, g2: string): { type: string; detail: string } | null {
  const pk = pairKey(g1, g2)
  if (GAN_HE_SET.has(pk)) return { type: '五合', detail: '' }
  if (GAN_CHONG[g1] === g2) {
    return { type: '冲', detail: `${[g1, g2].sort((x, y) => GAN_ORDER.indexOf(x) - GAN_ORDER.indexOf(y)).join('')}相冲` }
  }
  const w1 = GAN_WUXING[g1]
  const w2 = GAN_WUXING[g2]
  if (w1 === w2) return null // 比和不报
  if (SHENG[w1] === w2) return { type: '生', detail: `${g1}生${g2}` }
  if (SHENG[w2] === w1) return { type: '生', detail: `${g2}生${g1}` }
  if (KE[w1] === w2) return { type: '克', detail: `${g1}克${g2}` }
  return { type: '克', detail: `${g2}克${g1}` }
}

/** 同一对支存在多个字面关系时按 §9 只保留最高优先级：生地半三合 > 冲 > 六合 > 墓地半三合 > 刑 > 害 > 破 */
function branchPairTypes(z1: string, z2: string): string[] {
  const pk = pairKey(z1, z2)
  const out: string[] = []
  if (LIU_HE_MAP[pk]) out.push('六合')
  if (ZHI_CHONG[z1] === z2) out.push('相冲')
  if (BAN_SANHE_MAP[pk]) out.push('半三合')
  if (XING_PAIR_SET.has(pk)) out.push('刑')
  if (z1 === z2 && ZI_XING_SET.has(z1)) out.push('刑')
  if (ZHI_HAI_SET.has(pk)) out.push('害')
  if (ZHI_PO_SET.has(pk)) out.push('破')
  if (out.length <= 1) return out
  const shengDi = _pairSet(['亥卯', '寅午', '申子'])
  const rank = (t: string): number => {
    if (t === '半三合') return shengDi.has(pk) ? 0 : 3
    const m: Record<string, number> = { 相冲: 1, 六合: 2, 刑: 4, 害: 5, 破: 6 }
    return m[t] ?? 7
  }
  out.sort((x, y) => rank(x) - rank(y))
  return [out[0]]
}

function stemHeHuaOk(c1: JCol, c2: JCol, hua: string, cols: JCol[], monthZhi: string): boolean {
  if (!['旺', '相'].includes(monthState(hua, monthZhi))) return false
  const zuozhi = new Set([ZHI_WUXING[c1.zhi], ZHI_WUXING[c2.zhi]])
  const pk = pairKey(c1.gan, c2.gan)
  let weak: string
  if (pk === '甲己') {
    if (!zuozhi.has('土')) return false
    weak = '甲'
    const deg = wxDegreesLite(cols)
    if (deg['水'] === 0 && !cols.some((c) => ['辰', '丑'].includes(c.zhi))) return false // 过燥
  } else if (pk === '乙庚') {
    if (!zuozhi.has('金')) return false
    weak = '乙'
  } else if (pk === '丙辛') {
    if (!zuozhi.has('水')) return false
    weak = '丙'
  } else if (pk === '丁壬') {
    // 修复（2026-08-17）：§3 条件② 坐支一支为木、另一支为水或木（与后端 wangdu.py 对齐）
    const z1 = c1.zhi ? ZHI_WUXING[c1.zhi] : null
    const z2 = c2.zhi ? ZHI_WUXING[c2.zhi] : null
    if (!z1 || !z2 || !((z1 === '木' && (z2 === '水' || z2 === '木')) || (z2 === '木' && (z1 === '水' || z1 === '木')))) return false
    weak = '丁'
  } else {
    if (!zuozhi.has('火')) return false
    weak = '癸'
  }
  // 弱方不能独立（裁定 C17：无单支度数 ≥3 的同类根）
  const weakWx = GAN_WUXING[weak]
  for (const c of cols) {
    for (const [g, d] of Object.entries(c.hidden)) {
      if (GAN_WUXING[g] === weakWx && d >= 3) return false
    }
  }
  return true
}

function liuheVerdict(c1: JCol, c2: JCol, cols: JCol[], monthZhi: string): { detail: string; hua: string | null } {
  const pk = pairKey(c1.zhi, c2.zhi)
  const tou = (wx: string) => cols.some((c) => c.gan && GAN_WUXING[c.gan] === wx)
  const deg = wxDegreesLite(cols)
  const taiwang = (wx: string) => deg[wx] >= 26
  if (pk === '子丑') {
    if (['旺', '相'].includes(monthState('水', monthZhi)) && monthZhi !== '戌' && (tou('水') || taiwang('水')))
      return { detail: '合化水', hua: '水' }
    if (['旺', '相'].includes(monthState('土', monthZhi)) && monthZhi !== '子' && (tou('土') || taiwang('土')))
      return { detail: '合化土', hua: '土' }
    if ('亥子丑申酉'.includes(monthZhi)) return { detail: '相生（不化）', hua: null }
    return { detail: '合绊', hua: null }
  }
  if (pk === '寅亥') {
    if ((['旺', '相'].includes(monthState('木', monthZhi)) || taiwang('木')) && (tou('木') || taiwang('木')))
      return { detail: '合化木', hua: '木' }
    return { detail: '相生（不化）', hua: null }
  }
  if (pk === '卯戌') {
    if ((['旺', '相'].includes(monthState('火', monthZhi)) || taiwang('火')) && (tou('火') || taiwang('火')) && monthZhi !== '卯')
      return { detail: '合化火', hua: '火' }
    return { detail: '合绊', hua: null }
  }
  if (pk === '辰酉') {
    if (['旺', '相'].includes(monthState('金', monthZhi)) && (tou('金') || taiwang('金')) && monthZhi !== '辰')
      return { detail: '合化金', hua: '金' }
    return { detail: '相生（不化）', hua: null }
  }
  if (pk === '巳申') {
    if (['旺', '相'].includes(monthState('水', monthZhi)) && (tou('水') || taiwang('水')) && !'巳午未戌'.includes(monthZhi)) {
      // 修复（2026-08-17）：§4 条件④ 化神水不受重克（土太旺以上）且旺度 ≥8（与后端对齐）
      if (deg['土'] < 26 && deg['水'] >= 8) return { detail: '合化水', hua: '水' }
    }
    return { detail: '合绊', hua: null }
  }
  // 午未
  if (['旺', '相'].includes(monthState('火', monthZhi)) && (tou('火') || taiwang('火')) && monthZhi !== '亥')
    return { detail: '合化火', hua: '火' }
  if (['旺', '相'].includes(monthState('土', monthZhi)) && (tou('土') || taiwang('土')) && monthZhi !== '寅')
    return { detail: '合化土', hua: '土' } // 裁定 C2（用户补充口径）
  if ('寅卯巳午未戌'.includes(monthZhi)) return { detail: '互助', hua: null }
  if ('亥子丑辰'.includes(monthZhi)) return { detail: '合绊', hua: null }
  return deg['水'] > deg['火'] ? { detail: '合绊', hua: null } : { detail: '互助', hua: null }
}

function banheVerdict(c1: JCol, c2: JCol, cols: JCol[], monthZhi: string): { detail: string; hua: string | null } {
  const pk = pairKey(c1.zhi, c2.zhi)
  const wx = BAN_SANHE_MAP[pk]
  if (pk === '巳酉') return { detail: '合绊', hua: null } // 不论合化均论合绊
  const tou = cols.some((c) => c.gan && GAN_WUXING[c.gan] === wx)
  const taiwang = wxDegreesLite(cols)[wx] >= 26
  let ok = (['旺', '相'].includes(monthState(wx, monthZhi)) || taiwang) && (tou || taiwang)
  if (pk === '卯未' && monthZhi === '未') ok = false
  if (pk === pairKey('酉', '丑') && monthZhi === '丑') ok = false
  if (pk === '子辰' && monthZhi === '辰') ok = false
  if (pk === '午戌' && '亥子丑'.includes(monthZhi)) ok = false
  if (ok) return { detail: `合化${wx}`, hua: wx }
  if (_pairSet(['亥卯', '酉丑', '申子']).has(pk)) return { detail: '相生（不化）', hua: null }
  return { detail: '合绊', hua: null }
}

/** 两支自刑逢冲或逢"非加强化神之合"则不成（§7）。与后端 wangdu.py _zixing_blocked 对齐。 */
function zixingBlocked(z: string, cols: JCol[]): boolean {
  const wx = ZHI_WUXING[z]
  const zIdxs = cols.map((c, i) => (c.zhi === z ? i : -1)).filter((i) => i >= 0)
  for (let i = 0; i < cols.length; i++) {
    const c = cols[i]
    if (!JU_KEYS.has(c.id) || c.zhi === z) continue
    if (!zIdxs.some((j) => Math.abs(i - j) === 1)) continue
    if (ZHI_CHONG[z] === c.zhi) return true
    const pk = pairKey(z, c.zhi)
    if (LIU_HE_MAP[pk] && !LIU_HE_MAP[pk].includes(wx)) return true
    if (BAN_SANHE_MAP[pk] && BAN_SANHE_MAP[pk] !== wx) return true
    for (const [grp, gwx] of Object.entries(SAN_HE_MAP)) {
      if (grp.includes(z) && grp.includes(c.zhi) && gwx !== wx) return true
    }
    for (const [grp, gwx] of Object.entries(SAN_HUI_MAP)) {
      if (grp.includes(z) && grp.includes(c.zhi) && gwx !== wx) return true
    }
  }
  return false
}

/** 辰午酉亥自刑成立条件（§7）。与后端 wangdu.py _zixing_ok 对齐。 */
function zixingOk(z: string, cols: JCol[], monthZhi: string, zset: Record<string, number>): boolean {
  const wx = ZHI_WUXING[z]
  const deg = wxDegreesLite(cols)
  const n = zset[z] ?? 0
  const tou = cols.some((c) => c.gan && GAN_WUXING[c.gan] === wx)
  if (!(tou || deg[wx] >= 26)) return false        // 化神不透且未太旺 → 不成
  if (n >= 4) return true                          // 4支以上：无需月令旺地
  if (!['旺', '相'].includes(monthState(wx, monthZhi))) return false // 两支/三支：须月令化神旺相
  if (n >= 3) return true                          // 三支：干透即可
  return !zixingBlocked(z, cols)                   // 两支：不逢合/冲
}

function xingVerdict(c1: JCol, c2: JCol, cols: JCol[], monthZhi: string, zset: Record<string, number>): { ok: boolean; reason?: string } {
  const pk = pairKey(c1.zhi, c2.zhi)
  const count = (z: string) => (zset[z] ?? 0) * (z === monthZhi ? 2 : 1) // 当令翻倍
  if (pk === '子卯') {
    if (count('子') >= 3 && count('子') > count('卯')) return { ok: true }
    if (count('卯') >= 2 && count('卯') > count('子')) return { ok: true }
    return { ok: false, reason: '条件不足' } // 1:1 以相生论
  }
  if (pk === '寅巳') {
    if (count('寅') >= 3 && count('寅') > count('巳')) return { ok: true }
    if (count('巳') >= 2 && count('巳') > count('寅')) return { ok: true }
    return { ok: false, reason: '条件不足' }
  }
  if (c1.zhi === c2.zhi && ZI_XING_SET.has(c1.zhi)) {
    // 修复（2026-08-17）：自刑须满足成立条件（化神透出/太旺 + 月令旺相 + 不逢合冲）
    return zixingOk(c1.zhi, cols, monthZhi, zset) ? { ok: true } : { ok: false, reason: '条件不足' }
  }
  return { ok: true } // 巳申/寅申 1:1 仍成立；丑戌/未戌/丑未两支可论
}

function sanheHuiOk(rtype: string, wx: string, branches: string[], cols: JCol[], monthZhi: string): boolean {
  const tou = cols.some((c) => c.gan && GAN_WUXING[c.gan] === wx)
  const deg = wxDegreesLite(cols)
  const countOf = (z: string) => branches.filter((b) => b === z).length
  if (rtype === '三合') {
    if (!['旺', '相'].includes(monthState(wx, monthZhi))) return false
    if (!(tou || deg[wx] >= 26)) return false
    const muku = ({ 木: '未', 火: '戌', 金: '丑', 水: '辰' } as Record<string, string>)[wx]
    if (wx !== '火' && branches.includes(muku) && '辰戌丑未'.includes(monthZhi)) return false
    if (countOf(muku) >= 3) return false
    return true
  }
  if (!(tou || deg[wx] >= 20)) return false
  const muku = ({ 木: '辰', 火: '未', 金: '戌', 水: '丑' } as Record<string, string>)[wx]
  if (branches.includes(muku) && muku === monthZhi && !['辰', '丑'].includes(muku)) return false
  if (countOf(muku) >= 3) return false
  if (deg[KE_INV[wx]] >= 26) return false
  return true
}

/**
 * 干支关系条件判定（008：《四柱精髓》口径，与后端 wangdu.judge_relations 对拍）。
 * @param opts.excludeColIds 排除列（如不关联大运/流年）
 * 返回 { established, rejected }：成立关系画线/入汇总，未成立关系入"未成立"分组（含原因）。
 */
export function buildRelationJudgments(
  cols: RelCol[],
  opts?: { excludeColIds?: string[] },
): { established: Judgment[]; rejected: Judgment[] } {
  const exclude = new Set(opts?.excludeColIds ?? [])
  const active = cols.filter((c) => !exclude.has(c.id))
  const monthZhi = active.find((c) => c.id === 'month')?.zhi ?? ''
  const zhiCount: Record<string, number> = {}
  for (const c of active) if (c.zhi) zhiCount[c.zhi] = (zhiCount[c.zhi] ?? 0) + 1
  const jcols: JCol[] = active.map((c, idx) => ({
    idx, id: c.id, gan: c.gan, zhi: c.zhi,
    hidden: c.zhi ? Object.fromEntries(hiddenDegrees(c.zhi, monthZhi, zhiCount)) : {},
  }))

  const established: Judgment[] = []
  const rejected: Judgment[] = []

  // ---------- 天干层 ----------
  interface StemPair { i: number; j: number; type: string; detail: string }
  const ganPairs: StemPair[] = []
  const stemIdx = jcols.filter((c) => c.gan).map((c) => c.idx)
  for (let a = 0; a < stemIdx.length; a++) {
    for (let b = a + 1; b < stemIdx.length; b++) {
      const i = stemIdx[a]
      const j = stemIdx[b]
      const rel = stemRelation(jcols[i].gan, jcols[j].gan)
      if (!rel) continue
      const bothJu = JU_KEYS.has(jcols[i].id) && JU_KEYS.has(jcols[j].id)
      if (bothJu && Math.abs(i - j) !== 1) {
        // 中隔同类可论生克、不论合（§2.1-1）
        const mids = jcols.slice(Math.min(i, j) + 1, Math.max(i, j)).filter((c) => c.gan)
        const bridge = mids.some((m) =>
          [GAN_WUXING[jcols[i].gan], GAN_WUXING[jcols[j].gan]].includes(GAN_WUXING[m.gan]),
        )
        if (rel.type === '五合') {
          rejected.push({ a: jcols[i].gan, b: jcols[j].gan, layer: 'stem', type: '五合', reason: '隔位不论' })
          continue
        }
        if (!bridge) continue // 生克隔位无同类中隔：不论
      }
      ganPairs.push({ i, j, type: rel.type, detail: rel.detail })
    }
  }

  // 争合（§3.6）：同一干被多干合 → 力量大者优先，失利者不论；势均力敌双方合绊；岁运不争合
  const competed = new Set<StemPair>()
  for (const p of ganPairs) {
    if (p.type !== '五合') continue
    for (const t of [p.i, p.j]) {
      const involved = ganPairs.filter(
        (q) => q.type === '五合' && (q.i === t || q.j === t) &&
          pairKey(jcols[q.i].gan, jcols[q.j].gan) === pairKey(jcols[p.i].gan, jcols[p.j].gan),
      )
      if (involved.length < 2) continue
      if (involved.some((q) => !JU_KEYS.has(jcols[q.i].id) || !JU_KEYS.has(jcols[q.j].id))) continue
      const power = (q: StemPair) => {
        const o = q.i === t ? q.j : q.i
        const c = jcols[o]
        const root = Object.entries(c.hidden)
          .filter(([g]) => GAN_WUXING[g] === GAN_WUXING[c.gan])
          .reduce((s, [, d]) => s + d, 0)
        return 1 + root
      }
      const powers = involved.map(power)
      if (Math.max(...powers) - Math.min(...powers) < 1e-9) continue
      const winner = involved[powers.indexOf(Math.max(...powers))]
      for (const q of involved) if (q !== winner) competed.add(q)
    }
  }

  for (const p of ganPairs) {
    const c1 = jcols[p.i]
    const c2 = jcols[p.j]
    const pos = [POS_LABEL[c1.id], POS_LABEL[c2.id]]
    if (p.type === '五合') {
      if (competed.has(p)) {
        rejected.push({ a: c1.gan, b: c2.gan, layer: 'stem', type: '五合', reason: '争合失利', positions: pos })
        continue
      }
      const hua = GAN_HE_HUA_MAP[pairKey(c1.gan, c2.gan)]
      const ok = stemHeHuaOk(c1, c2, hua, jcols, monthZhi)
      established.push({
        a: c1.gan, b: c2.gan, layer: 'stem', type: '五合',
        detail: ok ? `合化${hua}` : '合绊', positions: pos,
        aColId: c1.id, bColId: c2.id,
      })
    } else {
      established.push({
        a: c1.gan, b: c2.gan, layer: 'stem', type: p.type, detail: p.detail,
        aColId: c1.id, bColId: c2.id,
      })
    }
  }

  // ---------- 地支层 ----------
  interface BEntry {
    i: number; j: number; type: string; a: string; b: string
    detail?: string; rejected?: string; hua?: string | null
    members?: string[]; memberIdxs?: number[]
  }
  const branchActionable = (i: number, j: number): boolean => {
    if (!JU_KEYS.has(jcols[i].id) || !JU_KEYS.has(jcols[j].id)) return true // 岁运介入
    const lo = Math.min(i, j)
    const hi = Math.max(i, j)
    if (hi - lo === 1) return true
    const mids = new Set(jcols.slice(lo + 1, hi).map((c) => c.zhi))
    return mids.has(jcols[i].zhi) || mids.has(jcols[j].zhi) // 中隔为其中一支本身可论
  }

  const refined: BEntry[] = []
  const zhiIdx = jcols.filter((c) => c.zhi).map((c) => c.idx)
  const zsetCount: Record<string, number> = {}
  for (const c of jcols) if (c.zhi) zsetCount[c.zhi] = (zsetCount[c.zhi] ?? 0) + 1
  for (let a = 0; a < zhiIdx.length; a++) {
    for (let b = a + 1; b < zhiIdx.length; b++) {
      const i = zhiIdx[a]
      const j = zhiIdx[b]
      const types = branchPairTypes(jcols[i].zhi, jcols[j].zhi)
      if (!types.length) continue
      const actionable = branchActionable(i, j)
      for (const t of types) {
        if (!actionable) {
          refined.push({ i, j, type: t, a: jcols[i].zhi, b: jcols[j].zhi, rejected: '隔位不论' })
          continue
        }
        const entry: BEntry = { i, j, type: t, a: jcols[i].zhi, b: jcols[j].zhi }
        if (t === '六合') {
          const v = liuheVerdict(jcols[i], jcols[j], jcols, monthZhi)
          entry.detail = v.detail
          entry.hua = v.hua
        } else if (t === '半三合') {
          const v = banheVerdict(jcols[i], jcols[j], jcols, monthZhi)
          entry.detail = v.detail
          entry.hua = v.hua
        } else if (t === '刑') {
          const v = xingVerdict(jcols[i], jcols[j], jcols, monthZhi, zsetCount)
          if (!v.ok) entry.rejected = v.reason
          else entry.detail = '刑（成立）'
        } else if (t === '相冲') {
          entry.detail = '冲'
        } else if (t === '害') {
          entry.detail = '害'
        } else if (t === '破') {
          entry.detail = '破'
        }
        refined.push(entry)
      }
    }
  }

  // 三支关系（三合/三会/三刑）：成局不论位置；不化且三支不连续 → 条件不足
  const zsetCols: Record<string, number[]> = {}
  for (const c of jcols) if (c.zhi) (zsetCols[c.zhi] ??= []).push(c.idx)
  const triples: BEntry[] = []
  const tripleGroups: { key: string; type: string; wx: string | null }[] = [
    ...Object.entries(SAN_HE_MAP).map(([k, wx]) => ({ key: k, type: '三合', wx })),
    ...Object.entries(SAN_HUI_MAP).map(([k, wx]) => ({ key: k, type: '三会', wx })),
    ...SAN_XING_SETS.map((k) => ({ key: k, type: '三刑', wx: null })),
  ]
  for (const g of tripleGroups) {
    const branches = [...g.key]
    if (!branches.every((z) => zsetCols[z]?.length)) continue
    const idxs = branches.map((z) => zsetCols[z][0])
    const entry: BEntry = {
      i: idxs[0], j: idxs[idxs.length - 1], type: g.type,
      a: jcols[idxs[0]].zhi, b: jcols[idxs[idxs.length - 1]].zhi,
      members: branches, memberIdxs: idxs,
    }
    if (g.type === '三刑') {
      entry.detail = '三刑'
    } else {
      const ok = sanheHuiOk(g.type, g.wx!, branches, jcols, monthZhi)
      const contiguous = Math.max(...idxs) - Math.min(...idxs) === idxs.length - 1
      entry.hua = ok ? g.wx : null
      if (ok) entry.detail = `合化${g.wx}`
      else if (g.key === '巳午未' && contiguous) entry.detail = '互助' // 巳午未特殊：不化不论绊，论互相帮扶
      else if (contiguous) entry.detail = '合绊'
      else entry.rejected = '条件不足'
    }
    triples.push(entry)
  }

  // 合冲并见与让位（§9.3）
  const isHe = (e: BEntry) => ['六合', '半三合', '三合', '三会'].includes(e.type) && !e.rejected
  const all = [...refined.filter((e) => !e.rejected), ...triples.filter((t) => !t.rejected)]
  for (const e of all) {
    if (e.type !== '相冲') continue
    const master = !JU_KEYS.has(jcols[e.i].id) ? e.i : !JU_KEYS.has(jcols[e.j].id) ? e.j : null
    if (master !== null) {
      const bound = all.some((h) => h !== e && isHe(h) && [h.i, h.j].includes(master))
      if (bound) e.rejected = '被合绊让位' // 主冲之支被合绊 → 冲不成
    }
  }
  for (const e of all) {
    if (e.type !== '相冲' || e.rejected) continue
    if (!JU_KEYS.has(jcols[e.i].id) || !JU_KEYS.has(jcols[e.j].id)) continue
    const heldI = all.some((h) => h !== e && isHe(h) && [h.i, h.j].includes(e.i))
    const heldJ = all.some((h) => h !== e && isHe(h) && [h.i, h.j].includes(e.j))
    if (heldI && heldJ) {
      e.rejected = '冲被合解' // 相冲两支全被合住 → 论合不论冲
    } else if (heldI || heldJ) {
      for (const h of all) {
        if (h !== e && isHe(h) && ([h.i, h.j].includes(e.i) || [h.i, h.j].includes(e.j))) {
          h.rejected = '后论关系让位' // 原局合冲同现 → 论冲不论合
        }
      }
    }
  }

  // 汇总输出
  const involvesOf = (e: BEntry): string | undefined =>
    [jcols[e.i].id, jcols[e.j].id].includes('dayun') ? 'dayun'
      : [jcols[e.i].id, jcols[e.j].id].includes('liunian') ? 'liunian' : undefined
  for (const e of [...refined, ...triples]) {
    const inv = involvesOf(e)
    if (e.rejected) {
      rejected.push({
        a: e.a, b: e.b, layer: 'branch', type: e.type, reason: e.rejected,
        ...(inv ? { involves: inv } : {}),
      })
    } else {
      established.push({
        a: e.a, b: e.b, layer: 'branch', type: e.type, detail: e.detail ?? e.type,
        ...(inv ? { involves: inv } : {}),
        aColId: jcols[e.i].id, bColId: jcols[e.j].id,
        ...(e.members ? { members: e.members, memberColIds: e.memberIdxs!.map((k) => jcols[k].id) } : {}),
      })
    }
  }

  return { established, rejected }
}
