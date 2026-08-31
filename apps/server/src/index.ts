import { serve } from '@hono/node-server'
import { createApp } from './app.js'
import { loadConfig } from './config.js'
import { FsStore } from './store/fs.js'
import { PgStore, DEFAULT_WORKSPACE } from './store/pg.js'
import { db } from './db/pool.js'
import { migrate } from './db/migrate.js'
import { makeAuth, workspaceResolver } from './auth.js'
import type { Auth } from './auth.js'
import type { StoreFor } from './app.js'
import { ExportQueue } from './export/queue.js'

const config = loadConfig()

// postgres when there is a DATABASE_URL, the filesystem otherwise. DocStore is
// the whole seam, so nothing downstream of here knows which one it got
let storeFor: StoreFor
let auth: Auth | undefined
let workspaceOf: ((userId: string) => Promise<string | null>) | undefined

if (config.databaseUrl) {
  const pool = db(config.databaseUrl)
  const ran = await migrate(pool)
  if (ran.length) console.log(`migrations applied: ${ran.join(', ')}`)
  // a store per workspace; it holds a pool reference and an id, so this is free
  storeFor = ws => new PgStore(pool, ws ?? DEFAULT_WORKSPACE)
  if (config.auth) {
    auth = makeAuth(pool, config.auth)
    workspaceOf = workspaceResolver(pool)
  } else {
    console.log('auth: off (set BETTER_AUTH_SECRET to enable accounts)')
  }
} else {
  const fs = new FsStore(config.docsDir)
  storeFor = () => fs
}
const queue = new ExportQueue(config.export)
queue.start()
const app = createApp(storeFor, config, queue, auth, workspaceOf)

// say up front whether exporting will actually work, rather than failing on
// the first request
void queue.preflight().then(r => {
  console.log(r.ok ? 'export: renderer and ffmpeg ready' : `export unavailable: ${r.reason}`)
})

const server = serve({ fetch: app.fetch, port: config.port }, info => {
  console.log(`whippan api on :${info.port}  ${config.databaseUrl ? 'postgres' : config.docsDir}  [${config.env}]`)
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
