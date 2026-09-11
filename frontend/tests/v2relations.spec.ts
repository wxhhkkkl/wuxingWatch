/**
 * T072 — 后端 v2 关系裁定的前端适配与命盘图消费（012，方案 A）。
 *
 * 裁定依据：012 spec C26-3 / research R7「方案 A」——命盘图**消费后端裁定**，
 * 不再本地复判；原本地实现与后端**已经漂移**（丑·水状态、丑/辰党众取度）。
 */
import { describe, it, expect } from 'vitest'
import { toFrontendType, v2RelationsToJudgments } from '../src/utils/v2relations'
import { REL_TYPES } from '../src/utils/relations'
import type { V2Relation } from '../src/types'

function rel(over: Partial<V2Relation>): V2Relation {
  return {
    tier: 8, type: '六冲', members: ['子', '午'], cols: ['month', 'time'],
    hua: null, detail: '子午冲', effects: [], ...over,
  } as V2Relation
}

describe('v2RelationsToJudgments', () => {
  it('地支两两关系 → branch 层 Judgment，柱位 id 保留', () => {
    const out = v2RelationsToJudgments({ established: [rel({})], rejected: [] })!
    expect(out.established).toHaveLength(1)
    const j = out.established[0]
    expect(j.layer).toBe('branch')
    expect(j.a).toBe('子')
    expect(j.b).toBe('午')
    expect(j.aColId).toBe('month')
    expect(j.bColId).toBe('time')
  })

  it('三支关系（三合/三会/三刑）→ 成员与柱位完整保留', () => {
    const sanhe = rel({ tier: 6, type: '三合', members: ['亥', '卯', '未'],
                        cols: ['year', 'month', 'day'], hua: '木' })
    const out = v2RelationsToJudgments({ established: [sanhe], rejected: [] })!
    const j = out.established[0]
    expect(j.members).toEqual(['亥', '卯', '未'])
    expect(j.memberColIds).toEqual(['year', 'month', 'day'])
  })

  it('天合地合（tier 1，members 为四字）→ stem 层，支另存于 members', () => {
    const tianhe = rel({ tier: 1, type: '天合地合', members: ['乙', '庚', '辰', '酉'],
                         cols: ['year', 'month'], hua: '金' })
    const out = v2RelationsToJudgments({ established: [tianhe], rejected: [] })!
    const j = out.established[0]
    expect(j.layer).toBe('stem')
    expect([j.a, j.b]).toEqual(['乙', '庚'])
    expect(j.members).toEqual(['辰', '酉'])
  })

  it('rejected 条目带 reason，供命盘图「未成立」分组展示', () => {
    const rej = rel({ reason: '让位：被 tier 4（三会）消费' })
    const out = v2RelationsToJudgments({ established: [], rejected: [rej] })!
    expect(out.rejected[0].reason).toContain('让位')
  })

  it('无裁定可用时返回 null——调用方回退本地判定（旧记录兼容）', () => {
    expect(v2RelationsToJudgments(null)).toBeNull()
    expect(v2RelationsToJudgments(undefined)).toBeNull()
    expect(v2RelationsToJudgments({ established: [], rejected: [] })).toBeNull()
  })
})

// ---- 组件级：命盘图确实消费后端裁定（T072）----

import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import RelationDiagram from '../src/components/RelationDiagram.vue'
import { mockResult } from './fixtures'

function mountDiagram(strength: unknown) {
  setActivePinia(createPinia())
  const result = JSON.parse(JSON.stringify(mockResult))
  result.xi_yong.strength = strength
  return mount(RelationDiagram, { props: { result } })
}

describe('RelationDiagram 消费后端 v2 裁定', () => {
  it('v2 结果：汇总里出现后端的裁定条目', () => {
    const strength = {
      engine: 'wangdu-v2', contract_version: 2,
      relations: {
        established: [{
          tier: 8, type: '六冲', members: ['子', '午'], cols: ['year', 'time'],
          hua: null, detail: '子午冲〔来自后端裁定〕', effects: [],
        }],
        rejected: [{
          tier: 12, type: '六合', members: ['子', '丑'], cols: ['year', 'month'],
          hua: null, detail: '', effects: [], reason: '让位：被 tier 8（六冲）消费',
        }],
      },
    }
    const w = mountDiagram(strength)
    const text = w.text()
    expect(text).toContain('子午冲')
    expect(text).toContain('让位')
  })

  it('非 v2 结果：回退本地判定路径，不报错（旧记录兼容）', () => {
    const w = mountDiagram({ method: 'sizhu-jingsui', level: '较弱' })
    expect(w.exists()).toBe(true)
  })
})

describe('后端类型名 → 前端 RelType 映射', () => {
  it('书里的十八级名映射到前端筛选器的 12 类', () => {
    expect(toFrontendType('六冲')).toBe('相冲')
    expect(toFrontendType('生地半三合')).toBe('三合')
    expect(toFrontendType('丑未戌刑')).toBe('刑')
    expect(toFrontendType('卯辰半会')).toBe('三会')
    expect(toFrontendType('六合')).toBe('六合')
  })

  it('映射后的类型必须落在前端 REL_TYPES 内——否则会被筛选器滤掉、连不上线', () => {
    for (const bt of ['天合地合', '天克地冲', '三会', '卯辰半会', '拱会', '四库土局',
                      '三合', '生地半三合', '墓地半三合', '拱合', '六冲', '六合',
                      '六害', '丑未戌刑', '寅巳申三刑', '三支自刑', '两支刑']) {
      expect(REL_TYPES as readonly string[]).toContain(toFrontendType(bt))
    }
  })

  it('未知类型原样返回（不静默篡改）', () => {
    expect(toFrontendType('某个没见过的类型')).toBe('某个没见过的类型')
  })
})
