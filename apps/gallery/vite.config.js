import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  optimizeDeps: { exclude: ['@whippan/engine-web'] },
  plugins: [react(), tailwindcss()],
  server: { port: 8901, fs: { allow: ['../..'] } },
})
