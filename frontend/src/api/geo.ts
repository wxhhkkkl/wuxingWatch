import { request } from './client'

export interface GeoCity {
  name: string
  name_zh: string | null
  admin1_zh: string | null
  country_code: string | null
  latitude: number
  longitude: number
  timezone: string | null
}

export function searchGeo(q: string): Promise<{ items: GeoCity[] }> {
  return request<{ items: GeoCity[] }>(`/api/geo/search?q=${encodeURIComponent(q)}`)
}
