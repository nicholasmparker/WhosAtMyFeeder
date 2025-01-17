import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';
// https://vitejs.dev/config/
export default defineConfig({
    plugins: [vue()],
    server: {
        port: 5173,
        proxy: {
            '/api': {
                target: 'http://localhost:7766',
                changeOrigin: true,
            },
            '/frigate': {
                target: 'http://localhost:7766',
                changeOrigin: true,
            }
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
});
