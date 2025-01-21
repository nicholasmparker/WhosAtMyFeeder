<template>
  <div>
    <div class="px-6 py-4 border-b border-gray-200">
      <h2 class="text-lg font-medium text-gray-900">Recent Detections</h2>
    </div>
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
              <div v-if="detection.quality_score !== undefined" class="flex items-center">
                <div 
                  class="h-2 w-16 bg-gray-200 rounded-full overflow-hidden"
                  role="progressbar"
                  :aria-valuenow="detection.quality_score * 100"
                  aria-valuemin="0"
                  aria-valuemax="100"
                >
                  <div 
                    class="h-full"
                    :class="{
                      'bg-green-600': detection.quality_score >= 0.7,
                      'bg-yellow-500': detection.quality_score >= 0.4 && detection.quality_score < 0.7,
                      'bg-red-500': detection.quality_score < 0.4
                    }"
                    :style="{ width: `${detection.quality_score * 100}%` }"
                  ></div>
                </div>
                <span class="ml-2 text-sm text-gray-700">{{ (detection.quality_score * 100).toFixed(0) }}%</span>
                <span v-if="detection.enhancement_status === 'completed'" 
                      class="ml-2 text-xs text-green-600">
                  Enhanced
                </span>
              </div>
              <div v-else class="text-sm text-gray-500">
                Analyzing...
              </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="relative group">
                <img 
                  :src="detection.enhancement_status === 'completed' ? `/api/enhanced/${detection.frigate_event}/thumbnail.jpg` : `/frigate/${detection.frigate_event}/thumbnail.jpg`" 
                  alt="Bird Detection"
                  class="h-32 w-32 object-cover rounded-lg shadow-sm cursor-zoom-in transform transition duration-200 group-hover:scale-105"
                  @click.prevent="showSnapshot(detection)"
                  @error="handleImageError"
                />
                <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-10 transition-opacity duration-200 rounded-lg"></div>
                <div v-if="detection.enhancement_status === 'completed'" 
                     class="absolute top-2 right-2 bg-green-500 text-white text-xs px-2 py-1 rounded-full opacity-75">
                  Enhanced
                </div>
                <div class="absolute bottom-2 right-2 bg-gray-800 text-white text-xs px-2 py-1 rounded-full opacity-75">
                  Click to Zoom
                </div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
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
                        :src="getSnapshotUrl(selectedDetection.frigate_event, false)" 
                        alt="Original Bird Detection Snapshot" 
                        class="w-full h-auto rounded-lg shadow-lg"
                      />
                    </div>
                    <div>
                      <div class="text-sm font-medium text-gray-500 mb-2">Enhanced</div>
                      <img 
                        :src="getSnapshotUrl(selectedDetection.frigate_event, true)" 
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
                      Detected at {{ formatDateTime(selectedDetection?.detection_time || '') }}
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

<script setup lang="ts">
import { ref } from 'vue'

interface Detection {
  id: number
  detection_time: string
  common_name: string
  scientific_name: string
  score: number
  frigate_event: string
  quality_score?: number
  enhancement_status?: 'pending' | 'completed' | 'failed'
  quality_improvement?: number
}

interface Props {
  recentDetections: Detection[]
}

const props = defineProps<Props>()
const currentSnapshotUrl = ref('')
const currentClipUrl = ref('')
const isModalOpen = ref(false)
const selectedDetection = ref<Detection | null>(null)
const showEnhanced = ref(false)
const isComparisonView = ref(false)

const formatDateTime = (dateTime: string) => {
  // Parse the UTC date string and create a Date object
  const date = new Date(dateTime + 'Z') // Append Z to ensure UTC parsing
  
  // Format using browser's timezone
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

const getSnapshotUrl = (frigateEvent: string, enhanced = false) => {
  return enhanced 
    ? `/api/enhanced/${frigateEvent}/snapshot.jpg`
    : `/frigate/${frigateEvent}/snapshot.jpg`
}

const showSnapshot = (detection: Detection) => {
  if (!detection) return
  
  selectedDetection.value = detection
  showEnhanced.value = detection.enhancement_status === 'completed'
  isComparisonView.value = false
  
  currentSnapshotUrl.value = getSnapshotUrl(
    detection.frigate_event, 
    showEnhanced.value
  )
  currentClipUrl.value = `/frigate/${detection.frigate_event}/clip.mp4`
  isModalOpen.value = true
}


const toggleEnhanced = () => {
  showEnhanced.value = !showEnhanced.value
  if (selectedDetection.value) {
    currentSnapshotUrl.value = getSnapshotUrl(
      selectedDetection.value.frigate_event,
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

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  console.error('Image failed to load:', img.src)
  // Fall back to original image if enhanced fails
  if (img.src.includes('/api/enhanced/')) {
    img.src = img.src.replace('/api/enhanced/', '/frigate/')
  }
}
</script>
