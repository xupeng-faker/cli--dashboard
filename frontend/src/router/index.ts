import { createRouter, createWebHistory } from 'vue-router'

import ScreenPage from '@/pages/ScreenPage.vue'

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [{ path: '/', name: 'screen', component: ScreenPage }],
})
