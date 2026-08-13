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

describe('accessToken 持久化', () => {
  it('setAccessToken 写入 localStorage，清空时移除', () => {
    localStorage.clear()
    setAccessToken('token-abc')
    expect(localStorage.getItem('access_token')).toBe('token-abc')
    setAccessToken(null)
    expect(localStorage.getItem('access_token')).toBeNull()
  })
})
