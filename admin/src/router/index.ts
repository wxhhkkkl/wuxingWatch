import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory('/admin/'),
  routes: [
    { path: '/login', name: 'login', component: () => import('../pages/Login.vue') },
    { path: '/', name: 'members', component: () => import('../pages/Members.vue') },
    { path: '/members/:id', name: 'member-detail', component: () => import('../pages/MemberDetail.vue') },
    { path: '/books', name: 'admin-books', component: () => import('../pages/AdminBooks.vue') },
    { path: '/books/:id', name: 'admin-book-edit', component: () => import('../pages/AdminBookEdit.vue') },
    { path: '/categories', name: 'admin-categories', component: () => import('../pages/AdminCategories.vue') },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.name !== 'login' && !auth.isAdmin) {
    return { name: 'login' }
  }
  if (to.name === 'login' && auth.isAdmin) {
    return { name: 'members' }
  }
})

export default router
