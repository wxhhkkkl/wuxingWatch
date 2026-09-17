import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { request, setAccessToken } from '../src/api/client'

describe('request 401 鉴权失败跳转登录', () => {
  const replace = vi.fn()
  const originalLocation = window.location

  beforeEach(() => {
    localStorage.clear()
    replace.mockClear()
    Object.defineProperty(window, 'location', {
      value: { pathname: '/records', search: '', replace },
      writable: true,
    })
  })

  afterEach(() => {
    Object.defineProperty(window, 'location', { value: originalLocation, writable: true })
    vi.unstubAllGlobals()
  })

  it('受保护接口 401 且 refresh 失败 → 清登录态并跳转 /login', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValueOnce(new Response('{"detail":"Not authenticated"}', { status: 401 }))
        .mockResolvedValueOnce(new Response('{}', { status: 401 })), // refresh 失败
    )
    setAccessToken('expired')
    await expect(request('/api/records')).rejects.toThrow()
    expect(localStorage.getItem('auth')).toBeNull()
    expect(replace).toHaveBeenCalledWith('/login?redirect=%2Frecords')
  })

  it('登录类接口（如密码错误）401 不跳转登录页', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValueOnce(new Response('{"detail":"密码错误"}', { status: 401 }))
        .mockResolvedValueOnce(new Response('{}', { status: 401 })), // refresh 失败
    )
    await expect(request('/api/auth/login', { method: 'POST', body: '{}' })).rejects.toThrow(
      '密码错误',
    )
    expect(replace).not.toHaveBeenCalled()
  })
})

describe('并发 401 共用同一次刷新', () => {
  const replace = vi.fn()
  const originalLocation = window.location

  beforeEach(() => {
    localStorage.clear()
    replace.mockClear()
    Object.defineProperty(window, 'location', {
      value: { pathname: '/', search: '', replace },
      writable: true,
    })
  })

  afterEach(() => {
    Object.defineProperty(window, 'location', { value: originalLocation, writable: true })
    vi.unstubAllGlobals()
  })

  it('两个请求同时 401 只刷新一次，且不误跳登录页', async () => {
    // 刷新令牌是一次性轮换的：第一次 refresh 成功、第二次（并发）用旧令牌必然 401
    let refreshCalls = 0
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
        if (String(input) === '/api/auth/refresh') {
          refreshCalls += 1
          return refreshCalls === 1
            ? new Response('{"access_token":"fresh"}', { status: 200 })
            : new Response('{}', { status: 401 })
        }
        const auth = new Headers(init.headers).get('Authorization')
        return auth === 'Bearer fresh'
          ? new Response('{"ok":true}', { status: 200 })
          : new Response('{"detail":"Not authenticated"}', { status: 401 })
      }),
    )
    setAccessToken('stale')

    const results = await Promise.all([request('/api/records'), request('/api/records')])

    expect(refreshCalls).toBe(1)
    expect(results).toEqual([{ ok: true }, { ok: true }])
    expect(localStorage.getItem('auth')).toBeNull()
    expect(replace).not.toHaveBeenCalled()
  })
})

describe('accessToken 持久化', () => {
  it('setAccessToken 写入 localStorage，清空时移除', () => {
    localStorage.clear()
    setAccessToken('token-abc')
    expect(localStorage.getItem('access_token')).toBe('token-abc')
    setAccessToken(null)
    expect(localStorage.getItem('access_token')).toBeNull()
  })
})
