import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { logger } from 'hono/logger'
import type { Config } from './config.js'
import type { DocStore } from './store/types.js'
import { SLUG, validateDoc } from './validate.js'
import { ExportQueue } from './export/queue.js'
import { capabilities, isMissingKey, runImage, runMotion, runVector } from './ai/providers.js'
import { createReadStream } from 'node:fs'
import { Readable } from 'node:stream'

/**
 * The film API. Deliberately storage-agnostic: it is handed a DocStore and
 * never learns whether that is a filesystem, object storage or a database.
 */
export function createApp(store: DocStore, config: Config, queue?: ExportQueue) {
  const app = new Hono()

  app.use('*', logger())
  if (config.corsOrigins.length) {
    app.use('/api/*', cors({
      origin: config.corsOrigins.includes('*') ? '*' : config.corsOrigins,
      allowMethods: ['GET', 'PUT', 'POST', 'DELETE', 'OPTIONS'],
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

  app.get('/api/assets', async c => {
    try {
      return c.json(await store.assets())
    } catch (e) {
      return c.json({ error: String(e) }, 503)
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

  // ---- export -------------------------------------------------------------
  // Rendering a film takes seconds, so an export is a job rather than a
  // request: POST queues it, GET polls it, and the file is fetched separately.
  // The document travels in the body so what you see in the editor is what
  // gets rendered, unsaved edits included.

  /**
   * The prompt bar. The browser never sees a provider key: it asks what is
   * configured, then posts a prompt and gets back a proposal it can show.
   */
  app.get('/api/ai', c => c.json(capabilities()))

  app.post('/api/ai/:kind', async c => {
    const kind = c.req.param('kind')
    let body: Record<string, unknown>
    try {
      body = await c.req.json() as Record<string, unknown>
    } catch {
      return c.json({ error: 'body must be json' }, 400)
    }
    const prompt = typeof body.prompt === 'string' ? body.prompt.trim() : ''
    if (!prompt) return c.json({ error: 'prompt is required' }, 400)
    if (prompt.length > 4000) return c.json({ error: 'prompt is too long' }, 400)
    const model = typeof body.model === 'string' ? body.model : undefined

    try {
      if (kind === 'motion') {
        const nodes = Array.isArray(body.nodes) ? body.nodes : []
        if (!nodes.length) return c.json({ error: 'select something first' }, 400)
        return c.json(await runMotion({
          prompt, model,
          nodes: nodes as { id: string; type: string }[],
          scene: body.scene as { id: string; dur: number; index: number; total: number },
          tracks: Array.isArray(body.tracks) ? body.tracks : [],
        }))
      }
      if (kind === 'image') {
        return c.json(await runImage({
          prompt, model,
          aspect: typeof body.aspect === 'string' ? body.aspect : undefined,
        }))
      }
      if (kind === 'vector') {
        return c.json(await runVector({
          prompt, model,
          instructions: typeof body.instructions === 'string' ? body.instructions : undefined,
        }))
      }
      return c.json({ error: `no such action: ${kind}` }, 404)
    } catch (e) {
      // a missing key is a configuration answer, not a server fault
      if (isMissingKey(e)) return c.json({ error: String((e as Error).message) }, 503)
      return c.json({ error: e instanceof Error ? e.message : String(e) }, 502)
    }
  })

  if (queue) {
    app.post('/api/films/:slug/export', async c => {
      const slug = c.req.param('slug')
      if (!SLUG.test(slug)) return c.json({ error: 'bad slug' }, 400)

      let body: unknown
      try {
        body = await c.req.json()
      } catch {
        return c.json({ error: 'body is not json' }, 400)
      }

      const { fps, supersample } = (body ?? {}) as
        { fps?: unknown; supersample?: unknown }
      const checked = validateDoc(body)
      if ('error' in checked) return c.json(checked, 422)

      const ready = await queue.preflight()
      if (!ready.ok) return c.json({ error: ready.reason }, 503)

      const rate = Number(fps)
      const job = queue.enqueue(slug, checked.stage, checked.anim, {
        fps: Number.isFinite(rate) && rate >= 1 && rate <= 120 ? rate : undefined,
        supersample: supersample === 2 ? 2 : 1,
      })
      return c.json(queue.get(job.id), 202)
    })

    app.get('/api/exports', c => c.json(queue.list()))

    app.get('/api/exports/:id', c => {
      const job = queue.get(c.req.param('id'))
      return job ? c.json(job) : c.json({ error: 'no such job' }, 404)
    })

    app.delete('/api/exports/:id', c => {
      const ok = queue.cancel(c.req.param('id'))
      return ok ? c.json({ ok: true }) : c.json({ error: 'not cancellable' }, 409)
    })

    app.get('/api/exports/:id/file', async c => {
      const id = c.req.param('id')
      const job = queue.get(id)
      if (!job) return c.json({ error: 'no such job' }, 404)
      if (job.status !== 'done') {
        return c.json({ error: `job is ${job.status}` }, 409)
      }
      const path = queue.fileOf(id)
      if (!path) return c.json({ error: 'artifact swept' }, 410)

      c.header('content-type', 'video/mp4')
      c.header('content-length', String(job.bytes ?? 0))
      c.header('content-disposition', `attachment; filename="${job.slug}.mp4"`)
      // stream it: a 4K export is tens of megabytes and should not be buffered
      return c.body(Readable.toWeb(createReadStream(path)) as ReadableStream)
    })
  }

  app.notFound(c => c.json({ error: 'no such route' }, 404))
  return app
}
