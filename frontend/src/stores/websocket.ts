import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Notification, NotificationType, NotificationOptions } from '@/types/notifications'

interface DetectionData {
  common_name: string
  scientific_name: string
  score: number
  frigate_event: string
}

interface WebSocketMessage {
  type: string
  data: any
}

interface ConnectionStatus {
  isConnected: boolean
  connections: number
  lastPing: number
}

export const useWebSocketStore = defineStore('websocket', () => {
  const ws = ref<WebSocket | null>(null)
  const status = ref<ConnectionStatus>({
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
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.hostname}:8765/ws`
    
    ws.value = new WebSocket(wsUrl)

    ws.value.onopen = () => {
      console.log('WebSocket connected')
      status.value.isConnected = true
      startPingInterval()
      
      // Show connection notification
      addNotification({
        message: 'Connected to real-time updates',
        type: 'success'
      })
    }

    ws.value.onclose = () => {
      console.log('WebSocket disconnected')
      status.value.isConnected = false
      clearPingInterval()
      scheduleReconnect()

      // Show disconnection notification
      addNotification({
        message: 'Connection lost. Attempting to reconnect...',
        type: 'warning'
      })
    }

    ws.value.onerror = (error) => {
      console.error('WebSocket error:', error)
      status.value.isConnected = false
      
      addNotification({
        message: 'Connection error occurred',
        type: 'error'
      })
    }

    ws.value.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data)
        handleMessage(message)
      } catch (error) {
        console.error('Error parsing WebSocket message:', error)
      }
    }
  }

  function handleMessage(message: WebSocketMessage) {
    switch (message.type) {
      case 'status':
        status.value.connections = message.data.connections
        break
      
      case 'detection':
        // Handle new bird detection
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
    }, 30000) // Ping every 30 seconds
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
    reconnectTimeout = window.setTimeout(() => {
      console.log('Attempting to reconnect...')
      connect()
    }, 5000) // Try to reconnect after 5 seconds
  }

  function addNotification(options: NotificationOptions) {
    const id = ++notificationId
    const notification: Notification = {
      id,
      message: options.message,
      type: options.type || 'info',
      timestamp: Date.now()
    }
    notifications.value.push(notification)

    // Remove notification after 5 seconds
    setTimeout(() => {
      removeNotification(id)
    }, 5000)
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
