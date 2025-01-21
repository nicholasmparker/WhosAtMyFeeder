<template>
  <div class="container mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold mb-8">Special Detections</h1>
    
    <!-- Type Filter -->
    <div class="mb-8">
      <div class="flex space-x-4">
        <button 
          v-for="type in ['all', 'rare', 'quality', 'behavior']" 
          :key="type"
          @click="currentType = type"
          :class="[
            'px-4 py-2 rounded-lg font-medium',
            currentType === type 
              ? 'bg-blue-600 text-white' 
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          ]"
        >
          {{ type.charAt(0).toUpperCase() + type.slice(1) }}
        </button>
      </div>
    </div>

    <!-- Detection Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div 
        v-for="detection in filteredDetections" 
        :key="detection.id"
        class="bg-white rounded-lg shadow-lg overflow-hidden"
      >
        <!-- Image -->
        <div class="relative w-full" style="padding-top: 75%;">
          <img 
            :src="detection.enhancement_status === 'completed' ? `/api/enhanced/${detection.frigate_event}/snapshot.jpg` : `/frigate/${detection.frigate_event}/snapshot.jpg`"
            :alt="detection.common_name"
            class="absolute top-0 left-0 w-full h-full object-cover"
          />
          <div class="absolute top-2 right-2 flex space-x-1">
            <!-- Highlight Type Badge -->
            <span 
              :class="[
                'px-1.5 py-0.5 rounded text-xs font-medium',
                {
                  'bg-purple-500 text-white': detection.highlight_type === 'rare',
                  'bg-green-500 text-white': detection.highlight_type === 'quality',
                  'bg-yellow-500 text-white': detection.highlight_type === 'behavior'
                }
              ]"
            >
              {{ detection.highlight_type }}
            </span>
            <!-- Score Badge -->
            <span class="px-1.5 py-0.5 rounded bg-blue-500 text-white text-xs font-medium">
              {{ Math.round(detection.score * 100) }}%
            </span>
          </div>
        </div>

        <!-- Details -->
        <div class="p-4">
          <div class="flex justify-between items-start mb-2">
            <div>
              <h3 class="text-lg font-bold text-gray-900">{{ detection.common_name }}</h3>
              <p class="text-sm text-gray-600">{{ detection.display_name }}</p>
            </div>
            <!-- Featured Star -->
            <button 
              @click="toggleFeatured(detection)"
              :class="[
                'text-2xl focus:outline-none',
                detection.featured_status ? 'text-yellow-400' : 'text-gray-300 hover:text-yellow-400'
              ]"
            >
              ★
            </button>
          </div>

          <!-- Metrics -->
          <div class="grid grid-cols-2 gap-2 mb-4 text-sm">
            <div v-if="detection.clarity_score" class="text-gray-600">
              Clarity: {{ Math.round(detection.clarity_score * 100) }}%
            </div>
            <div v-if="detection.composition_score" class="text-gray-600">
              Composition: {{ Math.round(detection.composition_score * 100) }}%
            </div>
          </div>

          <!-- Timestamp -->
          <p class="text-sm text-gray-500 mb-4">
            {{ new Date(detection.detection_time).toLocaleString() }}
          </p>

          <!-- Community Voting -->
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <button 
                @click="vote(detection, true)"
                class="text-gray-500 hover:text-blue-500 focus:outline-none"
              >
                <i class="fas fa-thumbs-up"></i>
              </button>
              <span class="text-gray-600">{{ detection.community_votes }}</span>
              <button 
                @click="vote(detection, false)"
                class="text-gray-500 hover:text-red-500 focus:outline-none"
              >
                <i class="fas fa-thumbs-down"></i>
              </button>
            </div>
            <!-- View Full Button -->
            <button 
              @click="viewFullImage(detection)"
              class="text-blue-600 hover:text-blue-800 text-sm font-medium focus:outline-none"
            >
              View Full
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <!-- No Results -->
    <div 
      v-if="!loading && filteredDetections.length === 0" 
      class="text-center py-12 text-gray-500"
    >
      No special detections found
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted } from 'vue'

export default defineComponent({
  name: 'SpecialDetectionsView',

  setup() {
    const detections = ref<any[]>([])
    const loading = ref(true)
    const currentType = ref('all')

    const filteredDetections = computed(() => {
      if (currentType.value === 'all') {
        return detections.value
      }
      return detections.value.filter(d => d.highlight_type === currentType.value)
    })

    const fetchDetections = async () => {
      try {
        loading.value = true
        if (currentType.value === 'all') {
          const response = await fetch('/api/special-detections/recent')
          detections.value = await response.json()
        } else {
          const response = await fetch(`/api/special-detections/by-type/${currentType.value}`)
          detections.value = await response.json()
        }
      } catch (error) {
        console.error('Error fetching special detections:', error)
      } finally {
        loading.value = false
      }
    }

    const vote = async (detection: any, increment: boolean) => {
      try {
        const response = await fetch(`/api/special-detections/${detection.id}/vote`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ increment })
        })
        if (response.ok) {
          detection.community_votes += increment ? 1 : -1
        }
      } catch (error) {
        console.error('Error voting:', error)
      }
    }

    const toggleFeatured = async (detection: any) => {
      try {
        const response = await fetch(`/api/special-detections/${detection.id}/featured`, {
          method: 'POST'
        })
        if (response.ok) {
          const result = await response.json()
          detection.featured_status = result.featured
        }
      } catch (error) {
        console.error('Error toggling featured status:', error)
      }
    }

    const viewFullImage = (detection: any) => {
      const imageUrl = detection.enhancement_status === 'completed' 
        ? `/api/enhanced/${detection.frigate_event}/snapshot.jpg` 
        : `/frigate/${detection.frigate_event}/snapshot.jpg`
      window.open(imageUrl, '_blank')
    }

    onMounted(fetchDetections)

    return {
      detections,
      loading,
      currentType,
      filteredDetections,
      vote,
      toggleFeatured,
      viewFullImage
    }
  }
})
</script>
