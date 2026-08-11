import { request } from './client'
import type { BirthInput, RecordDetail, RecordSummary } from '../types'

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
