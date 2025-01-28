<template>
  <div>
    <!-- Header -->
    <div class="px-6 py-4 border-b border-gray-200">
      <h2 class="text-lg font-medium text-gray-900">Recent Detections</h2>
    </div>

    <!-- Detection List -->
    <div class="overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Detection Time
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Common Name
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Confidence
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Image Quality
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Image
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="detection in recentDetections" :key="detection.id" class="hover:bg-gray-50">
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
              {{ formatDateTime(detection.detection_time) }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="text-sm font-medium text-gray-900">{{ detection.common_name }}</div>
              <div class="text-sm text-gray-500">{{ detection.scientific_name }}</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="flex items-center">
                <div 
                  class="h-2 w-16 bg-gray-200 rounded-full overflow-hidden"
                  role="progressbar"
                  :aria-valuenow="detection.score * 100"
                  aria-valuemin="0"
                  aria-valuemax="100"
                >
                  <div 
                    class="h-full bg-primary-600 transition-all duration-500"
                    :style="{ width: `${detection.score * 100}%` }"
                  ></div>
                </div>
                <span class="ml-2 text-sm text-gray-700">{{ (detection.score * 100).toFixed(0) }}%</span>
              </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="flex items-center">
                <div 
                  class="h-2 w-16 bg-gray-200 rounded-full overflow-hidden"
                  role="progressbar"
                  :aria-valuenow="detection.visibility_score * 100"
                  aria-valuemin="0"
                  aria-valuemax="100"
                >
                  <div 
                    class="h-full"
                    :class="{
                      'bg-green-600': detection.visibility_score >= 0.7,
                      'bg-yellow-500': detection.visibility_score >= 0.4 && detection.visibility_score < 0.7,
                      'bg-red-500': detection.visibility_score < 0.4
                    }"
                    :style="{ width: `${detection.visibility_score * 100}%` }"
                  ></div>
                </div>
                <span class="ml-2 text-sm text-gray-700">{{ (detection.visibility_score * 100).toFixed(0) }}%</span>
                <span v-if="detection.enhancement_status === 'completed'" 
                      class="ml-2 text-xs text-green-600">
                  Enhanced
                </span>
              </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="flex items-center space-x-4">
                <div class="relative group">
                  <img 
                    :src="detection.enhanced_path || `/frigate/${detection.frigate_event}/snapshot.jpg`" 
                    alt="Bird Detection"
                    class="h-32 w-32 object-cover rounded-lg shadow-sm transform transition duration-200 group-hover:scale-105"
                    @error="handleImageError"
                  />
                  <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-10 transition-opacity duration-200 rounded-lg"></div>
                  <div v-if="detection.enhancement_status === 'completed'" 
                       class="absolute top-2 right-2 bg-green-500 text-white text-xs px-2 py-1 rounded-full opacity-75">
                    Enhanced
                  </div>
                </div>
                <!-- View button -->
                <button 
                  @click="openModal(detection)"
                  class="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                  View
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
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
import { ref, onMounted } from 'vue'
import ImageModal from './ImageModal.vue'
import type { Detection } from '@/types/detection'

// Props
defineProps<{
  recentDetections: Detection[]
}>()

// State
const isModalOpen = ref(false)
const selectedDetection = ref<Detection | null>(null)

// Lifecycle
onMounted(() => {
  console.log('RecentDetections component mounted')
})

// Methods
const formatDateTime = (dateTime: string) => {
  const date = new Date(dateTime + 'Z')
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: 'numeric',
    hour12: true,
    timeZoneName: 'short'
  }).format(date)
}

const openModal = (detection: Detection) => {
  console.log('Opening modal for detection:', detection)
  selectedDetection.value = detection
  isModalOpen.value = true
  console.log('Modal state:', { isModalOpen: isModalOpen.value, selectedDetection: selectedDetection.value })
}

const closeModal = () => {
  console.log('Closing modal')
  isModalOpen.value = false
  selectedDetection.value = null
}

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  if (img.src.includes('/api/enhanced/')) {
    img.src = img.src.replace('/api/enhanced/', '/frigate/')
  }
}
</script>
