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
          </div>

          <!-- Right side -->
          <div class="flex items-center">
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
    <div class="fixed bottom-0 right-0 p-6 space-y-4">
      <!-- Add toast notifications here -->
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
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
})
</script>
