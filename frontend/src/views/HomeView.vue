<template>
  <div class="home">
    <div class="container-fluid">
      <div v-if="!detectionStore.hasData" class="row">
        <div class="col-12 text-center mt-5">
          <h3>Waiting for Bird Detections</h3>
          <p class="text-muted">
            The system is ready and waiting for the first bird detection.
            Data will appear here automatically when birds are detected.
          </p>
        </div>
      </div>

      <template v-else>
        <div class="row">
          <div class="col-12">
            <RecentDetections 
              v-if="!detectionStore.loading"
              :recent-detections="detectionStore.getRecentDetections" 
            />
            <div v-else class="text-center">
              <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
              </div>
            </div>
          </div>
        </div>

        <div class="row mt-4">
          <div class="col-12">
            <h2>Detection Summary</h2>
            <DailySummaryTable 
              v-if="!detectionStore.loading"
              :daily-summary="detectionStore.getDailySummary"
              :current-hour="currentHour"
            />
            <div v-else class="text-center">
              <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useDetectionStore } from '@/stores/detection'
import RecentDetections from '@/components/RecentDetections.vue'
import DailySummaryTable from '@/components/DailySummaryTable.vue'

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

<style scoped>
.home {
  padding: 20px;
}
</style>
