import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'node:fs'
import path from 'node:path'

// dev-only save endpoint: the inspector posts edited docs back to disk
function saveEndpoint() {
  return {
    name: 'save-endpoint',
    configureServer(server) {
      server.middlewares.use('/save', (req, res) => {
        if (req.method !== 'POST') { res.statusCode = 404; return res.end() }
        let body = ''
        req.on('data', c => { body += c })
        req.on('end', () => {
          const { path: rel, doc } = JSON.parse(body)
          const target = path.join(process.cwd(), 'public',
            path.normalize(rel).replace(/^\/+/, ''))
          if (!target.includes(path.join('public', 'docs')) ||
              !target.endsWith('.json')) {
            res.statusCode = 403
            return res.end('only docs/*.json')
          }
          fs.writeFileSync(target, JSON.stringify(doc, null, 1))
          res.setHeader('Content-Type', 'application/json')
          res.end('{"ok":true}')
        })
      })
    },
  }
}

export default defineConfig({
  plugins: [react(), saveEndpoint()],
  server: { port: 8900 },
})
