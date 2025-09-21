import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [vue()],
    server: {
        // This is needed for the Docker container to be accessible
        host: true,
        port: 5173,
        // Proxy API requests to the backend
        proxy: {
            '/api': {
                target: 'http://backend:8000',
                changeOrigin: true,
            },
        },
    },
})