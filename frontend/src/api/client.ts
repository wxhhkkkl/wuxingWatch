/** Minimal fetch wrapper with in-memory access token + refresh-on-401. */

let accessToken: string | null = null

export function setAccessToken(token: string | null) {
  accessToken = token
}

export function getAccessToken() {
  return accessToken
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function tryRefresh(): Promise<boolean> {
  const resp = await fetch('/api/auth/refresh', { method: 'POST', credentials: 'same-origin' })
  if (!resp.ok) return false
  const data = await resp.json()
  setAccessToken(data.access_token)
  return true
}

export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  headers.set('Content-Type', 'application/json')
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`)

  let resp = await fetch(path, { ...options, headers, credentials: 'same-origin' })

  if (resp.status === 401 && path !== '/api/auth/refresh') {
    const refreshed = await tryRefresh()
    if (refreshed) {
      const headers2 = new Headers(headers)
      if (accessToken) headers2.set('Authorization', `Bearer ${accessToken}`)
      resp = await fetch(path, { ...options, headers: headers2, credentials: 'same-origin' })
    }
  }

  if (resp.status === 204) return undefined as T
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}))
    throw new ApiError(resp.status, (body as { detail?: string }).detail || '请求失败，请稍后再试')
  }
  return (await resp.json()) as T
}
