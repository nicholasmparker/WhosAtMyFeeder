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
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DataZoomComponent,
  ToolboxComponent,
  LegendComponent,
  MarkAreaComponent
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

interface DailyData {
  date: string
  total: number
  bySpecies: {
    [key: string]: number
  }
}

const loading = ref(true)
const dailyData = ref<DailyData[]>([])
const topSpecies = ref<string[]>([])

const chartOption = computed(() => {
  // Get dates for x-axis
  const dates = dailyData.value.map(d => d.date)
  
  // Create series for each top species
  const series = topSpecies.value.map(species => ({
    name: species,
    type: 'line',
    smooth: true,
    symbol: 'circle',
    symbolSize: 8,
    data: dailyData.value.map(d => d.bySpecies[species] || 0),
    emphasis: {
      focus: 'series'
    },
    lineStyle: {
      width: 3
    }
  }))

  // Add total detections series
  series.push({
    name: 'Total Detections',
    type: 'line',
    smooth: true,
    symbol: 'circle',
    symbolSize: 8,
    data: dailyData.value.map(d => d.total),
    emphasis: {
      focus: 'series'
    },
    lineStyle: {
      width: 4,
      type: 'dashed'
    },
    itemStyle: {
      color: '#6b7280' // gray-500
    }
  })

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      type: 'scroll',
      orient: 'horizontal',
      top: 0,
      right: 10,
      data: [...topSpecies.value, 'Total Detections']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates,
      axisLabel: {
        formatter: (value: string) => format(parseISO(value), 'MMM d')
      }
    },
    yAxis: {
      type: 'value',
      name: 'Detections',
      splitLine: {
        show: true,
        lineStyle: {
          type: 'dashed'
        }
      }
    },
    series,
    dataZoom: [
      {
        type: 'slider',
        show: true,
        start: 50,
        end: 100,
        height: 20
      },
      {
        type: 'inside',
        start: 50,
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
    // Get the last 30 days of data
    const endDate = new Date()
    const startDate = new Date()
    startDate.setDate(startDate.getDate() - 30)
    
    const dates = Array(30).fill(0).map((_, i) => {
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
    
    // Process daily data
    const processedData: DailyData[] = dates.map((date, index) => {
      const dayData = responses[index].data
      const bySpecies: { [key: string]: number } = {}
      let total = 0

      Object.values(dayData).forEach((species: any) => {
        bySpecies[species.common_name] = species.total_detections
        total += species.total_detections
      })

      return {
        date,
        total,
        bySpecies
      }
    })

    // Calculate top species by total detections
    const speciesCounts = new Map<string, number>()
    processedData.forEach(day => {
      Object.entries(day.bySpecies).forEach(([species, count]) => {
        speciesCounts.set(species, (speciesCounts.get(species) || 0) + count)
      })
    })

    // Get top 5 species
    topSpecies.value = Array.from(speciesCounts.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([species]) => species)

    dailyData.value = processedData
    
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
