<template>
  <div class="space-y-6">
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
                    :src="getThumbnailUrl(detection.frigate_event)"
                    alt="Detection thumbnail"
                    class="h-16 w-16 object-cover rounded-lg shadow-sm cursor-pointer transform transition duration-200 group-hover:scale-105"
                    @click="showSnapshot(detection)"
                  />
                  <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-10 transition-opacity duration-200 rounded-lg"></div>
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
      class="fixed inset-0 z-50 overflow-y-auto"
      @click.self="closeModal"
    >
      <div class="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:p-0">
        <div class="fixed inset-0 transition-opacity" aria-hidden="true">
          <div class="absolute inset-0 bg-gray-500 opacity-75"></div>
        </div>

        <div 
          class="inline-block bg-white rounded-lg overflow-hidden shadow-xl transform transition-all sm:my-8 sm:max-w-4xl w-full"
          @click.stop
        >
          <div class="bg-white">
            <div class="sm:flex sm:items-start">
              <div class="w-full">
                <div class="flex justify-between items-center px-6 py-3 border-b border-gray-200">
                  <h3 class="text-lg font-medium text-gray-900">
                    Detection Snapshot
                  </h3>
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
                <div class="px-6 py-4">
                  <img 
                    :src="currentSnapshotUrl" 
                    alt="Detection Snapshot" 
                    class="w-full h-auto rounded-lg shadow-lg"
                  />
                  <div class="mt-4 flex justify-end">
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

interface Detection {
  id: number
  detection_time: string
  common_name: string
  score: number
  frigate_event: string
}

const route = useRoute()
const loading = ref(true)
const detections = ref<Detection[]>([])
const currentSnapshotUrl = ref('')
const currentClipUrl = ref('')
const isModalOpen = ref(false)

const formattedDateTime = computed(() => {
  const date = new Date(route.params.date as string)
  const hour = parseInt(route.params.hour as string)
  date.setHours(hour)
  return date.toLocaleString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: 'numeric',
    hour12: true
  })
})

const formatTime = (dateTime: string) => {
  const date = new Date(dateTime)
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true
  })
}

const getThumbnailUrl = (frigateEvent: string) => {
  return `/frigate/${frigateEvent}/thumbnail.jpg`
}

const showSnapshot = (detection: Detection) => {
  currentSnapshotUrl.value = `/frigate/${detection.frigate_event}/snapshot.jpg`
  currentClipUrl.value = `/frigate/${detection.frigate_event}/clip.mp4`
  isModalOpen.value = true
}

const closeModal = () => {
  isModalOpen.value = false
  currentSnapshotUrl.value = ''
  currentClipUrl.value = ''
}

onMounted(async () => {
  try {
    const response = await axios.get(`/api/detections/by-hour/${route.params.date}/${route.params.hour}`)
    detections.value = response.data
  } catch (error) {
    console.error('Failed to fetch detections:', error)
  } finally {
    loading.value = false
  }
})
</script>
