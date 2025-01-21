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
            :src="detection.enhancement_status === 'completed' ? `/api/enhanced/${detection.frigate_event}/thumbnail.jpg` : `/frigate/${detection.frigate_event}/thumbnail.jpg`"
            :alt="detection.common_name"
            class="absolute top-0 left-0 w-full h-full object-cover"
            @error="handleImageError"
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
              @click.prevent="showSnapshot(detection)"
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

    <!-- Modal for displaying snapshot -->
    <div 
      v-if="isModalOpen"
      class="fixed inset-0 z-[100] overflow-y-auto"
      @click.self="closeModal"
    >
      <div class="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:p-0">
        <div class="fixed inset-0 transition-opacity" aria-hidden="true">
          <div class="absolute inset-0 bg-gray-500 opacity-75"></div>
        </div>

        <div 
          class="inline-block bg-white rounded-lg overflow-hidden shadow-xl transform transition-all sm:my-8 sm:max-w-4xl w-full relative z-[110]"
          @click.stop
        >
          <div class="bg-white">
            <div class="sm:flex sm:items-start">
              <div class="w-full">
                <div class="flex justify-between items-center px-6 py-3 border-b border-gray-200 bg-gray-50">
                  <div>
                    <h3 class="text-lg font-medium text-gray-900">
                      {{ selectedDetection?.common_name }}
                    </h3>
                    <div v-if="selectedDetection?.quality_score !== undefined" class="mt-1 text-sm text-gray-500">
                      Quality Score: {{ (selectedDetection.quality_score * 100).toFixed(0) }}%
                      <span v-if="selectedDetection.quality_improvement" class="text-green-600 ml-2">
                        ({{ selectedDetection.quality_improvement > 0 ? '+' : '' }}{{ (selectedDetection.quality_improvement * 100).toFixed(0) }}% improvement)
                      </span>
                    </div>
                  </div>
                  <div class="flex items-center space-x-4">
                    <div v-if="selectedDetection?.enhancement_status === 'completed'" class="flex items-center">
                      <button
                        @click="toggleComparisonView"
                        class="mr-4 px-4 py-2 text-sm font-medium rounded-md bg-blue-50 text-blue-700 hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <span v-if="isComparisonView">
                          <svg class="inline-block w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                          </svg>
                          Single View
                        </span>
                        <span v-else>
                          <svg class="inline-block w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                          </svg>
                          Compare Views
                        </span>
                      </button>
                      <button
                        v-if="!isComparisonView"
                        @click="toggleEnhanced"
                        class="px-4 py-2 text-sm font-medium rounded-md"
                        :class="showEnhanced ? 'bg-green-50 text-green-700 hover:bg-green-100' : 'bg-gray-50 text-gray-700 hover:bg-gray-100'"
                      >
                        <svg class="inline-block w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path v-if="showEnhanced" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
                          <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        {{ showEnhanced ? 'Show Original' : 'Show Enhanced' }}
                      </button>
                    </div>
                    <button 
                      @click="closeModal"
                      class="text-gray-400 hover:text-gray-500 focus:outline-none"
                    >
                      <span class="sr-only">Close</span>
                      <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </div>
                <div class="px-6 py-4">
                  <div v-if="isComparisonView && selectedDetection?.enhancement_status === 'completed'" class="grid grid-cols-2 gap-4">
                    <div>
                      <div class="text-sm font-medium text-gray-500 mb-2">Original</div>
                      <img 
                        :src="getImageUrl(selectedDetection, false)" 
                        alt="Original Bird Detection Snapshot" 
                        class="w-full h-auto rounded-lg shadow-lg"
                      />
                    </div>
                    <div>
                      <div class="text-sm font-medium text-gray-500 mb-2">Enhanced</div>
                      <img 
                        :src="getImageUrl(selectedDetection, true)" 
                        alt="Enhanced Bird Detection Snapshot" 
                        class="w-full h-auto rounded-lg shadow-lg"
                      />
                    </div>
                  </div>
                  <div v-else>
                    <img 
                      :src="currentSnapshotUrl" 
                      alt="Bird Detection Snapshot" 
                      class="w-full h-auto rounded-lg shadow-lg"
                    />
                  </div>
                  <div class="mt-4 flex justify-between items-center">
                    <div class="text-sm text-gray-500">
                      Detected at {{ new Date(selectedDetection?.detection_time || '').toLocaleString() }}
                    </div>
                    <a 
                      :href="currentClipUrl" 
                      target="_blank"
                      class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                    >
                      <svg class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      View Clip
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
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

    const getImageUrl = (detection: any, isSnapshot = false) => {
      const type = isSnapshot ? 'snapshot' : 'thumbnail'
      return detection.enhancement_status === 'completed'
        ? `/api/enhanced/${detection.frigate_event}/${type}.jpg`
        : `/frigate/${detection.frigate_event}/${type}.jpg`
    }

    const handleImageError = (event: Event) => {
      const img = event.target as HTMLImageElement
      console.error('Image failed to load:', img.src)
      // Fall back to original image if enhanced fails
      if (img.src.includes('/api/enhanced/')) {
        img.src = img.src.replace('/api/enhanced/', '/frigate/')
      }
    }

    const currentSnapshotUrl = ref('')
    const currentClipUrl = ref('')
    const isModalOpen = ref(false)
    const selectedDetection = ref<any>(null)
    const showEnhanced = ref(false)
    const isComparisonView = ref(false)

    const showSnapshot = (detection: any) => {
      if (!detection) return
      
      selectedDetection.value = detection
      showEnhanced.value = detection.enhancement_status === 'completed'
      isComparisonView.value = false
      
      currentSnapshotUrl.value = getImageUrl(detection, true)
      currentClipUrl.value = `/frigate/${detection.frigate_event}/clip.mp4`
      isModalOpen.value = true
    }

    const toggleEnhanced = () => {
      showEnhanced.value = !showEnhanced.value
      if (selectedDetection.value) {
        currentSnapshotUrl.value = getImageUrl(
          selectedDetection.value,
          showEnhanced.value
        )
      }
    }

    const toggleComparisonView = () => {
      isComparisonView.value = !isComparisonView.value
      showEnhanced.value = false
    }

    const closeModal = () => {
      isModalOpen.value = false
      selectedDetection.value = null
      showEnhanced.value = false
      isComparisonView.value = false
    }

    onMounted(fetchDetections)

    return {
      detections,
      loading,
      currentType,
      filteredDetections,
      vote,
      toggleFeatured,
      handleImageError,
      showSnapshot,
      toggleEnhanced,
      toggleComparisonView,
      closeModal,
      isModalOpen,
      selectedDetection,
      showEnhanced,
      isComparisonView,
      currentSnapshotUrl,
      currentClipUrl,
      getImageUrl
    }
  }
})
</script>
