import type { RouteLocationNormalized } from 'vue-router'
import { useAuthStore } from '../stores/auth'

/** 全局登录守卫：除 /login 外所有页面均需登录，未登录跳转登录页并记录原路径（登录后回跳）。 */
export function requireAuth(to: RouteLocationNormalized) {
  if (to.name !== 'login' && !useAuthStore().isLoggedIn) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  return true
}
