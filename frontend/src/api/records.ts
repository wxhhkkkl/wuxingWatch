import { request } from './client'
import type { BirthInput, RecordDetail, RecordSummary, SuiyunResponse } from '../types'

export interface SaveRecordInput extends BirthInput {
  person_name?: string
  relationship?: 'SELF' | 'CHILD' | 'PARENT' | 'OTHER'
  notes?: string
}

export interface SavedRecord {
  id: number
  person_name: string | null
  relationship: string
  created_at: string
  chart_result: ChartResultLike
}

type ChartResultLike = Record<string, unknown> & { day_master: string }

export function saveRecord(input: SaveRecordInput): Promise<SavedRecord> {
  return request<SavedRecord>('/api/records', { method: 'POST', body: JSON.stringify(input) })
}

export function listRecords(): Promise<RecordSummary[]> {
  return request<RecordSummary[]>('/api/records')
}

export function getRecord(id: number): Promise<RecordDetail> {
  return request<RecordDetail>(`/api/records/${id}`)
}

/** 从**已保存记录**进岁运推导（013 T034；FR-021a）——后端按该记录的输入**当场重推**
 *  大运与流年（不读记录里可能存过的岁运结论，FR-026）。 */
export function getRecordSuiyun(
  id: number, dayunGanzhi: string, liunianYear?: number,
): Promise<SuiyunResponse> {
  const q = new URLSearchParams({ dayun_ganzhi: dayunGanzhi })
  if (liunianYear != null) q.set('liunian_year', String(liunianYear))
  return request<SuiyunResponse>(`/api/records/${id}/suiyun?${q}`)
}

export function updateRecord(id: number, input: SaveRecordInput): Promise<RecordDetail> {
  return request<RecordDetail>(`/api/records/${id}`, { method: 'PUT', body: JSON.stringify(input) })
}

export function deleteRecord(id: number): Promise<void> {
  return request<void>(`/api/records/${id}`, { method: 'DELETE' })
}
