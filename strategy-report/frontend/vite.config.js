import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    allowedHosts: process.env.STRATEGY_REPORT_DEV_HOST?.split(',').map(host => host.trim()).filter(Boolean),
    proxy: { '/api': process.env.STRATEGY_REPORT_API_PROXY || 'http://localhost:8001' }
  }
})
