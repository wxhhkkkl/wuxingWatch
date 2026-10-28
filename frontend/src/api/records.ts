import { request } from './client'
import type { BirthInput, Dayun2Response, RecordDetail, RecordSummary } from '../types'

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

export function updateRecord(id: number, input: SaveRecordInput): Promise<RecordDetail> {
  return request<RecordDetail>(`/api/records/${id}`, { method: 'PUT', body: JSON.stringify(input) })
}

export function deleteRecord(id: number): Promise<void> {
  return request<void>(`/api/records/${id}`, { method: 'DELETE' })
}

/** 从**已保存记录**进大运引擎2（014 T027）——后端按该记录输入**当场重推**四柱与大运步。 */
export function getRecordDayun2(id: number, dayunGanzhi?: string): Promise<Dayun2Response> {
  const q = new URLSearchParams()
  if (dayunGanzhi) q.set('dayun_ganzhi', dayunGanzhi)
  const qs = q.toString()
  return request<Dayun2Response>(`/api/records/${id}/dayun2${qs ? `?${qs}` : ''}`)
}
