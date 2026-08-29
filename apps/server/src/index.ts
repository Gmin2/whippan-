import { serve } from '@hono/node-server'
import { createApp } from './app.js'
import { loadConfig } from './config.js'
import { FsStore } from './store/fs.js'
import { ExportQueue } from './export/queue.js'

const config = loadConfig()
const store = new FsStore(config.docsDir)
const queue = new ExportQueue(config.export)
queue.start()
const app = createApp(store, config, queue)

// say up front whether exporting will actually work, rather than failing on
// the first request
void queue.preflight().then(r => {
  console.log(r.ok ? 'export: renderer and ffmpeg ready' : `export unavailable: ${r.reason}`)
})

const server = serve({ fetch: app.fetch, port: config.port }, info => {
  console.log(`whippan api on :${info.port}  ${store.description}  [${config.env}]`)
})

// a busy port is an operator mistake, not a crash: say which port and stop
server.on('error', (e: NodeJS.ErrnoException) => {
  if (e.code === 'EADDRINUSE') {
    console.error(`port ${config.port} is already in use. `
      + 'stop the other server, or set PORT to something else.')
    process.exit(1)
  }
  throw e
})

// containers stop by signal; finish in-flight writes rather than dropping them
for (const signal of ['SIGINT', 'SIGTERM'] as const) {
  process.on(signal, () => {
    void queue.stop()
    server.close(() => process.exit(0))
    setTimeout(() => process.exit(1), 5000).unref()
  })
}
