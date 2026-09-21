import { request } from './client'
import type {
  BirthInput,
  ChartResult,
  LiuRiResponse,
  LiuShiRequest,
  LiuShiResponse,
  LiuYueResponse,
  SuiyunResponse,
} from '../types'

export function predictChart(input: BirthInput): Promise<ChartResult> {
  return request<ChartResult>('/api/charts/predict', { method: 'POST', body: JSON.stringify(input) })
}

/** 岁运推导（013 T034；FR-021a）——**按需实时算、不落库**（FR-026）。
 *
 *  给 `liunian_year` 即得**阶段 3**（另含 `pairs`），不给只算**阶段 2**。 */
export function fetchSuiyun(
  input: BirthInput & { dayun_ganzhi: string; liunian_year?: number },
): Promise<SuiyunResponse> {
  return request<SuiyunResponse>('/api/charts/suiyun', {
    method: 'POST', body: JSON.stringify(input),
  })
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
