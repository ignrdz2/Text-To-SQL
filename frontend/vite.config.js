import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,  // escucha en 0.0.0.0 para que funcione dentro del contenedor Docker
    port: 5173,
    proxy: {
      '/api': {
        // En Docker usa la red interna; en local usa localhost.
        // Controlado por la variable VITE_API_TARGET en docker-compose.yml.
        target: process.env.VITE_API_TARGET ?? 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
