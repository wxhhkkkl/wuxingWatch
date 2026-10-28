import { request } from './client'
import type {
  BirthInput,
  ChartResult,
  LiuRiResponse,
  LiuShiRequest,
  LiuShiResponse,
  LiuYueResponse,
  Dayun2Response,
} from '../types'

export function predictChart(input: BirthInput): Promise<ChartResult> {
  return request<ChartResult>('/api/charts/predict', { method: 'POST', body: JSON.stringify(input) })
}

/** 流月/流日/流时下钻（level=month → LiuYueResponse，day → LiuRiResponse，hour → LiuShiResponse）。 */
export function fetchLiuShi(input: LiuShiRequest & { level: 'month' }): Promise<LiuYueResponse>
export function fetchLiuShi(input: LiuShiRequest & { level: 'day' }): Promise<LiuRiResponse>
export function fetchLiuShi(input: LiuShiRequest & { level: 'hour' }): Promise<LiuShiResponse>
export function fetchLiuShi(input: LiuShiRequest): Promise<unknown> {
  return request('/api/charts/liushi', { method: 'POST', body: JSON.stringify(input) })
}

export async function fetchChartImage(input: BirthInput): Promise<Blob> {
  const resp = await fetch('/api/charts/image', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  if (!resp.ok) throw new Error('命盘图片生成失败')
  return resp.blob()
}

/** **大运引擎2**（014 T027）——按教师八步流程（R30 起含天干五合）独立算出的另一套大运旺度。
 *
 *  **按需实时算、不落库**（FR-008）。
 *  不给 `dayun_ganzhi` 即得该盘**全部**大运步。 */
export function fetchDayun2(
  input: BirthInput & { dayun_ganzhi?: string },
): Promise<Dayun2Response> {
  return request<Dayun2Response>('/api/charts/dayun2', {
    method: 'POST', body: JSON.stringify(input),
  })
}
