<template>
  <div class="space-y-8">
    <!-- Empty State -->
    <div v-if="!detectionStore.hasData" class="text-center py-12">
      <div class="rounded-full bg-primary-100 p-3 mx-auto w-fit">
        <svg class="w-12 h-12 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
      </div>
      <h3 class="mt-4 text-xl font-medium text-gray-900">Waiting for Bird Detections</h3>
      <p class="mt-2 text-sm text-gray-500">
        The system is ready and waiting for the first bird detection.
        Data will appear here automatically when birds are detected.
      </p>
    </div>

    <template v-else>
      <!-- Data Visualization Section -->
      <div class="grid grid-cols-1 xl:grid-cols-2 gap-8">
        <!-- Bird Activity Heatmap -->
        <BirdActivityHeatmap class="xl:col-span-2" />

        <!-- Species Frequency Chart -->
        <SpeciesFrequencyChart />

        <!-- Detection Trends Chart -->
        <DetectionTrendsChart />
      </div>

      <!-- Recent Detections Section -->
      <section class="bg-white rounded-lg shadow-sm overflow-hidden">
        <div v-if="detectionStore.loading" class="p-8">
          <div class="flex justify-center items-center">
            <svg class="animate-spin h-8 w-8 text-primary-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
        </div>
        <RecentDetections 
          v-else
          :recent-detections="detectionStore.getRecentDetections" 
          class="divide-y divide-gray-200"
        />
      </section>

      <!-- Daily Summary Section -->
      <section class="bg-white rounded-lg shadow-sm overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-200">
          <h2 class="text-lg font-medium text-gray-900">Detection Summary</h2>
        </div>
        <div v-if="detectionStore.loading" class="p-8">
          <div class="flex justify-center items-center">
            <svg class="animate-spin h-8 w-8 text-primary-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
        </div>
        <DailySummaryTable 
          v-else
          :daily-summary="detectionStore.getDailySummary"
          :current-hour="currentHour"
        />
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useDetectionStore } from '@/stores/detection'
import RecentDetections from '@/components/RecentDetections.vue'
import DailySummaryTable from '@/components/DailySummaryTable.vue'
import BirdActivityHeatmap from '@/components/BirdActivityHeatmap.vue'
import SpeciesFrequencyChart from '@/components/SpeciesFrequencyChart.vue'
import DetectionTrendsChart from '@/components/DetectionTrendsChart.vue'

const detectionStore = useDetectionStore()
const currentHour = ref(new Date().getHours())

onMounted(async () => {
  const today = new Date().toISOString().split('T')[0]
  await Promise.all([
    detectionStore.fetchRecentDetections(),
    detectionStore.fetchDailySummary(today)
  ])
})
</script>
