/**
 * 012 期：把**后端 v2 关系裁定**适配为命盘图既有的 `Judgment` 形状（T071）。
 *
 * 背景：008 期起命盘图用 `utils/relations.ts` 在**浏览器里自己判一遍**关系，
 * 与后端 `wangdu.judge_relations` 构成双实现，且两份**已经漂移**（丑·水状态、
 * 丑/辰党众取度）。012 裁定走**方案 A**：命盘图改为**消费后端裁定**，
 * 不再本地复判——从根上消除实现漂移。
 *
 * 本文件只做**形状适配**（后端 `V2Relation` → 前端 `Judgment`），不含任何判定逻辑。
 */

import type { Judgment } from './relations'
import type { V2Relation } from '../types'

/**
 * 后端 `tier.type` → 前端 `RelType` 的映射。
 *
 * 两侧的**命名体系不同**：后端用书里的十八级名（六冲、生地半三合、拱会…），
 * 前端 `RelType` 是 008 期为筛选器定的 12 类（相冲、三合、三会…）。
 * 不映射的话，后端裁定会因类型不在 `REL_TYPES` 里而被**筛选器滤掉、连不上线**。
 */
const TYPE_MAP: Record<string, string> = {
  天合地合: '合',
  天克地冲: '冲',
  三会: '三会',
  卯辰半会: '三会',
  拱会: '三会',
  四库土局: '三会',
  三合: '三合',
  生地半三合: '三合',
  墓地半三合: '三合',
  拱合: '三合',
  六冲: '相冲',
  六合: '六合',
  六害: '害',
  丑未戌刑: '刑',
  寅巳申三刑: '刑',
  三支自刑: '刑',
  两支刑: '刑',
  // 特殊生克（未克申酉/子生寅…）在书里分生与克两类，前端 12 类里无对应；
  // 归入「克」以保住连线与筛选的可操作性，**不计入精确判定**。
  特殊生克: '克',
}

/** 映射为该前端可识别的 `RelType`；未知类型原样返回（会被筛选器挡住）。 */
export function toFrontendType(backendType: string): string {
  return TYPE_MAP[backendType] ?? backendType
}

/** 天干层关系（tier 1/2 的 members 形如 [干,干,支,支]）。 */
const STEM_LAYER_TIERS = new Set([1, 2])

/** 后端的附加列 id → 命盘图既有的列 id。 */
const COL_ID_MAP: Record<string, string> = { _dayun: 'dayun', _liunian: 'liunian' }

function colId(id: string): string {
  return COL_ID_MAP[id] ?? id
}

function isStemLayer(r: V2Relation): boolean {
  return STEM_LAYER_TIERS.has(r.tier) && r.members.length >= 4
}

function toJudgment(r: V2Relation, established: boolean): Judgment {
  const stem = isStemLayer(r)
  if (stem) {
    const [g1, g2, z1, z2] = r.members
    return {
      a: g1, b: g2, layer: 'stem', type: toFrontendType(r.type), detail: r.detail,
      aColId: colId(r.cols[0]), bColId: colId(r.cols[1]),
      members: [z1, z2], memberColIds: r.cols.map(colId),
      ...(established ? {} : { reason: r.reason }),
    }
  }
  // 地支层：一个关系可能涉及 2 支（六合/冲/害/刑）或 3 支（三合/三会/三刑）
  const members = r.members
  return {
    a: members[0], b: members[1] ?? members[0],
    layer: 'branch', type: toFrontendType(r.type), detail: r.detail,
    aColId: colId(r.cols[0]), bColId: colId(r.cols[1] ?? r.cols[0]),
    members: [...members], memberColIds: r.cols.map(colId),
    ...(established ? {} : { reason: r.reason }),
  }
}

/**
 * 后端 `strength.relations` → 命盘图用的 `{ established, rejected }`。
 *
 * 无裁定可用时（旧记录、或输入不足）返回 `null`，调用方回退到本地判定路径。
 */
export function v2RelationsToJudgments(
  relations: { established: V2Relation[]; rejected: V2Relation[] } | undefined | null,
): { established: Judgment[]; rejected: Judgment[] } | null {
  if (!relations || (!relations.established?.length && !relations.rejected?.length)) {
    return null
  }
  return {
    established: (relations.established ?? []).map((r) => toJudgment(r, true)),
    rejected: (relations.rejected ?? []).map((r) => toJudgment(r, false)),
  }
}
