import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { logger } from 'hono/logger'
import type { Config } from './config.js'
import type { DocStore } from './store/types.js'
import { SLUG, validateDoc } from './validate.js'

/**
 * The film API. Deliberately storage-agnostic: it is handed a DocStore and
 * never learns whether that is a filesystem, object storage or a database.
 */
export function createApp(store: DocStore, config: Config) {
  const app = new Hono()

  app.use('*', logger())
  if (config.corsOrigins.length) {
    app.use('/api/*', cors({
      origin: config.corsOrigins.includes('*') ? '*' : config.corsOrigins,
      allowMethods: ['GET', 'PUT', 'OPTIONS'],
      allowHeaders: ['content-type'],
    }))
  }

  // liveness for a load balancer or orchestrator
  app.get('/healthz', c => c.json({ ok: true, env: config.env }))

  app.get('/api/films', async c => {
    try {
      return c.json(await store.list())
    } catch (e) {
      return c.json({ error: `registry unavailable: ${String(e)}` }, 503)
    }
  })

  app.get('/api/films/:slug', async c => {
    const slug = c.req.param('slug')
    if (!SLUG.test(slug)) return c.json({ error: 'bad slug' }, 400)
    const doc = await store.get(slug)
    return doc ? c.json(doc) : c.json({ error: 'not found' }, 404)
  })

  app.put('/api/films/:slug', async c => {
    const slug = c.req.param('slug')
    if (!SLUG.test(slug)) return c.json({ error: 'bad slug' }, 400)
    if (!(await store.has(slug))) return c.json({ error: 'not found' }, 404)

    let body: unknown
    try {
      body = await c.req.json()
    } catch {
      return c.json({ error: 'body is not json' }, 400)
    }

    const checked = validateDoc(body)
    if ('error' in checked) return c.json(checked, 422)

    try {
      await store.put(slug, checked)
      return c.json({ ok: true, slug })
    } catch (e) {
      return c.json({ error: String(e) }, 500)
    }
  })

  app.notFound(c => c.json({ error: 'no such route' }, 404))
  return app
}
