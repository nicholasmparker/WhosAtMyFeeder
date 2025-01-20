<template>
  <div class="bg-white shadow-sm rounded-lg overflow-hidden mb-6">
    <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
      <h2 class="text-lg font-medium text-gray-900">Weather Correlation</h2>
      <div class="flex space-x-4">
        <select 
          v-model="selectedMetric"
          class="block pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
        >
          <option value="temperature">Temperature</option>
          <option value="wind_speed">Wind Speed</option>
          <option value="humidity">Humidity</option>
          <option value="cloud_cover">Cloud Cover</option>
        </select>
      </div>
    </div>

    <div class="p-6">
      <div v-if="loading" class="flex justify-center items-center h-64">
        <svg class="animate-spin h-8 w-8 text-primary-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      </div>
      <div v-else>
        <!-- Chart container -->
        <div ref="chartContainer" class="w-full h-64"></div>

        <!-- Correlation Insight -->
        <div v-if="correlationInsight" class="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-100">
          <p class="text-blue-800">{{ correlationInsight }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'

const props = defineProps<{
  date: string
  hour: string
}>()

const loading = ref(true)
const selectedMetric = ref('temperature')
const chartContainer = ref<HTMLElement | null>(null)
const chart = ref<echarts.ECharts | null>(null)
const correlationInsight = ref('')

interface WeatherCorrelation {
  timestamp: string
  metric_value: number
  detection_count: number
  weather_condition: string
}

const generateTimestamps = (hour: string): string[] => {
  const timestamps: string[] = []
  const baseDate = new Date()
  baseDate.setHours(parseInt(hour), 0, 0, 0)
  
  // Generate timestamps for every 5 minutes in the hour
  for (let minute = 0; minute < 60; minute += 5) {
    const timestamp = new Date(baseDate)
    timestamp.setMinutes(minute)
    timestamps.push(timestamp.toISOString())
  }
  
  return timestamps
}

const fetchCorrelationData = async () => {
  try {
    loading.value = true
    const response = await axios.get('/api/weather/correlation', {
      params: {
        date: props.date,
        hour: props.hour,
        metric: selectedMetric.value
      }
    })
    
    const timestamps = generateTimestamps(props.hour)
    const data: WeatherCorrelation[] = timestamps.map((timestamp, index) => ({
      timestamp,
      metric_value: response.data.correlations[0]?.metric_value || 0,
      detection_count: Math.floor(response.data.correlations[0]?.detection_count / 12) || 0, // Distribute detections across the hour
      weather_condition: response.data.correlations[0]?.weather_condition || ''
    }))
    
    correlationInsight.value = response.data.insight

    // Update chart with new data
    updateChart(data)
  } catch (error) {
    console.error('Failed to fetch correlation data:', error)
  } finally {
    loading.value = false
  }
}

const getMetricUnit = (metric: string): string => {
  switch (metric) {
    case 'temperature':
      return '°F'
    case 'wind_speed':
      return 'mph'
    case 'humidity':
    case 'cloud_cover':
      return '%'
    default:
      return ''
  }
}

const updateChart = (data: WeatherCorrelation[]) => {
  if (!data.length) return
  if (!chartContainer.value) return

  if (!chart.value) {
    chart.value = echarts.init(chartContainer.value)
  }

  const metricName = selectedMetric.value.split('_').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ')

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    grid: {
      right: '20%'
    },
    legend: {
      data: [metricName, 'Bird Activity']
    },
    xAxis: {
      type: 'time',
      axisLabel: {
        formatter: (value: number) => {
          const date = new Date(value)
          return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
          })
        }
      }
    },
    yAxis: [
      {
        type: 'value',
        name: metricName,
        position: 'left',
        axisLabel: {
          formatter: `{value}${getMetricUnit(selectedMetric.value)}`
        }
      },
      {
        type: 'value',
        name: 'Bird Activity',
        position: 'right',
        axisLabel: {
          formatter: '{value} detections'
        }
      }
    ],
    series: [
      {
        name: metricName,
        type: 'line',
        smooth: true,
        data: data.map(item => [item.timestamp, item.metric_value]),
        itemStyle: {
          color: '#60A5FA'
        }
      },
      {
        name: 'Bird Activity',
        type: 'bar',
        yAxisIndex: 1,
        data: data.map(item => [item.timestamp, item.detection_count]),
        itemStyle: {
          color: '#34D399'
        }
      }
    ]
  }

  chart.value.setOption(option)
}

// Handle window resize
const handleResize = () => {
  chart.value?.resize()
}

// Watch for changes in selected metric
watch(selectedMetric, () => {
  fetchCorrelationData()
})

onMounted(() => {
  fetchCorrelationData()
  window.addEventListener('resize', handleResize)
})

// Clean up
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart.value?.dispose()
})
</script>
