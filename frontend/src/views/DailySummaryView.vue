<template>
  <div class="daily-summary">
    <div class="container-fluid">
      <div class="row">
        <div class="col-12">
          <h2>Daily Summary for {{ formattedDate }}</h2>
          <DailySummaryTable 
            v-if="!detectionStore.loading"
            :daily-summary="detectionStore.getDailySummary"
            :current-hour="23"
          />
          <div v-else class="text-center">
            <div class="spinner-border" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useDetectionStore } from '@/stores/detection'
import DailySummaryTable from '@/components/DailySummaryTable.vue'

const route = useRoute()
const detectionStore = useDetectionStore()

const getCurrentDate = (): string => {
  const today = new Date()
  return today.toISOString().split('T')[0]
}

const date = computed((): string => {
  const routeDate = Array.isArray(route.params.date) 
    ? route.params.date[0] 
    : (route.params.date as string | undefined)
  return routeDate || getCurrentDate()
})

const formattedDate = computed((): string => {
  const dateObj = new Date(date.value)
  return dateObj.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
})

onMounted(async () => {
  await detectionStore.fetchDailySummary(date.value)
})
</script>

<style scoped>
.daily-summary {
  padding: 20px;
}
</style>
