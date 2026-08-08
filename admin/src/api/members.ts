import { request } from './client'

export interface MemberListItem {
  id: number
  phone_masked: string
  created_at: string
  chart_count: number
}

export interface MemberDetail {
  id: number
  phone: string
  name: string | null
  created_at: string
  chart_count: number
}

export interface ChartSummary {
  id: number
  person_name: string | null
  relationship: string
  created_at: string
  summary: { year?: unknown; month?: unknown; day?: unknown; time?: unknown }
}

export function listMembers(params: { page: number; page_size: number; phone?: string }) {
  const q = new URLSearchParams({ page: String(params.page), page_size: String(params.page_size) })
  if (params.phone) q.set('phone', params.phone)
  return request<{ total: number; items: MemberListItem[] }>(`/api/admin/members?${q.toString()}`)
}

export function getMember(id: number): Promise<MemberDetail> {
  return request<MemberDetail>(`/api/admin/members/${id}`)
}

export function listMemberCharts(id: number, page = 1): Promise<{ items: ChartSummary[] }> {
  return request<{ items: ChartSummary[] }>(`/api/admin/members/${id}/charts?page=${page}`)
}

export function getChart(id: number): Promise<{ id: number; chart_result: Record<string, unknown> }> {
  return request<{ id: number; chart_result: Record<string, unknown> }>(`/api/admin/charts/${id}`)
}
