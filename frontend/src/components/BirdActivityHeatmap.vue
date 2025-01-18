<template>
  <div class="bg-white rounded-lg shadow-sm overflow-hidden">
    <div class="px-6 py-4 border-b border-gray-200">
      <h2 class="text-lg font-medium text-gray-900">Bird Activity Patterns</h2>
    </div>
    <div class="p-6">
      <div v-if="loading" class="flex justify-center items-center h-96">
        <svg class="animate-spin h-8 w-8 text-primary-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      </div>
      <v-chart 
        v-else
        class="h-96 w-full"
        :option="chartOption"
        :autoresize="true"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
// Vue imports
import { ref, computed, onMounted } from 'vue'

// ECharts imports
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { HeatmapChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  VisualMapComponent,
  DataZoomComponent,
  ToolboxComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

// Utility imports
import { format, parseISO, getHours } from 'date-fns'
import axios from 'axios'

// Register ECharts components
use([
  CanvasRenderer,
  HeatmapChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  VisualMapComponent,
  DataZoomComponent,
  ToolboxComponent
])

interface Detection {
  detection_time: string
  common_name: string
}

interface DailySummaryResponse {
  [key: string]: {
    common_name: string
    scientific_name: string
    total_detections: number
    hourly_detections: number[]
  }
}

const loading = ref(true)
const detections = ref<Detection[]>([])
const dateList = ref<string[]>([])

// Initialize data matrix for the heatmap (24 hours x 7 days)
const activityData = computed(() => {
  const data: number[][] = Array(24).fill(0).map(() => Array(7).fill(0))
  
  detections.value.forEach(detection => {
    const date = parseISO(detection.detection_time)
    const hour = getHours(date)
    const dateStr = format(date, 'yyyy-MM-dd')
    
    // Find the index of this date in our dates array
    const dayIndex = dateList.value.indexOf(dateStr)
    if (dayIndex !== -1) {
      data[hour][dayIndex]++
    }
  })
  
  // Convert to format expected by ECharts
  return data.flatMap((hourData, hour) => 
    hourData.map((value, day) => [day, hour, value])
  )
})

const chartOption = computed(() => ({
  tooltip: {
    position: 'top',
    formatter: (params: any) => {
      const days = ['6 days ago', '5 days ago', '4 days ago', '3 days ago', '2 days ago', 'Yesterday', 'Today']
      const day = days[params.data[0]]
      const hour = params.data[1]
      const value = params.data[2]
      return `${day} at ${hour}:00<br>Detections: ${value}`
    }
  },
  grid: {
    top: '10%',
    left: '10%',
    right: '10%',
    bottom: '15%'
  },
  xAxis: {
    type: 'category',
    data: ['6 days ago', '5 days ago', '4 days ago', '3 days ago', '2 days ago', 'Yesterday', 'Today'],
    splitArea: {
      show: true
    },
    axisLabel: {
      interval: 0,
      rotate: 30
    }
  },
  yAxis: {
    type: 'category',
    data: Array(24).fill(0).map((_, i) => `${i}:00`),
    splitArea: {
      show: true
    }
  },
  visualMap: {
    min: 0,
    max: 10,
    calculable: true,
    orient: 'horizontal',
    left: 'center',
    bottom: '0%',
    inRange: {
      color: ['#f3f4f6', '#93c5fd', '#3b82f6', '#1d4ed8']
    }
  },
  series: [{
    name: 'Bird Activity',
    type: 'heatmap',
    data: activityData.value,
    label: {
      show: true,
      formatter: (params: any) => params.data[2] || ''
    },
    emphasis: {
      itemStyle: {
        shadowBlur: 10,
        shadowColor: 'rgba(0, 0, 0, 0.5)'
      }
    }
  }],
  toolbox: {
    feature: {
      saveAsImage: { title: 'Save' },
      dataZoom: { title: { zoom: 'Zoom', back: 'Reset Zoom' } },
    }
  }
}))

const fetchData = async () => {
  try {
    loading.value = true
    // Get today and the previous 6 days
    const today = new Date()
    dateList.value = Array(7).fill(0).map((_, i) => {
      const date = new Date(today)
      date.setDate(date.getDate() - (6 - i)) // Start 6 days ago, end with today
      return format(date, 'yyyy-MM-dd')
    })
    
    console.log('Requesting data for dates:', JSON.stringify(dateList.value, null, 2))
    
    // Fetch data for each day
    const responses = await Promise.all(
      dateList.value.map(async (date: string) => {
        console.log(`Fetching data for date: ${date}`)
        try {
          const response = await axios.get<DailySummaryResponse>(`/api/detections/daily-summary/${date}`)
          console.log(`Response for ${date}:`, JSON.stringify(response.data, null, 2))
          return response
        } catch (error) {
          if (axios.isAxiosError(error)) {
            console.error(`Error fetching data for ${date}:`, error.response?.data || error.message)
          } else {
            console.error(`Error fetching data for ${date}:`, error)
          }
          throw error
        }
      })
    )
    
    console.log('All responses received')
    
    // Process daily data
    const processedDetections: Detection[] = []
    
    dateList.value.forEach((date: string, dayIndex: number) => {
      const dayData = responses[dayIndex].data
      console.log(`Processing data for ${date}:`, JSON.stringify(dayData, null, 2))
      
      if (Object.keys(dayData).length === 0) {
        console.log(`No data for ${date}`)
        return
      }
      
      Object.values(dayData).forEach((species) => {
        if (!species.hourly_detections) {
          console.warn(`Missing hourly_detections for species:`, JSON.stringify(species, null, 2))
          return
        }
        
        species.hourly_detections.forEach((count: number, hour: number) => {
          if (count > 0) {
            // Create a detection entry for each count
            for (let i = 0; i < count; i++) {
              processedDetections.push({
                detection_time: `${date}T${hour.toString().padStart(2, '0')}:00:00`,
                common_name: species.common_name
              })
            }
          }
        })
      })
    })
    
    console.log('Processed detections:', JSON.stringify(processedDetections.slice(0, 5), null, 2), `(total: ${processedDetections.length})`)
    
    detections.value = processedDetections
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error('Failed to fetch detection data:', error.response?.data || error.message)
    } else {
      console.error('Failed to fetch detection data:', error)
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>
