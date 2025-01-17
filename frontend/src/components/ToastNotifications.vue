<template>
  <div 
    aria-live="polite" 
    class="fixed bottom-0 right-0 z-50 p-4 space-y-4 pointer-events-none"
  >
    <TransitionGroup 
      name="toast"
      tag="div"
      class="space-y-2"
    >
      <div
        v-for="notification in notifications"
        :key="notification.id"
        class="pointer-events-auto max-w-sm w-full bg-white shadow-lg rounded-lg ring-1 ring-black ring-opacity-5 transform transition-all duration-300"
        :class="{
          'ring-green-500/30 bg-green-50': notification.type === 'success',
          'ring-blue-500/30 bg-blue-50': notification.type === 'info',
          'ring-yellow-500/30 bg-yellow-50': notification.type === 'warning',
          'ring-red-500/30 bg-red-50': notification.type === 'error'
        }"
      >
        <div class="p-4">
          <div class="flex items-start">
            <div class="flex-shrink-0">
              <!-- Success Icon -->
              <svg
                v-if="notification.type === 'success'"
                class="h-6 w-6 text-green-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              <!-- Info Icon -->
              <svg
                v-else-if="notification.type === 'info'"
                class="h-6 w-6 text-blue-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <!-- Warning Icon -->
              <svg
                v-else-if="notification.type === 'warning'"
                class="h-6 w-6 text-yellow-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <!-- Error Icon -->
              <svg
                v-else-if="notification.type === 'error'"
                class="h-6 w-6 text-red-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <div class="ml-3 w-0 flex-1">
              <p 
                class="text-sm font-medium"
                :class="{
                  'text-green-800': notification.type === 'success',
                  'text-blue-800': notification.type === 'info',
                  'text-yellow-800': notification.type === 'warning',
                  'text-red-800': notification.type === 'error'
                }"
              >
                {{ notification.message }}
              </p>
              <p class="mt-1 text-sm text-gray-500">
                {{ formatTime(notification.timestamp) }}
              </p>
            </div>
            <div class="ml-4 flex-shrink-0 flex">
              <button
                type="button"
                class="rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                @click="removeNotification(notification.id)"
              >
                <span class="sr-only">Close</span>
                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { useWebSocketStore } from '@/stores/websocket'
import { storeToRefs } from 'pinia'
import { formatDistanceToNow } from 'date-fns'
import type { Notification } from '@/types/notifications'

const store = useWebSocketStore()
const { notifications } = storeToRefs(store)
const { removeNotification } = store

const formatTime = (timestamp: number) => {
  return formatDistanceToNow(timestamp, { addSuffix: true })
}
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.toast-move {
  transition: transform 0.3s ease;
}
</style>
