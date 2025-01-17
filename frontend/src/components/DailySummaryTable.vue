<template>
  <div class="table-responsive">
    <table class="table">
      <thead>
        <tr>
          <th scope="col">Common Name</th>
          <th scope="col">Total</th>
          <th v-for="hour in currentHour + 1" :key="hour" scope="col">
            <router-link 
              :to="{ name: 'detections-by-hour', params: { date: currentDate, hour: hour }}"
              class="text-decoration-none text-reset"
            >
              {{ hour }}
            </router-link>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="species in dailySummaryArray" :key="species.scientific_name">
          <td>
            <router-link 
              :to="{ 
                name: 'detections-by-species', 
                params: { 
                  scientificName: species.scientific_name,
                  date: currentDate
                }
              }"
              class="text-decoration-none text-reset"
            >
              {{ species.common_name }}
            </router-link>
          </td>
          <td>{{ species.total_detections }}</td>
          <td v-for="hour in currentHour + 1" :key="hour">
            {{ species.hourly_detections[hour] || 0 }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface DailySummary {
  [key: string]: {
    common_name: string
    scientific_name: string
    total_detections: number
    hourly_detections: number[]
  }
}

interface Props {
  dailySummary: DailySummary
  currentHour: number
}

const props = defineProps<Props>()

const currentDate = computed(() => {
  return new Date().toISOString().split('T')[0]
})

const dailySummaryArray = computed(() => {
  return Object.values(props.dailySummary).sort((a, b) => {
    return b.total_detections - a.total_detections
  })
})
</script>

<style scoped>
.table th {
  white-space: nowrap;
}

.table td {
  vertical-align: middle;
}
</style>
