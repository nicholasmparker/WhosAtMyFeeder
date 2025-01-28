<template>
  <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center">
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
        <!-- Images Side by Side -->
        <div class="flex flex-col md:flex-row gap-4">
          <!-- Original Image -->
          <div class="flex-1">
            <h4 class="text-lg font-medium mb-2">Original Image</h4>
            <img :src="originalImageUrl" class="w-full rounded-lg shadow-md" alt="Original detection" />
            <div class="mt-2 text-sm text-gray-600">
              <p>Clarity: {{ Math.round(detection.quality_score * 100) }}%</p>
              <p>Composition: {{ Math.round(detection.composition_score * 100) }}%</p>
              <p>Overall Quality: {{ Math.round(detection.visibility_score * 100) }}%</p>
            </div>
          </div>
          
          <!-- Enhanced Image -->
          <div v-if="hasEnhancedImage" class="flex-1">
            <h4 class="text-lg font-medium mb-2">Enhanced Image</h4>
            <img :src="enhancedImageUrl" class="w-full rounded-lg shadow-md" alt="Enhanced detection" />
            <div class="mt-2 text-sm text-gray-600">
              <p v-if="detection.enhanced_quality_scores">
                Clarity: {{ Math.round(detection.enhanced_quality_scores.clarity * 100) }}%
              </p>
              <p v-if="detection.enhanced_quality_scores">
                Composition: {{ Math.round(detection.enhanced_quality_scores.composition * 100) }}%
              </p>
              <p v-if="detection.enhanced_quality_scores">
                Overall Quality: {{ Math.round(detection.enhanced_quality_scores.overall * 100) }}%
              </p>
              <p v-if="detection.quality_improvement" class="mt-1 text-green-600">
                Quality Improvement: {{ Math.round(detection.quality_improvement * 100) }}%
              </p>
            </div>
          </div>
        </div>
        
        <!-- Detection Details -->
        <div class="mt-6">
          <h4 class="text-lg font-medium mb-2">Detection Details</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <p><span class="font-medium">Time:</span> {{ new Date(detection.detection_time).toLocaleString() }}</p>
            <p><span class="font-medium">Species:</span> {{ detection.common_name }} ({{ detection.display_name }})</p>
            <p><span class="font-medium">Confidence:</span> {{ Math.round(detection.score * 100) }}%</p>
            <p><span class="font-medium">Camera:</span> {{ detection.camera_name }}</p>
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
import { computed } from 'vue'

const props = defineProps<{
  show: boolean
  detection: any
}>()

const emit = defineEmits(['close'])

const close = () => {
  emit('close')
}

const originalImageUrl = computed(() => {
  return `/frigate/${props.detection.frigate_event}/snapshot.jpg`
})

const enhancedImageUrl = computed(() => {
  return `/api/enhanced/${props.detection.frigate_event}/snapshot.jpg`
})

const hasEnhancedImage = computed(() => {
  return props.detection.enhancement_status === 'completed'
})
</script>
