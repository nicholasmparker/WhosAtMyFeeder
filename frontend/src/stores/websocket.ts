import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Notification, NotificationType, NotificationOptions } from '@/types/notifications'

export const useWebSocketStore = defineStore('websocket', () => {
  const ws = ref<WebSocket | null>(null)
  const status = ref({
    isConnected: false,
    connections: 0,
    lastPing: Date.now()
  })
  const notifications = ref<Notification[]>([])
  let pingInterval: number | undefined
  let reconnectTimeout: number | undefined
  let notificationId = 0

  const isConnected = computed(() => status.value.isConnected)
  const activeConnections = computed(() => status.value.connections)

  function connect() {
    const wsUrl = `ws://${window.location.host}/ws`
    ws.value = new WebSocket(wsUrl)

    ws.value.onopen = () => {
      status.value.isConnected = true
      startPingInterval()
    }

    ws.value.onclose = () => {
      status.value.isConnected = false
      clearPingInterval()
      scheduleReconnect()
    }

    ws.value.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        handleMessage(message)
      } catch (error) {
        console.error('Error parsing message:', error)
      }
    }
  }

  function handleMessage(message: any) {
    switch (message.type) {
      case 'status':
        status.value.connections = message.data.connections
        break
      case 'detection':
        addNotification({
          message: `New detection: ${message.data.common_name}`,
          type: 'info'
        })
        break
      case 'pong':
        status.value.lastPing = Date.now()
        break
    }
  }

  function startPingInterval() {
    clearPingInterval()
    pingInterval = window.setInterval(() => {
      if (ws.value?.readyState === WebSocket.OPEN) {
        ws.value.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000)
  }

  function clearPingInterval() {
    if (pingInterval) {
      clearInterval(pingInterval)
      pingInterval = undefined
    }
  }

  function scheduleReconnect() {
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout)
    }
    reconnectTimeout = window.setTimeout(connect, 5000)
  }

  function addNotification(options: NotificationOptions) {
    const id = ++notificationId
    notifications.value.push({
      id,
      message: options.message,
      type: options.type || 'info',
      timestamp: Date.now()
    })
    setTimeout(() => removeNotification(id), 5000)
  }

  function removeNotification(id: number) {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index !== -1) {
      notifications.value.splice(index, 1)
    }
  }

  function disconnect() {
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
    clearPingInterval()
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout)
      reconnectTimeout = undefined
    }
  }

  return {
    status,
    notifications,
    isConnected,
    activeConnections,
    connect,
    disconnect,
    addNotification,
    removeNotification
  }
})
