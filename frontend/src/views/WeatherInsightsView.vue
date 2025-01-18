<template>
  <div class="container mx-auto px-4 py-8">
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-gray-900">Weather Analysis</h1>
      <p class="mt-2 text-gray-600">Discover patterns between bird activity and weather conditions</p>
    </div>

    <!-- Current Weather Card -->
    <div class="bg-white rounded-lg shadow-sm overflow-hidden mb-8">
      <div class="px-6 py-4 border-b border-gray-200">
        <h2 class="text-lg font-medium text-gray-900">Current Weather</h2>
      </div>
      <div class="p-6">
        <div v-if="loadingWeather" class="flex justify-center items-center h-24">
          <svg class="animate-spin h-8 w-8 text-primary-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </div>
        <div v-else-if="currentWeather" class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div class="text-center">
            <div class="text-sm text-gray-500">Temperature</div>
            <div class="mt-1 text-xl font-semibold">{{ currentWeather.temperature }}°C</div>
            <div class="text-sm text-gray-500">Feels like {{ currentWeather.feels_like }}°C</div>
          </div>
          <div class="text-center">
            <div class="text-sm text-gray-500">Wind</div>
            <div class="mt-1 text-xl font-semibold">{{ currentWeather.wind_speed }} m/s</div>
            <div class="text-sm text-gray-500">Direction {{ currentWeather.wind_direction }}°</div>
          </div>
          <div class="text-center">
            <div class="text-sm text-gray-500">Conditions</div>
            <div class="mt-1 text-xl font-semibold capitalize">{{ currentWeather.weather_condition }}</div>
            <div class="text-sm text-gray-500">{{ currentWeather.cloud_cover }}% cloud cover</div>
          </div>
          <div class="text-center">
            <div class="text-sm text-gray-500">Humidity</div>
            <div class="mt-1 text-xl font-semibold">{{ currentWeather.humidity }}%</div>
            <div class="text-sm text-gray-500">Pressure {{ currentWeather.pressure }} hPa</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Weather Pattern Insights -->
    <WeatherPatternInsights />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import WeatherPatternInsights from '@/components/WeatherPatternInsights.vue'

interface CurrentWeather {
  temperature: number
  feels_like: number
  humidity: number
  pressure: number
  wind_speed: number
  wind_direction: number
  precipitation: number
  cloud_cover: number
  visibility: number
  weather_condition: string
  timestamp: string
}

const currentWeather = ref<CurrentWeather | null>(null)
const loadingWeather = ref(true)

const fetchCurrentWeather = async () => {
  try {
    loadingWeather.value = true
    const response = await axios.get('/api/weather/current')
    currentWeather.value = response.data
  } catch (error) {
    console.error('Failed to fetch current weather:', error)
  } finally {
    loadingWeather.value = false
  }
}

onMounted(() => {
  fetchCurrentWeather()
  // Refresh weather data every 5 minutes
  setInterval(fetchCurrentWeather, 5 * 60 * 1000)
})
</script>
