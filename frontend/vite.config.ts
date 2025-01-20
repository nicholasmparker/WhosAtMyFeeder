import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: true,
    proxy: {
      '/api': {
        target: 'http://app:7766',
        changeOrigin: true
      },
      '/frigate': {
        target: 'http://app:7766',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://websocket:8765',
        ws: true,
        rewriteWsOrigin: true,
      }
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  }
})
