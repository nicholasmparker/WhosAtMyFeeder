<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Navigation -->
    <nav class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <!-- Left side -->
          <div class="flex">
            <router-link 
              to="/" 
              class="flex items-center px-2 text-primary-600 font-semibold text-lg hover:text-primary-700"
            >
              Who's At My Feeder?
            </router-link>

            <!-- Desktop Navigation Links -->
            <div class="hidden md:flex md:items-center md:ml-6 space-x-4">
              <router-link 
                to="/daily-summary" 
                class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                active-class="text-primary-600"
              >
                Daily Summary
              </router-link>
              <router-link 
                to="/detections-by-hour" 
                class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                active-class="text-primary-600"
              >
                By Hour
              </router-link>
              <router-link 
                to="/detections-by-species" 
                class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                active-class="text-primary-600"
              >
                By Species
              </router-link>
              <router-link 
                to="/weather-insights" 
                class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                active-class="text-primary-600"
              >
                Weather Analysis
              </router-link>
              <router-link 
                to="/special-detections" 
                class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                active-class="text-primary-600"
              >
                Special Detections
              </router-link>
            </div>
          </div>

          <!-- Right side -->
          <div class="flex items-center">
            <!-- Connection Status -->
            <div class="mr-4">
              <span 
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                :class="{
                  'bg-green-100 text-green-800': webSocketStore.isConnected,
                  'bg-red-100 text-red-800': !webSocketStore.isConnected
                }"
              >
                <span 
                  class="w-2 h-2 mr-1.5 rounded-full"
                  :class="{
                    'bg-green-400': webSocketStore.isConnected,
                    'bg-red-400': !webSocketStore.isConnected
                  }"
                ></span>
                {{ webSocketStore.isConnected ? 'Connected' : 'Disconnected' }}
              </span>
            </div>

            <!-- Date Picker -->
            <div class="relative">
              <input 
                type="date" 
                :value="currentDate"
                :min="earliestDate"
                :max="currentDate"
                @change="navigateToDailySummary"
                class="block w-44 rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              />
            </div>

            <!-- Mobile menu button -->
            <button 
              @click="isOpen = !isOpen"
              class="ml-4 inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500 md:hidden"
            >
              <span class="sr-only">Open main menu</span>
              <!-- Icon when menu is closed -->
              <svg 
                v-if="!isOpen"
                class="block h-6 w-6" 
                xmlns="http://www.w3.org/2000/svg" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
              <!-- Icon when menu is open -->
              <svg 
                v-else
                class="block h-6 w-6" 
                xmlns="http://www.w3.org/2000/svg" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Mobile menu -->
      <div v-show="isOpen" class="md:hidden">
        <div class="pt-2 pb-3 space-y-1">
          <router-link 
            to="/" 
            class="block px-3 py-2 text-base font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50"
            active-class="bg-primary-50 text-primary-700"
          >
            Home
          </router-link>
          <router-link 
            to="/daily-summary" 
            class="block px-3 py-2 text-base font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50"
            active-class="bg-primary-50 text-primary-700"
          >
            Daily Summary
          </router-link>
          <router-link 
            to="/detections-by-hour" 
            class="block px-3 py-2 text-base font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50"
            active-class="bg-primary-50 text-primary-700"
          >
            By Hour
          </router-link>
          <router-link 
            to="/detections-by-species" 
            class="block px-3 py-2 text-base font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50"
            active-class="bg-primary-50 text-primary-700"
          >
            By Species
          </router-link>
          <router-link 
            to="/weather-insights" 
            class="block px-3 py-2 text-base font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50"
            active-class="bg-primary-50 text-primary-700"
          >
            Weather Analysis
          </router-link>
          <router-link 
            to="/special-detections" 
            class="block px-3 py-2 text-base font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50"
            active-class="bg-primary-50 text-primary-700"
          >
            Special Detections
          </router-link>
        </div>
      </div>
    </nav>

    <!-- Main content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- Toast Notifications -->
    <ToastNotifications />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useWebSocketStore } from '@/stores/websocket'
import ToastNotifications from '@/components/ToastNotifications.vue'
import axios from 'axios'

const router = useRouter()
const webSocketStore = useWebSocketStore()
const currentDate = ref(new Date().toISOString().split('T')[0])
const earliestDate = ref(currentDate.value)
const isOpen = ref(false)

const navigateToDailySummary = (event: Event) => {
  const input = event.target as HTMLInputElement
  router.push({ name: 'daily-summary', params: { date: input.value } })
  isOpen.value = false
}

onMounted(async () => {
  try {
    const response = await axios.get('/api/earliest-detection-date')
    earliestDate.value = response.data.date
  } catch (error) {
    console.error('Failed to fetch earliest detection date:', error)
  }

  // Initialize WebSocket connection
  webSocketStore.connect()
})

onBeforeUnmount(() => {
  // Clean up WebSocket connection
  webSocketStore.disconnect()
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
</style>
