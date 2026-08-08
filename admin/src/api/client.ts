/** Admin API client: in-memory access token + refresh-on-401. */

let accessToken: string | null = null

export function setAccessToken(token: string | null) {
  accessToken = token
}

export function getAccessToken() {
  return accessToken
}

export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  headers.set('Content-Type', 'application/json')
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`)

  let resp = await fetch(path, { ...options, headers, credentials: 'same-origin' })

  if (resp.status === 401 && path !== '/api/auth/login') {
    const r = await fetch('/api/auth/refresh', { method: 'POST', credentials: 'same-origin' })
    if (r.ok) {
      setAccessToken((await r.json()).access_token)
      const h2 = new Headers(headers)
      if (accessToken) h2.set('Authorization', `Bearer ${accessToken}`)
      resp = await fetch(path, { ...options, headers: h2, credentials: 'same-origin' })
    }
  }

  if (resp.status === 204) return undefined as T
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}))
    if (resp.status === 403) throw new Error('无管理员权限')
    throw new Error((body as { detail?: string }).detail || '请求失败')
  }
  return (await resp.json()) as T
}
