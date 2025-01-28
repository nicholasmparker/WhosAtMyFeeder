<template>
  <div class="py-6 px-4">
    <!-- Gallery Grid -->
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
                :src="detection.enhanced_path || `/api/enhanced/${detection.frigate_event}/snapshot.jpg`"
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
            <h3 class="text-sm font-medium text-gray-900 truncate mb-3">{{ detection.common_name }}</h3>
            
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
    </div>

    <!-- Image Modal -->
    <ImageModal
      v-if="isModalOpen"
      :show="isModalOpen"
      :detection="selectedDetection"
      @close="closeModal"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ImageModal from './ImageModal.vue'

import type { Detection } from '@/types/detection'

// Props
const props = defineProps<{
  detections: Detection[]
}>()

// State
const isModalOpen = ref(false)
const selectedDetection = ref<Detection | null>(null)

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

const openModal = (detection: Detection) => {
  selectedDetection.value = detection
  isModalOpen.value = true
}

const closeModal = () => {
  isModalOpen.value = false
  selectedDetection.value = null
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
