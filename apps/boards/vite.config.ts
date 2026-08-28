import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  // the wasm glue must stay unbundled, and public/ symlinks out to the repo
  optimizeDeps: { exclude: ['@whippan/engine-web'] },
  plugins: [react(), tailwindcss()],
  server: { port: 8902, fs: { allow: ['../..'] } },
})
