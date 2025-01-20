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
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useDetectionStore } from '@/stores/detection'
import DailySummaryTable from '@/components/DailySummaryTable.vue'
import axios from 'axios'

const route = useRoute()
const detectionStore = useDetectionStore()
const currentDate = ref<string>('')

const getInitialDate = async (): Promise<string> => {
  const routeDate = Array.isArray(route.params.date) 
    ? route.params.date[0] 
    : (route.params.date as string | undefined)
  
  if (routeDate) {
    return routeDate
  }

  try {
    const response = await axios.get('/api/earliest-detection-date')
    return response.data.date || new Date().toISOString().split('T')[0]
  } catch (error) {
    console.error('Error fetching earliest date:', error)
    return new Date().toISOString().split('T')[0]
  }
}

const formattedDate = computed((): string => {
  if (!currentDate.value) return ''
  const dateObj = new Date(currentDate.value)
  return dateObj.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
})

onMounted(async () => {
  currentDate.value = await getInitialDate()
  await detectionStore.fetchDailySummary(currentDate.value)
})
</script>

<style scoped>
.daily-summary {
  padding: 20px;
}
</style>
