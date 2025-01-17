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
import { ref, computed, onMounted } from 'vue'
import { defineComponent } from 'vue'
import VChart, { THEME_KEY } from 'vue-echarts'
import type { ComponentPublicInstance } from 'vue'
import * as echarts from 'echarts/core'
import { HeatmapChart } from 'echarts/charts'
import type { HeatmapSeriesOption } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  VisualMapComponent,
  DataZoomComponent,
  ToolboxComponent
} from 'echarts/components'
import type {
  TitleComponentOption,
  TooltipComponentOption,
  GridComponentOption,
  VisualMapComponentOption,
  DataZoomComponentOption,
  ToolboxComponentOption
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

type ECOption = echarts.ComposeOption<
  | HeatmapSeriesOption
  | TitleComponentOption
  | TooltipComponentOption
  | GridComponentOption
  | VisualMapComponentOption
  | DataZoomComponentOption
  | ToolboxComponentOption
>
import { format, parseISO, getHours, getDay } from 'date-fns'
import axios from 'axios'

// Register ECharts components
echarts.use([
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

const loading = ref(true)
const detections = ref<Detection[]>([])

// Initialize data matrix for the heatmap (24 hours x 7 days)
const activityData = computed(() => {
  const data: number[][] = Array(24).fill(0).map(() => Array(7).fill(0))
  
  detections.value.forEach(detection => {
    const date = parseISO(detection.detection_time)
    const hour = getHours(date)
    const day = getDay(date)
    data[hour][day]++
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
      const day = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][params.data[0]]
      const hour = params.data[1]
      const value = params.data[2]
      return `${day} ${hour}:00<br>Detections: ${value}`
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
    data: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
    splitArea: {
      show: true
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
    // Get the last 7 days of data
    const endDate = new Date()
    const startDate = new Date()
    startDate.setDate(startDate.getDate() - 7)
    
    const dates = Array(7).fill(0).map((_, i) => {
      const date = new Date(startDate)
      date.setDate(date.getDate() + i)
      return format(date, 'yyyy-MM-dd')
    })
    
    // Fetch data for each day
    const responses = await Promise.all(
      dates.map(date => 
        axios.get(`/api/detections/daily-summary/${date}`)
      )
    )
    
    // Combine all detections
    const allDetections: Detection[] = []
    responses.forEach(response => {
      Object.values(response.data).forEach((species: any) => {
        species.detections?.forEach((detection: Detection) => {
          allDetections.push(detection)
        })
      })
    })
    
    detections.value = allDetections
  } catch (error) {
    console.error('Failed to fetch detection data:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>
