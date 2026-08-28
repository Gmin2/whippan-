import { serve } from '@hono/node-server'
import { createApp } from './app.js'
import { loadConfig } from './config.js'
import { FsStore } from './store/fs.js'

const config = loadConfig()
const store = new FsStore(config.docsDir)
const app = createApp(store, config)

const server = serve({ fetch: app.fetch, port: config.port }, info => {
  console.log(`whippan api on :${info.port}  ${store.description}  [${config.env}]`)
})

// containers stop by signal; finish in-flight writes rather than dropping them
for (const signal of ['SIGINT', 'SIGTERM'] as const) {
  process.on(signal, () => {
    server.close(() => process.exit(0))
    setTimeout(() => process.exit(1), 5000).unref()
  })
}
