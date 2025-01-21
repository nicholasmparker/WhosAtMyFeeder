<template>
  <div class="container mx-auto px-4 py-8 space-y-6">
    <!-- Weather Correlation Chart -->
    <WeatherCorrelationChart 
      :date="date" 
      :hour="hour" 
      class="max-w-full"
    />

    <div class="bg-white shadow-sm rounded-lg overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-200">
        <h2 class="text-lg font-medium text-gray-900">Detections for {{ formattedDateTime }}</h2>
      </div>

      <div v-if="!loading" class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Time
              </th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Common Name
              </th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Confidence
              </th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Image
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="detection in detections" :key="detection.id" class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ formatTime(detection.detection_time) }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">{{ detection.common_name }}</div>
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
                <div class="relative group">
                  <img 
                    :src="detection.enhancement_status === 'completed' ? `/api/enhanced/${detection.frigate_event}/thumbnail.jpg` : `/frigate/${detection.frigate_event}/thumbnail.jpg`"
                    alt="Detection thumbnail"
                    class="h-16 w-16 object-cover rounded-lg shadow-sm cursor-pointer transform transition duration-200 group-hover:scale-105"
                    @click.prevent="showSnapshot(detection)"
                    @error="handleImageError"
                  />
                  <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-10 transition-opacity duration-200 rounded-lg"></div>
                  <div v-if="detection.enhancement_status === 'completed'" 
                       class="absolute top-0 right-0 bg-green-500 text-white text-xs px-1 py-0.5 rounded-bl opacity-75">
                    Enhanced
                  </div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="flex justify-center items-center p-8">
        <svg class="animate-spin h-8 w-8 text-primary-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      </div>
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
                <div class="flex justify-between items-center px-6 py-3 border-b border-gray-200">
                  <div>
                    <h3 class="text-lg font-medium text-gray-900">
                      {{ selectedDetection?.common_name }}
                    </h3>
                    <div v-if="selectedDetection?.enhancement_status === 'completed'" class="mt-1 text-sm text-gray-500">
                      <span class="text-green-600">Enhanced Image</span>
                    </div>
                  </div>
                  <div class="flex items-center space-x-4">
                    <div v-if="selectedDetection?.enhancement_status === 'completed'" class="flex items-center">
                      <button
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
                  <img 
                    :src="currentSnapshotUrl" 
                    alt="Detection Snapshot" 
                    class="w-full h-auto rounded-lg shadow-lg"
                    @error="handleImageError"
                  />
                  <div class="mt-4 flex justify-between items-center">
                    <div class="text-sm text-gray-500">
                      Detected at {{ formatTime(selectedDetection?.detection_time || '') }}
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
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import WeatherCorrelationChart from '@/components/WeatherCorrelationChart.vue'

interface Detection {
  id: number
  detection_time: string
  common_name: string
  score: number
  frigate_event: string
  enhancement_status?: 'pending' | 'completed' | 'failed'
}

const route = useRoute()
const loading = ref(true)
const detections = ref<Detection[]>([])
const currentSnapshotUrl = ref('')
const currentClipUrl = ref('')
const isModalOpen = ref(false)
const selectedDetection = ref<Detection | null>(null)
const showEnhanced = ref(false)

const currentDate = ref<string>('')
const currentHour = ref<string>('')

const getInitialDate = async (): Promise<string> => {
  const routeDate = Array.isArray(route.params.date) 
    ? route.params.date[0] 
    : (route.params.date as string | undefined)
  
  if (routeDate) {
    return routeDate
  }

  try {
    const response = await axios.get('/api/earliest-detection-date')
    return response.data.date || new Date().toISOString().split('T')[0]
  } catch (error) {
    console.error('Error fetching earliest date:', error)
    return new Date().toISOString().split('T')[0]
  }
}

const getCurrentHour = (): string => {
  const routeHour = Array.isArray(route.params.hour)
    ? route.params.hour[0]
    : (route.params.hour as string | undefined)
  
  if (routeHour) {
    return routeHour
  }
  
  // Get current hour in local timezone
  const now = new Date()
  const localHour = now.getHours()
  return localHour.toString().padStart(2, '0')
}

const date = computed(() => currentDate.value)
const hour = computed(() => currentHour.value)

const formattedDateTime = computed(() => {
  const dateObj = new Date(date.value)
  dateObj.setHours(parseInt(hour.value))
  return dateObj.toLocaleString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: 'numeric',
    hour12: true
  })
})

const formatTime = (dateTime: string) => {
  // Parse UTC date string and create a Date object
  const date = new Date(dateTime + 'Z')
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
    timeZoneName: 'short'
  })
}

const getImageUrl = (detection: Detection, isSnapshot = false) => {
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

const showSnapshot = (detection: Detection) => {
  selectedDetection.value = detection
  showEnhanced.value = detection.enhancement_status === 'completed'
  currentSnapshotUrl.value = getImageUrl(detection, true)
  currentClipUrl.value = `/frigate/${detection.frigate_event}/clip.mp4`
  isModalOpen.value = true
}

const toggleEnhanced = () => {
  showEnhanced.value = !showEnhanced.value
  if (selectedDetection.value) {
    currentSnapshotUrl.value = getImageUrl(
      selectedDetection.value,
      true
    )
  }
}

const closeModal = () => {
  isModalOpen.value = false
  selectedDetection.value = null
  showEnhanced.value = false
  currentSnapshotUrl.value = ''
  currentClipUrl.value = ''
}

onMounted(async () => {
  try {
    currentDate.value = await getInitialDate()
    currentHour.value = getCurrentHour()
    const response = await axios.get(`/api/detections/by-hour/${currentDate.value}/${currentHour.value}`)
    detections.value = response.data
  } catch (error) {
    console.error('Failed to fetch detections:', error)
  } finally {
    loading.value = false
  }
})
</script>
