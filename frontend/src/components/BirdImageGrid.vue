<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 gap-8">
    <div v-for="detection in detections" 
         :key="detection.id" 
         class="relative group cursor-pointer"
         @click="openModal(detection)">
      <!-- Image Card -->
      <div class="bg-white rounded-lg shadow-md overflow-hidden transform transition-all duration-300 hover:scale-102 hover:shadow-lg">
        <!-- Image Container -->
        <div class="relative aspect-[4/3] bg-gray-100 rounded-t-lg overflow-hidden">
          <!-- Enhanced Image with Original on Hover -->
          <div v-if="detection.enhancement_status === 'completed'" class="w-full h-full relative group/image">
            <!-- Enhanced Image (Default View) -->
            <img 
              :src="`/api/enhanced/${detection.frigate_event}/snapshot.jpg`"
              :alt="`Enhanced ${detection.common_name}`"
              class="w-full h-full object-cover absolute inset-0 transition-opacity duration-300 group-hover/image:opacity-0"
              @error="handleImageError"
            />
            <!-- Original Image (Show on Hover) -->
            <img 
              :src="`/frigate/${detection.frigate_event}/snapshot.jpg`"
              :alt="`Original ${detection.common_name}`"
              class="w-full h-full object-contain absolute inset-0 opacity-0 group-hover/image:opacity-100 transition-opacity duration-300"
              @error="handleImageError"
            />

            <!-- Enhancement Badge -->
            <div class="absolute top-2 right-2 bg-green-500 text-white text-xs px-2.5 py-1.5 rounded-full shadow-sm">
              Enhanced
            </div>
            
            <!-- Compare Indicator -->
            <div class="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/70 to-transparent py-4 px-3 transform translate-y-full group-hover/image:translate-y-0 transition-transform duration-300">
              <div class="flex items-center justify-center space-x-2 text-white">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                <span class="text-sm font-medium">Viewing Original</span>
              </div>
            </div>
          </div>

          <!-- Special Detection Badge -->
          <div v-if="detection.is_special" 
               class="absolute top-2 left-2 px-2.5 py-1.5 rounded-full shadow-sm text-xs font-medium"
               :class="{
                 'bg-purple-500 text-white': detection.highlight_type === 'rare',
                 'bg-blue-500 text-white': detection.highlight_type === 'quality',
                 'bg-green-500 text-white': detection.highlight_type === 'behavior'
               }">
            {{ formatHighlightType(detection.highlight_type) }}
          </div>

          <!-- Time and Metadata Overlay -->
          <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
            <div class="absolute bottom-0 left-0 right-0 p-3">
              <p class="text-sm font-medium text-white drop-shadow-lg">{{ formatDateTime(detection.detection_time) }}</p>
            </div>
          </div>
        </div>

        <!-- Info Bar -->
        <div class="px-4 py-3 bg-white">
          <!-- Species Name -->
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-sm font-medium text-gray-900 truncate">{{ detection.common_name }}</h3>
            <span v-if="detection.is_special && detection.special_score" 
                  class="text-xs font-medium"
                  :class="{
                    'text-purple-600': detection.highlight_type === 'rare',
                    'text-blue-600': detection.highlight_type === 'quality',
                    'text-green-600': detection.highlight_type === 'behavior'
                  }">
              {{ (detection.special_score * 100).toFixed(0) }}%
            </span>
          </div>
          
          <!-- Scores -->
          <div class="space-y-2">
            <!-- Confidence Score -->
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Match</span>
              <div class="flex items-center space-x-2">
                <div class="h-2 w-20 bg-gray-100 rounded-full overflow-hidden">
                  <div 
                    class="h-full bg-blue-500"
                    :style="{ width: `${detection.score * 100}%` }"
                  ></div>
                </div>
                <span class="text-xs font-medium text-gray-700">{{ (detection.score * 100).toFixed(0) }}%</span>
              </div>
            </div>

            <!-- Quality Score -->
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">Quality</span>
              <div class="flex items-center space-x-2">
                <div class="h-2 w-20 bg-gray-100 rounded-full overflow-hidden">
                  <div 
                    class="h-full"
                    :class="{
                      'bg-green-500': detection.visibility_score >= 0.7,
                      'bg-yellow-500': detection.visibility_score >= 0.4 && detection.visibility_score < 0.7,
                      'bg-red-500': detection.visibility_score < 0.4
                    }"
                    :style="{ width: `${detection.visibility_score * 100}%` }"
                  ></div>
                </div>
                <span class="text-xs font-medium text-gray-700">{{ (detection.visibility_score * 100).toFixed(0) }}%</span>
                <span v-if="detection.quality_improvement > 0" 
                      class="text-xs text-green-600">
                  +{{ (detection.quality_improvement * 100).toFixed(0) }}%
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Enhanced Image Modal -->
    <div v-if="isModalOpen && selectedDetection"
         class="fixed inset-0 z-50 flex items-center justify-center">
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black opacity-50" @click="closeModal"></div>
      
      <!-- Modal -->
      <div class="relative bg-white rounded-lg shadow-xl max-w-6xl w-full mx-4">
        <!-- Header -->
        <div class="flex justify-between items-center p-4 border-b">
          <div>
            <h3 class="text-xl font-semibold">{{ selectedDetection.common_name }}</h3>
            <p class="text-sm text-gray-600">{{ selectedDetection.scientific_name }}</p>
          </div>
          <div class="flex items-center space-x-4">
            <!-- View Toggle -->
            <div v-if="selectedDetection.enhancement_status === 'completed'" class="flex items-center">
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
            <button @click="closeModal" class="text-gray-500 hover:text-gray-700">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
        
        <!-- Content -->
        <div class="p-6">
          <!-- Comparison View -->
          <div v-if="isComparisonView && selectedDetection.enhancement_status === 'completed'" class="grid grid-cols-2 gap-4">
            <div>
              <div class="text-sm font-medium text-gray-500 mb-2">Original</div>
              <img 
                :src="`/frigate/${selectedDetection.frigate_event}/snapshot.jpg`"
                :alt="`Original ${selectedDetection.common_name}`"
                class="w-full h-auto rounded-lg shadow-lg"
                @error="handleImageError"
              />
            </div>
            <div>
              <div class="text-sm font-medium text-gray-500 mb-2">Enhanced</div>
              <img 
                :src="`/api/enhanced/${selectedDetection.frigate_event}/snapshot.jpg`"
                :alt="`Enhanced ${selectedDetection.common_name}`"
                class="w-full h-auto rounded-lg shadow-lg"
                @error="handleImageError"
              />
            </div>
          </div>
          
          <!-- Single View -->
          <div v-else>
            <img 
              :src="currentImageUrl"
              :alt="selectedDetection.common_name"
              class="w-full h-auto rounded-lg shadow-lg"
              @error="handleImageError"
            />
          </div>

          <!-- Details -->
          <div class="mt-4 space-y-2">
            <p class="text-sm text-gray-600">
              Detected at {{ formatDateTime(selectedDetection.detection_time) }}
            </p>
            <div class="flex space-x-4">
              <p class="text-sm text-gray-600">
                Clarity: {{ (selectedDetection.clarity_score * 100).toFixed(0) }}%
              </p>
              <p class="text-sm text-gray-600">
                Composition: {{ (selectedDetection.composition_score * 100).toFixed(0) }}%
              </p>
              <p v-if="selectedDetection.quality_improvement > 0" class="text-sm text-green-600">
                Quality Improvement: +{{ (selectedDetection.quality_improvement * 100).toFixed(0) }}%
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Detection } from '@/types/detection'

