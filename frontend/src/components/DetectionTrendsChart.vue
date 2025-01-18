<template>
  <div class="bg-white rounded-lg shadow-sm overflow-hidden">
    <div class="px-6 py-4 border-b border-gray-200">
      <h2 class="text-lg font-medium text-gray-900">Detection Trends</h2>
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
import { LineChart } from 'echarts/charts'
import type { LineSeriesOption } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DataZoomComponent,
  ToolboxComponent,
  LegendComponent,
  MarkAreaComponent
} from 'echarts/components'
import type {
  TitleComponentOption,
  TooltipComponentOption,
  GridComponentOption,
  DataZoomComponentOption,
  ToolboxComponentOption,
  LegendComponentOption,
  MarkAreaComponentOption
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

// Utility imports
import { format, parseISO } from 'date-fns'
import axios from 'axios'

// Register ECharts components
use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DataZoomComponent,
  ToolboxComponent,
  LegendComponent,
  MarkAreaComponent
])

interface HourlyData {
  hour: number
  total: number
  bySpecies: {
    [key: string]: number
  }
}

interface DailySummaryResponse {
  [key: string]: {
    common_name: string
    scientific_name: string
    total_detections: number
    hourly_detections: number[]
  }
}

interface Species {
  scientific_name: string
  common_name: string
}

const loading = ref(true)
const hourlyData = ref<HourlyData[]>([])
const topSpecies = ref<Species[]>([])

// Color palette for species
const speciesColors = [
  '#ef4444', // Red (Cardinal)
  '#3b82f6', // Blue (Blue Jay)
  '#10b981', // Green (Chickadee)
  '#f59e0b', // Yellow (Nuthatch)
  '#8b5cf6'  // Purple (Other)
]

const chartOption = computed(() => {
  // Get hours for x-axis (0-23)
  const hours = Array.from({ length: 24 }, (_, i) => i)
  
  // Create series for each top species
  const seriesData: LineSeriesOption[] = topSpecies.value.map((species, index) => ({
    name: species.common_name,
    type: 'line',
    smooth: true,
    symbol: 'circle',
    symbolSize: 8,
    data: hours.map(hour => {
      const hourData = hourlyData.value.find(d => d.hour === hour)
      return hourData ? hourData.bySpecies[species.scientific_name] || 0 : 0
    }),
    emphasis: {
      focus: 'series'
    },
    lineStyle: {
      width: 3,
      type: 'solid'
    },
    itemStyle: {
      color: speciesColors[index]
    },
    markArea: {
      silent: true,
      itemStyle: {
        color: 'rgba(0, 0, 0, 0.1)'
      },
      data: [[{
        name: 'Night',
        xAxis: '0'
      }, {
        xAxis: '6'
      }], [{
        name: 'Night',
        xAxis: '18'
      }, {
        xAxis: '23'
      }]]
    }
  }))

  // Add total detections series
  const totalSeries: LineSeriesOption = {
    name: 'Total Detections',
    type: 'line',
    smooth: true,
    symbol: 'circle',
    symbolSize: 8,
    data: hours.map(hour => {
      const hourData = hourlyData.value.find(d => d.hour === hour)
      return hourData ? hourData.total : 0
    }),
    emphasis: {
      focus: 'series'
    },
    lineStyle: {
      width: 4,
      type: 'dashed'
    },
    itemStyle: {
      color: '#6b7280'
    }
  }

  seriesData.push(totalSeries)

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: (params: any) => {
        let result = `${params[0].axisValue}:00<br/>`
        // Only show species with detections
        params.forEach((param: any) => {
          if (param.value > 0) {
            result += `${param.marker} ${param.seriesName}: ${param.value}<br/>`
          }
        })
        return result
      }
    },
    legend: {
      type: 'scroll',
      orient: 'horizontal',
      top: 0,
      right: 10,
      textStyle: {
        fontSize: 12,
        color: '#374151'
      },
      data: [...topSpecies.value.map(s => s.common_name), 'Total Detections']
    },
    grid: {
      left: '5%',
      right: '5%',
      bottom: '15%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: hours.map(hour => `${hour}:00`),
      axisLabel: {
        interval: 2,
        fontSize: 11,
        color: '#374151'
      },
      splitLine: {
        show: true,
        lineStyle: {
          type: 'dashed',
          color: '#e5e7eb',
          opacity: 0.5
        }
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
          color: '#e5e7eb',
          opacity: 0.5
        }
      },
      axisLabel: {
        color: '#374151'
      }
    },
    series: seriesData,
    dataZoom: [
      {
        type: 'slider',
        show: true,
        start: 0,
        end: 100,
        height: 20,
        borderColor: '#e5e7eb'
      },
      {
        type: 'inside',
        start: 0,
        end: 100
      }
    ],
    toolbox: {
      feature: {
        saveAsImage: { title: 'Save' },
        dataZoom: { title: { zoom: 'Zoom', back: 'Reset Zoom' } },
        restore: { title: 'Reset' }
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
    
    // Process hourly data and track species totals
    const speciesMap = new Map<string, { common_name: string; total: number }>()
    const processedData: HourlyData[] = []
    
    // Initialize hourly data for each species
    Object.values(response.data).forEach((species) => {
      species.hourly_detections.forEach((count, hour) => {
        if (count > 0) {
          const hourData = processedData.find(d => d.hour === hour) || {
            hour,
            total: 0,
            bySpecies: {}
          }
          
          hourData.bySpecies[species.scientific_name] = count
          hourData.total += count
          
          if (!processedData.find(d => d.hour === hour)) {
            processedData.push(hourData)
          }
          
          // Track species totals
          const existingData = speciesMap.get(species.scientific_name) || {
            common_name: species.common_name,
            total: 0
          }
          existingData.total += count
          speciesMap.set(species.scientific_name, existingData)
        }
      })
    })
    
    // Sort by hour
    processedData.sort((a, b) => a.hour - b.hour)
    
    // Get top species with common names
    topSpecies.value = Array.from(speciesMap.entries())
      .sort((a, b) => b[1].total - a[1].total)
      .slice(0, 5)
      .map(([scientific_name, data]) => ({
        scientific_name,
        common_name: data.common_name
      }))
    
    hourlyData.value = processedData
    console.log('Processed hourly data:', JSON.stringify(processedData, null, 2))
    
  } catch (error) {
    console.error('Failed to fetch trend data:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>
