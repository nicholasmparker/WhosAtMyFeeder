import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',  // Listen on all addresses
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://host.docker.internal:7766',
        changeOrigin: true,
        secure: false,
      },
      '/frigate': {
        target: 'http://host.docker.internal:7766',
        changeOrigin: true,
        secure: false,
      }
    },
    watch: {
      usePolling: true,  // Required for Docker on some systems
    },
    hmr: {
      host: 'localhost',
      clientPort: 5173
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    manifest: true,
  },
})
