<template>
  <div class="container mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold mb-8">Recent Bird Detections</h1>
    
    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-12">
      <p class="text-red-600">{{ error }}</p>
      <button 
        @click="fetchDetections"
        class="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
      >
        Retry
      </button>
    </div>

    <!-- No Detections -->
    <div v-else-if="!detections.length" class="text-center py-12 text-gray-500">
      No detections found
    </div>

    <!-- Detection Grid -->
    <BirdImageGrid 
      v-else
      :detections="detections"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useDetectionStore } from '@/stores/detection'
import BirdImageGrid from '@/components/BirdImageGrid.vue'
import type { Detection } from '@/types/detection'

const detectionStore = useDetectionStore()
const loading = computed(() => detectionStore.isLoading)
const error = computed(() => detectionStore.getError)
const detections = computed(() => detectionStore.getRecentDetections)

const fetchDetections = async () => {
  await detectionStore.fetchRecentDetections('10')
}

onMounted(fetchDetections)
</script>
