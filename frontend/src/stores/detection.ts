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
  dailySummary: DailySummary
  loading: boolean
  error: string | null
  hasRecentDetections: boolean
  hasDailySummary: boolean
}

export const useDetectionStore = defineStore('detection', {
  state: (): DetectionState => ({
    recentDetections: [],
    dailySummary: {},
    loading: false,
    error: null,
    hasRecentDetections: false,
    hasDailySummary: false
  }),

  actions: {
    async fetchRecentDetections() {
      this.loading = true
      try {
        const response = await api.get('/api/detections/recent')
        if (response.data === null || response.data === undefined) {
          this.recentDetections = []
          this.hasRecentDetections = false
        } else {
          // Map response data to Detection interface
          this.recentDetections = response.data.map((detection: any) => ({
            ...detection,
            visibility_score: detection.visibility_score || detection.quality_score || 0,
            clarity_score: detection.clarity_score || 0,
            composition_score: detection.composition_score || 0,
            quality_improvement: detection.quality_improvement || 0,
            enhanced_path: detection.enhanced_path || null,
            enhanced_thumbnail_path: detection.enhanced_thumbnail_path || null
          }))
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
    getDailySummary: (state): DailySummary => state.dailySummary,
    isLoading: (state): boolean => state.loading,
    getError: (state): string | null => state.error,
    hasData: (state): boolean => state.hasRecentDetections || state.hasDailySummary
  }
})
