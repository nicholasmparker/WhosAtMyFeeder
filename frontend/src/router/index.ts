import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import DailySummaryView from '@/views/DailySummaryView.vue'
import DetectionsByHourView from '@/views/DetectionsByHourView.vue'
import DetectionsBySpeciesView from '@/views/DetectionsBySpeciesView.vue'
import WeatherInsightsView from '@/views/WeatherInsightsView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/daily-summary/:date?',
      name: 'daily-summary',
      component: DailySummaryView,
      props: true
    },
    {
      path: '/detections-by-hour/:date?/:hour?',
      name: 'detections-by-hour',
      component: DetectionsByHourView,
      props: true
    },
    {
      path: '/detections-by-species',
      name: 'detections-by-species',
      component: DetectionsBySpeciesView
    },
    {
      path: '/weather-insights',
      name: 'weather-insights',
      component: WeatherInsightsView
    }
  ]
})

export default router
