import { request } from './client'
import type { BirthInput, GeJuResponse } from '../types'

/** 子平格局喜忌（015）——按需实时算、不落库；不给 dayun_ganzhi 返回全部大运步。 */
export function fetchGeju(
  input: BirthInput & { dayun_ganzhi?: string },
): Promise<GeJuResponse> {
  return request<GeJuResponse>('/api/charts/geju', {
    method: 'POST', body: JSON.stringify(input),
  })
}

/** 从已保存记录进格局喜忌——按记录输入当场重推。 */
export function getRecordGeju(
  id: number, dayunGanzhi?: string,
): Promise<GeJuResponse> {
  const q = new URLSearchParams()
  if (dayunGanzhi) q.set('dayun_ganzhi', dayunGanzhi)
  const qs = q.toString()
  return request<GeJuResponse>(`/api/records/${id}/geju${qs ? `?${qs}` : ''}`)
}
