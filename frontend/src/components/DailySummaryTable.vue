<template>
  <div class="overflow-x-auto">
    <table class="min-w-full divide-y divide-gray-200">
      <thead class="bg-gray-50">
        <tr>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            Common Name
          </th>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            Total
          </th>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            Activity Timeline
          </th>
        </tr>
      </thead>
      <tbody class="bg-white divide-y divide-gray-200">
        <tr v-for="species in dailySummaryArray" :key="species.scientific_name" class="hover:bg-gray-50">
          <td class="px-6 py-4 whitespace-nowrap">
            <router-link 
              :to="{ 
                name: 'detections-by-species', 
                params: { 
                  scientificName: species.scientific_name,
                  date: currentDate
                }
              }"
              class="text-sm font-medium text-gray-900 hover:text-primary-600"
            >
              {{ species.common_name }}
            </router-link>
            <div class="text-sm text-gray-500">{{ species.scientific_name }}</div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap">
            <div class="text-sm font-medium text-gray-900">{{ species.total_detections }}</div>
            <div class="text-xs text-gray-500">detections today</div>
          </td>
          <td class="px-6 py-4">
            <div class="flex space-x-1">
              <div 
                v-for="hour in 24" 
                :key="hour-1"
                class="relative group"
              >
                <div 
                  class="w-4 h-8 rounded transition-colors duration-200"
                  :class="[
                    getActivityColor(species.hourly_detections[hour-1] || 0),
                    hour-1 === currentHour ? 'ring-2 ring-primary-500' : ''
                  ]"
                  :title="`${hour-1}:00 - ${species.hourly_detections[hour-1] || 0} detections`"
                >
                  <router-link 
                    :to="{ name: 'detections-by-hour', params: { date: currentDate, hour: hour-1 }}"
                    class="absolute inset-0"
                  >
                    <span class="sr-only">View detections for hour {{ hour-1 }}</span>
                  </router-link>
                </div>
                <!-- Tooltip -->
                <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap pointer-events-none">
                  {{ hour-1 }}:00 - {{ species.hourly_detections[hour-1] || 0 }} detections
                </div>
              </div>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface DailySummary {
  [key: string]: {
    common_name: string
    scientific_name: string
    total_detections: number
    hourly_detections: number[]
  }
}

interface Props {
  dailySummary: DailySummary
  currentHour: number
}

const props = defineProps<Props>()

const currentDate = computed(() => {
  return new Date().toISOString().split('T')[0]
})

const dailySummaryArray = computed(() => {
  return Object.values(props.dailySummary).sort((a, b) => {
    return b.total_detections - a.total_detections
  })
})

const getActivityColor = (count: number) => {
  if (count === 0) return 'bg-gray-100'
  if (count <= 2) return 'bg-primary-100'
  if (count <= 5) return 'bg-primary-300'
  if (count <= 10) return 'bg-primary-500'
  return 'bg-primary-700'
}
</script>
