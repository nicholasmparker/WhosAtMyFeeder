<template>
  <div>
    <!-- Header -->
    <div class="px-6 py-4 border-b border-gray-200">
      <h2 class="text-lg font-medium text-gray-900">Recent Detections</h2>
    </div>

    <!-- Detection Grid -->
    <div class="p-6">
      <BirdImageGrid :detections="recentDetections" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import BirdImageGrid from './BirdImageGrid.vue'
import type { Detection } from '@/types/detection'

// Props
defineProps<{
  recentDetections: Detection[]
}>()

// Lifecycle
onMounted(() => {
  console.log('RecentDetections component mounted')
})
</script>
