import { defineStore } from 'pinia'
import api from '@/api/axios'

import type { Detection } from '@/types/detection'

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
  specialDetections: Detection[]
  dailySummary: DailySummary
  loading: boolean
  error: string | null
  hasRecentDetections: boolean
  hasSpecialDetections: boolean
  hasDailySummary: boolean
}

export const useDetectionStore = defineStore('detection', {
  state: (): DetectionState => ({
    recentDetections: [],
    specialDetections: [],
    dailySummary: {},
    loading: false,
    error: null,
    hasRecentDetections: false,
    hasSpecialDetections: false,
    hasDailySummary: false
  }),

  actions: {
    async fetchRecentDetections(limit: string = '5') {
      this.loading = true
      try {
        const response = await api.get('/api/detections/recent', {
          params: { limit }
        })
        if (response.data === null || response.data === undefined) {
          this.recentDetections = []
          this.hasRecentDetections = false
        } else {
          this.recentDetections = response.data
          this.hasRecentDetections = Array.isArray(response.data) && response.data.length > 0
        }
        this.error = null
      } catch (error: any) {
        // Only set error if it's not a "no table" error
        if (!error.response?.data?.includes('no such table')) {
          this.error = 'Failed to fetch recent detections'
          console.error('Error fetching recent detections:', error)
        }
        this.hasRecentDetections = false
      } finally {
        this.loading = false
      }
    },

    async fetchSpecialDetections(type: string = 'all') {
      this.loading = true
      try {
        const url = type === 'all'
          ? '/api/special-detections/recent'
          : `/api/special-detections/by-type/${type}`
          
        const response = await api.get(url)
        if (response.data === null || response.data === undefined) {
          this.specialDetections = []
          this.hasSpecialDetections = false
        } else {
          this.specialDetections = response.data
          this.hasSpecialDetections = Array.isArray(response.data) && response.data.length > 0
        }
        this.error = null
      } catch (error: any) {
        this.error = 'Failed to fetch special detections'
        console.error('Error fetching special detections:', error)
        this.hasSpecialDetections = false
      } finally {
        this.loading = false
      }
    },

    async fetchDailySummary(date: string) {
      this.loading = true
      try {
        const response = await api.get(`/api/detections/daily-summary/${date}`)
        this.dailySummary = response.data
        this.hasDailySummary = Object.keys(response.data || {}).length > 0
        this.error = null
      } catch (error: any) {
        // Only set error if it's not a "no table" error
        if (!error.response?.data?.includes('no such table')) {
          this.error = 'Failed to fetch daily summary'
          console.error('Error fetching daily summary:', error)
        }
        this.hasDailySummary = false
      } finally {
        this.loading = false
      }
    }
  },

  getters: {
    getRecentDetections: (state): Detection[] => state.recentDetections,
    getSpecialDetections: (state): Detection[] => state.specialDetections,
    getDailySummary: (state): DailySummary => state.dailySummary,
    isLoading: (state): boolean => state.loading,
    getError: (state): string | null => state.error,
    hasData: (state): boolean => state.hasRecentDetections || state.hasSpecialDetections || state.hasDailySummary
  }
})
