/** 大运/流年默认选中逻辑（当前日期驱动）。 */

import type { DaYunStep } from '../types'

/** 当前年所在大运的下标（end_year 含端点）；不在任何区间（未起运等）回退第一步。 */
export function defaultDayunIndex(steps: DaYunStep[], currentYear: number): number {
  const idx = steps.findIndex(
    (s) => s.start_year != null && s.end_year != null && s.start_year <= currentYear && currentYear <= s.end_year,
  )
  return idx >= 0 ? idx : 0
}

/** 选中大运内默认流年：含当前年则当前年，否则该运第一年。 */
export function defaultLiunianYear(step: DaYunStep, currentYear: number): number | null {
  const years = step.liu_nian ?? []
  if (!years.length) return null
  return years.some((n) => n.year === currentYear) ? currentYear : years[0].year
}

/** 当前时刻所在节气月的月支（start ≤ now < end）；不在任何月内返回 null。 */
export function defaultLiuyueBranch(
  months: { branch: string; start: string; end: string }[],
  now: Date,
): string | null {
  const t = now.getTime()
  const hit = months.find((m) => new Date(m.start).getTime() <= t && t < new Date(m.end).getTime())
  return hit ? hit.branch : null
}

/** 流日列表中默认选中的日期：今日在列则今日，否则 null（调用方回落）。 */
export function defaultLiuriDate(days: { date: string }[], now: Date): string | null {
  const p = (n: number) => String(n).padStart(2, '0')
  const today = `${now.getFullYear()}-${p(now.getMonth() + 1)}-${p(now.getDate())}`
  return days.some((d) => d.date === today) ? today : null
}

const ZHI_LIST = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

/** 小时（0-23）→ 时支：23/0 点子时，1-2 丑时……21-22 亥时。 */
export function shichenZhiOf(hour: number): string {
  return ZHI_LIST[Math.floor(((hour + 1) % 24) / 2)]
}
