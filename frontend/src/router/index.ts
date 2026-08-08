import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../pages/Home.vue'),
    },
    {
      path: '/result',
      name: 'result',
      component: () => import('../pages/ChartResult.vue'),
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../pages/Login.vue'),
    },
    {
      path: '/records',
      name: 'records',
      component: () => import('../pages/Records.vue'),
    },
    {
      path: '/records/:id',
      name: 'record-detail',
      component: () => import('../pages/RecordDetail.vue'),
    },
  ],
})

export default router
