import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [
    vue({
      template: {
        compilerOptions: {
          isCustomElement: (tag) => tag === 'teleport'
        }
      }
    })
  ],
  server: {
    host: '0.0.0.0',
    port: 5173,
    watch: {
      usePolling: true
    },
    hmr: {
      protocol: 'ws',
      host: 'localhost',
      port: 5173,
      clientPort: 5173
    },
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
        changeOrigin: true
      }
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    }
  },
  optimizeDeps: {
    include: [
      'vue',
      'vue-router',
      'pinia',
      '@heroicons/vue',
      '@headlessui/vue',
      'axios',
      'date-fns',
      'echarts',
      'vue-echarts'
    ],
    exclude: [],
    esbuildOptions: {
      target: 'esnext'
    },
    force: true, // Force dependency pre-bundling
    disabled: process.env.NODE_ENV === 'development' // Disable caching in development
  },
  build: {
    target: 'esnext',
    commonjsOptions: {
      include: [/node_modules/],
      extensions: ['.js', '.cjs', '.mjs'],
    }
  },
  cacheDir: '.vite' // Store cache in project directory instead of node_modules
})
