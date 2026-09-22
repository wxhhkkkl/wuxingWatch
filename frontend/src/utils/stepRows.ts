/**
 * 判定依据「一段之内」的渲染序列（012 v2 建立，013 补遗抽为共享纯函数）。
 *
 * 抽出的理由与 `components/StepChart.vue` 同：原局页与岁运两页要「效果一致」，
 * 而序列的**次序规则**（逐实例快照插在哪一行之后、速览格与命盘是否相邻）是最容易
 * 两处各写一遍、然后悄悄漂移的地方。
 */
import type { StepTrace, V2ChartPillar, V2Step } from '../types'

const WUXING = ['木', '火', '土', '金', '水'] as const
const WUXING_SET = new Set<string>(WUXING)

type Wx = (typeof WUXING)[number]

export type StepRow =
  | { kind: 'trace'; t: StepTrace }
  | { kind: 'scores' }
  | { kind: 'result' }
  | { kind: 'chart'; label: string; pillars: V2ChartPillar[]; testid: string }

/** 该段 traces 里以**五行为 target** 且带数值者——渲染成得分行。
 *
 *  静态旺度 / 动态定级这两段天然给出五个五行的度数；其余段落多为说明性 traces。
 *  只在该段覆盖 ≥2 个五行时才当作「得分行」渲染，避免把零散 trace 误当表格。 */
export function stepScores(
  s: { traces?: { target: string; value: number | string | null }[] },
): { wx: Wx; value: number | undefined }[] {
  const m = new Map<string, number>()
  for (const t of s.traces ?? []) {
    if (WUXING_SET.has(t.target) && typeof t.value === 'number') m.set(t.target, t.value)
  }
  if (m.size < 2) return []
  return WUXING.map((wx) => ({ wx, value: m.get(wx) }))
}

/** 一段之内的渲染序列。
 *
 *  顺序：算式行 →（第 7 段的**逐实例快照**插在对应算式之后）→ 结果 → 五行速览 → 段末命盘。
 *  速览格与命盘相邻；第 7 段的命盘在过程中逐实例出（末尾那张即本段终态），段末不再重复贴。
 *
 *  算式行**不剔除**已进速览格的那几项——速览格只给「五行 + 数值」，算式本身
 *  （天干/通根/系数的来路）必须逐行可见，否则读者看得到结论看不到过程。
 *
 *  `idPrefix` 只影响快照的 testid（原局页 `v2`、岁运页 `sy-<阶段>`）——DOM 结构不变。
 */
export function stepRows(s: V2Step, idPrefix = 'v2'): StepRow[] {
  const rows: StepRow[] = []
  const points = s.charts ?? []
  let ci = 0
  const emitCharts = (rendered: number) => {
    while (ci < points.length && points[ci].after <= rendered) {
      rows.push({ kind: 'chart', label: `结算至此 · ${points[ci].label}`,
                  pillars: points[ci].chart.pillars,
                  testid: `${idPrefix}-step-chart-${s.key}-${ci + 1}` })
      ci++
    }
  }
  ;(s.traces ?? []).forEach((t, i) => {
    rows.push({ kind: 'trace', t })
    emitCharts(i + 1)
  })
  emitCharts(Number.MAX_SAFE_INTEGER)        // 保险：`after` 越界时补在算式行之后
  rows.push({ kind: 'result' })
  if (stepScores(s).length) rows.push({ kind: 'scores' })
  if (s.chart && !points.length) {
    rows.push({ kind: 'chart', label: '本段结束时的命盘',
                pillars: s.chart.pillars, testid: `${idPrefix}-step-chart-${s.key}` })
  }
  return rows
}
