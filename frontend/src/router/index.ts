import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/daily-summary/:date',
      name: 'daily-summary',
      component: () => import('@/views/DailySummaryView.vue')
    },
    {
      path: '/detections/by-hour/:date/:hour',
      name: 'detections-by-hour',
      component: () => import('@/views/DetectionsByHourView.vue')
    },
    {
      path: '/detections/by-species/:scientificName/:date',
      name: 'detections-by-species',
      component: () => import('@/views/DetectionsBySpeciesView.vue')
    }
  ]
})

export default router