// Props
const props = defineProps<{
  detections: Detection[]
}>()

// State
const isModalOpen = ref(false)
const selectedDetection = ref<Detection | null>(null)
const showEnhanced = ref(false)
const isComparisonView = ref(false)

// Computed
const currentImageUrl = computed(() => {
  if (!selectedDetection.value) return ''
  
  const isEnhanced = showEnhanced.value && selectedDetection.value.enhancement_status === 'completed'
  return isEnhanced
    ? `/api/enhanced/${selectedDetection.value.frigate_event}/snapshot.jpg`
    : `/frigate/${selectedDetection.value.frigate_event}/snapshot.jpg`
})

// Methods
const formatDateTime = (dateTime: string) => {
  const date = new Date(dateTime + 'Z')
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: 'numeric',
    hour12: true
  }).format(date)
}

const formatHighlightType = (type?: string) => {
  if (!type) return ''
  return type.charAt(0).toUpperCase() + type.slice(1)
}

const openModal = (detection: Detection) => {
  selectedDetection.value = detection
  showEnhanced.value = detection.enhancement_status === 'completed'
  isComparisonView.value = false
  isModalOpen.value = true
}

const closeModal = () => {
  isModalOpen.value = false
  selectedDetection.value = null
  showEnhanced.value = false
  isComparisonView.value = false
}

const toggleEnhanced = () => {
  showEnhanced.value = !showEnhanced.value
}

const toggleComparisonView = () => {
  isComparisonView.value = !isComparisonView.value
  showEnhanced.value = false
}

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  if (img.src.includes('/api/enhanced/')) {
    // If enhanced image fails, fall back to original
    img.src = img.src.replace('/api/enhanced/', '/frigate/')
  } else if (img.src.includes('snapshot.jpg')) {
    // If snapshot fails, try thumbnail
    img.src = img.src.replace('snapshot.jpg', 'thumbnail.jpg')
  }
}
</script>

<style scoped>
.scale-102 {
  --tw-scale-x: 1.02;
  --tw-scale-y: 1.02;
}
</style>
