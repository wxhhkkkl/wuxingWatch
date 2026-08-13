import { describe, it, expect, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { requireAuth } from '../src/router/guard'
import { useAuthStore } from '../src/stores/auth'

const to = (name: string, fullPath: string) => ({ name, fullPath })

describe('requireAuth', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('allows the login page without authentication', () => {
    expect(requireAuth(to('login', '/login') as never)).toBe(true)
  })

  it('redirects unauthenticated users to /login with the original path', () => {
    const result = requireAuth(to('home', '/records?page=2') as never) as {
      name: string
      query: { redirect: string }
    }
    expect(result.name).toBe('login')
    expect(result.query.redirect).toBe('/records?page=2')
  })

  it('allows navigation when logged in', () => {
    useAuthStore().user = { id: 1, phone: '13800000000' }
    expect(requireAuth(to('home', '/') as never)).toBe(true)
  })
})
