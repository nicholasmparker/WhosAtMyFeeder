<template>
  <div class="bg-white rounded-lg shadow-sm overflow-hidden">
    <div class="px-6 py-4 border-b border-gray-200">
      <h2 class="text-lg font-medium text-gray-900">Species Frequency</h2>
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
import { BarChart } from 'echarts/charts'
import type { BarSeriesOption } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DataZoomComponent,
  ToolboxComponent,
  LegendComponent
} from 'echarts/components'
import type {
  TitleComponentOption,
  TooltipComponentOption,
  GridComponentOption,
  DataZoomComponentOption,
  ToolboxComponentOption,
  LegendComponentOption
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

// Utility imports
import { format } from 'date-fns'
import axios from 'axios'

// Register ECharts components
use([
  CanvasRenderer,
  BarChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DataZoomComponent,
  ToolboxComponent,
  LegendComponent
])

interface SpeciesCount {
  common_name: string
  count: number
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
const speciesCounts = ref<SpeciesCount[]>([])

// Color palette for species
const speciesColors = [
  '#ef4444', // Red (Cardinal)
  '#3b82f6', // Blue (Blue Jay)
  '#10b981', // Green (Chickadee)
  '#f59e0b', // Yellow (Nuthatch)
  '#8b5cf6'  // Purple (Other)
]

const chartOption = computed(() => {
  const seriesData: BarSeriesOption = {
    name: 'Detections',
    type: 'bar',
    data: speciesCounts.value.map((s, index) => ({
      value: s.count,
      itemStyle: {
        color: speciesColors[index]
      }
    })),
    emphasis: {
      focus: 'series'
    }
  }

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params: any) => {
        const data = params[0]
        return `${data.name}<br/>Detections: ${data.value}`
      }
    },
    grid: {
      left: '5%',
      right: '5%',
      bottom: '15%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: speciesCounts.value.map(s => s.common_name),
      axisLabel: {
        interval: 0,
        rotate: 45,
        overflow: 'truncate',
        fontSize: 12,
        color: '#374151'
      },
      axisTick: {
        alignWithLabel: true
      }
    },
    yAxis: {
      type: 'value',
      name: 'Detections',
      minInterval: 1,
      max: 3,
      splitLine: {
        show: true,
        lineStyle: {
          type: 'dashed',
          color: '#e5e7eb'
        }
      },
      axisLabel: {
        color: '#374151'
      }
    },
    series: [seriesData],
    dataZoom: [
      {
        type: 'slider',
        show: true,
        start: 0,
        end: 100,
        height: 20
      }
    ],
    toolbox: {
      feature: {
        saveAsImage: { title: 'Save' }
      }
    }
  }
})

const fetchData = async () => {
  try {
    loading.value = true
    // Get today's data
    const today = format(new Date(), 'yyyy-MM-dd')
    console.log('Fetching data for today:', today)
    
    const response = await axios.get<DailySummaryResponse>(`/api/detections/daily-summary/${today}`)
    console.log('Response:', JSON.stringify(response.data, null, 2))
    
    // Convert response to species counts
    const speciesMap = new Map<string, { common_name: string; count: number }>()
    
    Object.values(response.data).forEach((species) => {
      speciesMap.set(species.scientific_name, {
        common_name: species.common_name,
        count: species.total_detections
      })
    })
    
    // Convert to array and sort by count
    speciesCounts.value = Array.from(speciesMap.values())
      .sort((a, b) => b.count - a.count)
    
    console.log('Processed species counts:', JSON.stringify(speciesCounts.value, null, 2))
    
  } catch (error) {
    console.error('Failed to fetch species data:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>
