import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

/** the film api; run it with `pnpm --filter @whippan/server dev` */
const API = process.env.VITE_API_BASE || 'http://localhost:8903'

export default defineConfig({
  // the wasm glue must stay unbundled, and public/ symlinks out to the repo
  optimizeDeps: { exclude: ['@whippan/engine-web'] },
  plugins: [react(), tailwindcss()],
  server: {
    port: 8902,
    fs: { allow: ['../..'] },
    // documents go through the api; only static assets come from public/
    proxy: { '/api': { target: API, changeOrigin: true } },
  },
})
