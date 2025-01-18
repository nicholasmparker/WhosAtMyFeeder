<template>
  <div class="bg-white rounded-lg shadow-sm overflow-hidden">
    <div class="px-6 py-4 border-b border-gray-200">
      <h2 class="text-lg font-medium text-gray-900">Weather Patterns & Insights</h2>
    </div>
    <div class="p-6">
      <div v-if="loading" class="flex justify-center items-center h-96">
        <svg class="animate-spin h-8 w-8 text-primary-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      </div>
      <div v-else>
        <!-- Weather Insights -->
        <div class="mb-8">
          <h3 class="text-md font-medium text-gray-700 mb-4">Key Insights</h3>
          <div class="space-y-4">
            <div v-for="(insight, index) in insights" :key="index" 
                 class="bg-blue-50 p-4 rounded-lg border border-blue-100">
              <p class="text-blue-800">{{ insight }}</p>
            </div>
          </div>
        </div>

        <!-- Weather Pattern Details -->
        <div class="mb-8">
          <h3 class="text-md font-medium text-gray-700 mb-4">Activity by Weather Condition</h3>
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th class="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Condition
                  </th>
                  <th class="px-6 py-3 bg-gray-50 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Temperature
                  </th>
                  <th class="px-6 py-3 bg-gray-50 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Wind Speed
                  </th>
                  <th class="px-6 py-3 bg-gray-50 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Activity
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="pattern in patterns" :key="pattern.weather_condition">
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {{ pattern.weather_condition }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                    {{ pattern.avg_temp }}°{{ temperatureUnit }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                    {{ pattern.avg_wind }} {{ windSpeedUnit }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                    {{ pattern.activity_percentage }}%
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Species Filter -->
        <div class="mt-4">
          <label class="block text-sm font-medium text-gray-700">Filter by Species</label>
          <select v-model="selectedSpecies" 
                  @change="fetchData"
                  class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md">
            <option value="">All Species</option>
            <option v-for="species in availableSpecies" 
                    :key="species.scientific_name" 
                    :value="species.scientific_name">
              {{ species.common_name }}
            </option>
          </select>
        </div>

        <!-- Time Range Filter -->
        <div class="mt-4">
          <label class="block text-sm font-medium text-gray-700">Analysis Period</label>
          <select v-model="selectedDays" 
                  @change="fetchData"
                  class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md">
            <option :value="7">Last 7 days</option>
            <option :value="30">Last 30 days</option>
            <option :value="90">Last 90 days</option>
          </select>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

interface Species {
  scientific_name: string
  common_name: string
}

interface WeatherPattern {
  weather_condition: string
  avg_temp: number
  avg_wind: number
  total_detections: number
  activity_percentage: number
}

const loading = ref(true)
const patterns = ref<WeatherPattern[]>([])
const insights = ref<string[]>([])
const selectedSpecies = ref('')
const selectedDays = ref(30)
const availableSpecies = ref<Species[]>([])
const units = ref<'imperial' | 'metric'>('imperial') // Default to imperial, will be set from API response

// Computed units based on the system
const temperatureUnit = computed(() => units.value === 'imperial' ? 'F' : 'C')
const windSpeedUnit = computed(() => units.value === 'imperial' ? 'mph' : 'm/s')

const fetchSpecies = async () => {
  try {
    const response = await axios.get('/api/species')
    availableSpecies.value = response.data
  } catch (error) {
    console.error('Failed to fetch species list:', error)
  }
}

const fetchData = async () => {
  try {
    loading.value = true
    const params = {
      species: selectedSpecies.value || undefined,
      days: selectedDays.value
    }
    
    const response = await axios.get('/api/weather/patterns', { params })
    patterns.value = response.data.patterns
    insights.value = response.data.insights
    
  } catch (error) {
    console.error('Failed to fetch weather patterns:', error)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await fetchSpecies()
  await fetchData()
})
</script>
