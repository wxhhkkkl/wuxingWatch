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
