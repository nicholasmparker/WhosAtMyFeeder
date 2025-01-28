<template>
  <div v-if="show && detection" class="fixed inset-0 z-50 flex items-center justify-center">
    <!-- Backdrop -->
    <div class="absolute inset-0 bg-black opacity-50" @click="close"></div>
    
    <!-- Modal -->
    <div class="relative bg-white rounded-lg shadow-xl max-w-6xl w-full mx-4">
      <!-- Header -->
      <div class="flex justify-between items-center p-4 border-b">
        <h3 class="text-xl font-semibold">Bird Detection Details</h3>
        <button @click="close" class="text-gray-500 hover:text-gray-700">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      
      <!-- Content -->
      <div class="p-6">
        <!-- Special Detection Badge -->
        <div v-if="detection.is_special && detection.special_score" class="mb-4">
          <div class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium"
               :class="{
                 'bg-purple-100 text-purple-800': detection.highlight_type === 'rare',
                 'bg-blue-100 text-blue-800': detection.highlight_type === 'quality',
                 'bg-green-100 text-green-800': detection.highlight_type === 'behavior'
               }">
            <span class="mr-2">{{ formatHighlightType(detection.highlight_type) }} Detection</span>
            <span class="text-xs">{{ Math.round(detection.special_score * 100) }}%</span>
          </div>
        </div>

        <!-- Images Side by Side -->
        <div class="flex flex-col md:flex-row gap-4">
          <!-- Original Image -->
          <div class="flex-1">
            <h4 class="text-lg font-medium mb-2">Original Image</h4>
            <div class="relative aspect-[4/3] bg-gray-100 rounded-lg overflow-hidden">
              <img 
                :src="originalImageUrl" 
                class="w-full h-full object-contain" 
                alt="Original detection" 
                @error="handleImageError" 
              />
            </div>
            <div class="mt-2 text-sm text-gray-600">
              <p>Clarity: {{ Math.round(detection.clarity_score * 100) }}%</p>
              <p>Composition: {{ Math.round(detection.composition_score * 100) }}%</p>
              <p>Overall Quality: {{ Math.round(detection.visibility_score * 100) }}%</p>
            </div>
          </div>
          
          <!-- Enhanced Image -->
          <div v-if="hasEnhancedImage" class="flex-1">
            <h4 class="text-lg font-medium mb-2">Enhanced Image</h4>
            <div class="relative aspect-[4/3] bg-gray-100 rounded-lg overflow-hidden">
              <img 
                :src="`/api/enhanced/${detection.frigate_event}/${useThumbnails ? 'thumbnail' : 'snapshot'}.jpg`"
                class="w-full h-full object-contain" 
                alt="Enhanced detection" 
                @error="handleImageError" 
              />
            </div>
            <div class="mt-2 text-sm text-gray-600">
              <p>Quality Improvement: {{ Math.round(detection.quality_improvement * 100) }}%</p>
            </div>
          </div>
        </div>
        
        <!-- Detection Details -->
        <div class="mt-6">
          <h4 class="text-lg font-medium mb-2">Detection Details</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <p><span class="font-medium">Time:</span> {{ new Date(detection.detection_time).toLocaleString() }}</p>
            <p><span class="font-medium">Species:</span> {{ detection.common_name }} ({{ detection.scientific_name }})</p>
            <p><span class="font-medium">Confidence:</span> {{ Math.round(detection.score * 100) }}%</p>
            <p><span class="font-medium">Camera:</span> {{ detection.camera_name }}</p>
          </div>
        </div>

        <!-- Special Detection Details -->
        <div v-if="detection.is_special && detection.special_score" class="mt-6">
          <h4 class="text-lg font-medium mb-2">Special Detection Details</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <p><span class="font-medium">Type:</span> {{ formatHighlightType(detection.highlight_type) }}</p>
            <p><span class="font-medium">Score:</span> {{ Math.round(detection.special_score * 100) }}%</p>
            <p><span class="font-medium">Community Votes:</span> {{ detection.community_votes || 0 }}</p>
            <p><span class="font-medium">Featured Status:</span> {{ detection.featured_status ? 'Yes' : 'No' }}</p>
          </div>
        </div>
      </div>
      
      <!-- Footer -->
      <div class="flex justify-end p-4 border-t">
        <button @click="close" class="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300">
          Close
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Detection } from '@/types/detection'

const props = defineProps<{
  show: boolean
  detection: Detection | null
}>()

const emit = defineEmits(['close'])

const close = () => {
  emit('close')
}

// Track if we've fallen back to thumbnails
const useThumbnails = ref(false)

const originalImageUrl = computed(() => {
  if (!props.detection) return ''
  return `/frigate/${props.detection.frigate_event}/${useThumbnails.value ? 'thumbnail' : 'snapshot'}.jpg`
})

const hasEnhancedImage = computed(() => {
  return props.detection?.enhancement_status === 'completed'
})

const formatHighlightType = (type?: string) => {
  if (!type) return ''
  return type.charAt(0).toUpperCase() + type.slice(1)
}

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  if (img.src.includes('/api/enhanced/')) {
    // If enhanced image fails, fall back to original
    img.src = img.src.replace('/api/enhanced/', '/frigate/')
  } else if (img.src.includes('snapshot.jpg') && !useThumbnails.value) {
    // If snapshot fails and we haven't tried thumbnails yet, switch to thumbnails
    useThumbnails.value = true
    img.src = img.src.replace('snapshot.jpg', 'thumbnail.jpg')
  }
}
</script>
