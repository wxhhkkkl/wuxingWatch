import { createRouter, createWebHistory } from 'vue-router'
import { requireAuth } from './guard'

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
      path: '/shichen',
      name: 'shichen',
      component: () => import('../pages/ShichenDetail.vue'),
    },
    {
      path: '/strength',
      name: 'strength',
      component: () => import('../pages/StrengthDetail.vue'),
    },
    // ---------- 大运引擎2（014-dayun-engine2）----------
    // 按教师八步流程（R30 起含天干五合）独立算出的另一套大运旺度；单独入口，**不做对比页**（裁定④）
    {
      path: '/dayun2',
      name: 'dayun2-detail',
      component: () => import('../pages/Dayun2Detail.vue'),
    },
    // ---------- 子平格局喜忌（015-ziping-geju-xiyong）----------
    {
      path: '/geju',
      name: 'geju-detail',
      component: () => import('../pages/GeJuDetail.vue'),
    },
    {
      path: '/geju-dayun',
      name: 'geju-dayun-detail',
      component: () => import('../pages/GeJuDayunDetail.vue'),
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
    {
      path: '/me',
      name: 'me',
      component: () => import('../pages/Me.vue'),
    },
    // ---------- 阅读模块（006-reading-module） ----------
    {
      path: '/reading/books',
      name: 'reading-books',
      component: () => import('../pages/ReadingBooks.vue'),
    },
    {
      path: '/reading/books/:id',
      name: 'reading-book',
      component: () => import('../pages/ReadingBook.vue'),
    },
    {
      path: '/reading/books/:bookId/chapters/:chapterId',
      name: 'reading-chapter',
      component: () => import('../pages/ReadingChapter.vue'),
    },
  ],
})

router.beforeEach(requireAuth)

export default router
