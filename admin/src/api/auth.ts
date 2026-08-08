import { request, setAccessToken } from './client'

export interface AdminUser {
  id: number
  phone: string
}

export async function login(phone: string, password: string): Promise<{ access_token: string; user: AdminUser }> {
  const data = await request<{ access_token: string; user: AdminUser }>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ phone, password }),
  })
  setAccessToken(data.access_token)
  return data
}
