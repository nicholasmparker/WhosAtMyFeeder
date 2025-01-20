import { defineStore } from 'pinia'
import api from '@/api/axios'

interface Detection {
  id: number
  detection_time: string
  common_name: string
  scientific_name: string
  score: number
  frigate_event: string
}

interface DailySummary {
  [key: string]: {
    common_name: string
    scientific_name: string
    total_detections: number
    hourly_detections: number[]
  }
}

interface DetectionState {
  recentDetections: Detection[]
  dailySummary: DailySummary
  loading: boolean
  error: string | null
  hasData: boolean
}

export const useDetectionStore = defineStore('detection', {
  state: (): DetectionState => ({
    recentDetections: [],
    dailySummary: {},
    loading: false,
    error: null,
    hasData: false
  }),

  actions: {
    async fetchRecentDetections() {
      this.loading = true
      try {
        const response = await api.get('/api/detections/recent')
        this.recentDetections = response.data
        this.hasData = response.data.length > 0
        this.error = null
      } catch (error: any) {
        // Only set error if it's not a "no table" error
        if (!error.response?.data?.includes('no such table')) {
          this.error = 'Failed to fetch recent detections'
          console.error('Error fetching recent detections:', error)
        }
        this.hasData = false
      } finally {
        this.loading = false
      }
    },

    async fetchDailySummary(date: string) {
      this.loading = true
      try {
        const response = await api.get(`/api/detections/daily-summary/${date}`)
        this.dailySummary = response.data
        this.hasData = Object.keys(response.data).length > 0
        this.error = null
      } catch (error: any) {
        // Only set error if it's not a "no table" error
        if (!error.response?.data?.includes('no such table')) {
          this.error = 'Failed to fetch daily summary'
          console.error('Error fetching daily summary:', error)
        }
        this.hasData = false
      } finally {
        this.loading = false
      }
    }
  },

  getters: {
    getRecentDetections: (state): Detection[] => state.recentDetections,
    getDailySummary: (state): DailySummary => state.dailySummary,
    isLoading: (state): boolean => state.loading,
    getError: (state): string | null => state.error,
    getHasData: (state): boolean => state.hasData
  }
})
