import type { GeJuDayunStep, GeJuRef, GeJuStrength } from '../types'

export const GEJU_STATUS_LABEL: Record<string, string> = {
  cheng: '成格',
  po: '破格',
  fu_cheng: '破而复成',
  undetermined: '未定',
}

export const STRENGTH_LABEL: Record<string, string> = {
  strong: '身强',
  weak: '身弱',
  unknown: '身强弱未知',
}

export function gejuName(ref: GeJuRef | null): string {
  if (!ref) return '未定'
  return ref.aliases.length ? `${ref.name}（${ref.aliases[0]}）` : ref.name
}

export function strengthText(s: GeJuStrength | null | undefined): string {
  if (!s) return '身强弱未知'
  return `${STRENGTH_LABEL[s.value] ?? '未知'} · ${s.score} 度`
}

export function stepOf(
  steps: GeJuDayunStep[], ganzhi: string | null | undefined,
): GeJuDayunStep | null {
  if (!ganzhi) return null
  return steps.find((s) => s.ganzhi === ganzhi) ?? null
}
