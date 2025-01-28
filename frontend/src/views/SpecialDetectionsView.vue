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

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <!-- No Results -->
    <div 
      v-else-if="!filteredDetections.length" 
      class="text-center py-12 text-gray-500"
    >
      No special detections found
    </div>

    <!-- Detection Grid -->
    <BirdImageGrid 
      v-else
      :detections="filteredDetections"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import BirdImageGrid from '@/components/BirdImageGrid.vue'
import type { Detection } from '@/types/detection'

const detections = ref<Detection[]>([])
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
    const url = currentType.value === 'all'
      ? '/api/special-detections/recent'
      : `/api/special-detections/by-type/${currentType.value}`
      
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    detections.value = await response.json()
  } catch (error) {
    console.error('Error fetching special detections:', error)
  } finally {
    loading.value = false
  }
}

// Watch for type changes to refetch data
watch(currentType, fetchDetections)

onMounted(fetchDetections)
</script>
