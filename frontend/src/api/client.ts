/** Minimal fetch wrapper with access token + refresh-on-401.
 * accessToken 持久化到 localStorage：页面刷新后恢复，避免首个请求因无 token 而 401。 */

const TOKEN_KEY = 'access_token'

let accessToken: string | null = null
try {
  accessToken = localStorage.getItem(TOKEN_KEY)
} catch {
  accessToken = null
}

export function setAccessToken(token: string | null) {
  accessToken = token
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
  } catch {
    /* ignore */
  }
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

/** 鉴权失败：清除登录态并跳转登录页（已在登录页则不重复跳转）。 */
function handleAuthFailure() {
  setAccessToken(null)
  try {
    // pinia-plugin-persistedstate 默认以 store id('auth') 为 localStorage key
    localStorage.removeItem('auth')
  } catch {
    /* ignore */
  }
  if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
    const redirect = encodeURIComponent(window.location.pathname + window.location.search)
    window.location.replace(`/login?redirect=${redirect}`)
  }
}

export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  headers.set('Content-Type', 'application/json')
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`)

  // cache: 'no-store' 防止浏览器复用旧账号/旧会话的 API 响应（如记录列表串号）
  let resp = await fetch(path, { ...options, headers, credentials: 'same-origin', cache: 'no-store' })

  if (resp.status === 401 && path !== '/api/auth/refresh') {
    const refreshed = await tryRefresh()
    if (refreshed) {
      const headers2 = new Headers(headers)
      if (accessToken) headers2.set('Authorization', `Bearer ${accessToken}`)
      resp = await fetch(path, { ...options, headers: headers2, credentials: 'same-origin', cache: 'no-store' })
    }
  }

  // 鉴权失败（refresh 也失败，或重试后仍 401）：跳转登录页；登录类接口（如密码错误）不跳
  if (resp.status === 401 && !path.startsWith('/api/auth/')) {
    handleAuthFailure()
  }

  if (resp.status === 204) return undefined as T
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}))
    throw new ApiError(resp.status, (body as { detail?: string }).detail || '请求失败，请稍后再试')
  }
  return (await resp.json()) as T
}
