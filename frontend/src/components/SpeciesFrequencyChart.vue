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
import { ref, computed, onMounted } from 'vue'
import VChart from 'vue-echarts'
import * as echarts from 'echarts/core'
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
import { format } from 'date-fns'
import axios from 'axios'

type ECOption = echarts.ComposeOption<
  | BarSeriesOption
  | TitleComponentOption
  | TooltipComponentOption
  | GridComponentOption
  | DataZoomComponentOption
  | ToolboxComponentOption
  | LegendComponentOption
>

// Register ECharts components
echarts.use([
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

const loading = ref(true)
const speciesCounts = ref<SpeciesCount[]>([])

const chartOption = computed<ECOption>(() => ({
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
    left: '3%',
    right: '4%',
    bottom: '15%',
    top: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    data: speciesCounts.value.map(s => s.common_name),
    axisLabel: {
      interval: 0,
      rotate: 45,
      overflow: 'truncate'
    }
  },
  yAxis: {
    type: 'value',
    name: 'Detections'
  },
  series: [
    {
      name: 'Detections',
      type: 'bar',
      data: speciesCounts.value.map(s => s.count),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#3b82f6' },
          { offset: 1, color: '#93c5fd' }
        ])
      },
      emphasis: {
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#2563eb' },
            { offset: 1, color: '#60a5fa' }
          ])
        }
      }
    }
  ],
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
}))

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
    
    // Count species occurrences
    const speciesMap = new Map<string, number>()
    responses.forEach(response => {
      Object.values(response.data).forEach((species: any) => {
        const count = speciesMap.get(species.common_name) || 0
        speciesMap.set(species.common_name, count + species.total_detections)
      })
    })
    
    // Convert to array and sort by count
    speciesCounts.value = Array.from(speciesMap.entries())
      .map(([common_name, count]) => ({ common_name, count }))
      .sort((a, b) => b.count - a.count)
    
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
