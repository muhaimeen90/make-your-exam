import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    server: {
        host: '0.0.0.0', // Allow external connections for Docker
        proxy: {
            '/api': {
                target: process.env.VITE_BACKEND_URL || 'http://localhost:8000',
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\/api/, '')
            },
            '/uploads': {
                target: process.env.VITE_BACKEND_URL || 'http://localhost:8000',
                changeOrigin: true
            },
            '/generated': {
                target: process.env.VITE_BACKEND_URL || 'http://localhost:8000',
                changeOrigin: true
            },
            '/thumbnail': {
                target: process.env.VITE_BACKEND_URL || 'http://localhost:8000',
                changeOrigin: true
            }
        }
    }
})
