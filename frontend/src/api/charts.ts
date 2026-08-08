import { request } from './client'
import type { BirthInput, ChartResult } from '../types'

export function predictChart(input: BirthInput): Promise<ChartResult> {
  return request<ChartResult>('/api/charts/predict', { method: 'POST', body: JSON.stringify(input) })
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
