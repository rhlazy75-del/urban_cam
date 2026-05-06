import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/ucs',
  server: {
    allowedHosts: ['geodev.fun', 'localhost', '127.0.0.1'],
  },
})
