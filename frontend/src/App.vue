<template>
  <nav class="navbar navbar-expand-lg navbar-light bg-light">
    <div class="container-fluid">
      <router-link class="navbar-brand" to="/">Who's At My Feeder?</router-link>
      <button 
        class="navbar-toggler" 
        type="button" 
        data-bs-toggle="collapse" 
        data-bs-target="#navbarSupportedContent"
      >
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarSupportedContent">
        <ul class="navbar-nav me-auto mb-2 mb-lg-0">
        </ul>
        <form class="d-flex" @submit.prevent>
          <input 
            type="date" 
            class="form-control" 
            :value="currentDate"
            :min="earliestDate"
            :max="currentDate"
            @change="navigateToDailySummary"
          />
        </form>
      </div>
    </div>
  </nav>

  <router-view v-slot="{ Component }">
    <transition name="fade" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const currentDate = ref(new Date().toISOString().split('T')[0])
const earliestDate = ref(currentDate.value)

const navigateToDailySummary = (event: Event) => {
  const input = event.target as HTMLInputElement
  router.push({ name: 'daily-summary', params: { date: input.value } })
}

onMounted(async () => {
  try {
    const response = await axios.get('/api/earliest-detection-date')
    earliestDate.value = response.data.date
  } catch (error) {
    console.error('Failed to fetch earliest detection date:', error)
  }
})
</script>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.navbar {
  flex-shrink: 0;
}

main {
  flex-grow: 1;
}
</style>
