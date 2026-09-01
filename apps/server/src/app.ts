import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { logger } from 'hono/logger'
import type { Config } from './config.js'
import type { DocStore } from './store/types.js'
import type { Auth } from './auth.js'
import type { BlobStore } from './blob/types.js'
import { ASSETS, EXPORTS } from './blob/types.js'
import { SLUG, validateDoc } from './validate.js'
import { ExportQueue } from './export/queue.js'
import {
  capabilities, isMissingKey, runFilm, runImage, runMotion, runScreen, runVector,
} from './ai/providers.js'
import type { BlockSpec } from './ai/types.js'
import { createReadStream } from 'node:fs'
import { Readable } from 'node:stream'

/**
 * The film API. Deliberately storage-agnostic: it is handed a DocStore and
 * never learns whether that is a filesystem, object storage or a database.
 */
/**
 * A store for one workspace. With accounts this is a new PgStore per request,
 * which is free: it holds a pool reference and an id. Without accounts, and in
 * local development, it is the same store every time.
 */
export type StoreFor = (workspace: string | null) => DocStore

export function createApp(
  storeFor: StoreFor, config: Config, queue?: ExportQueue,
  auth?: Auth, workspaceOf?: (userId: string) => Promise<string | null>,
  blobs?: { assets: BlobStore; exports: BlobStore },
) {
  const app = new Hono<{ Variables: { workspace: string | null } }>()

  app.use('*', logger())
  if (config.corsOrigins.length) {
    /**
     * The editor is a different origin from the api until they share a
     * hostname, and a session cookie has to survive that.
     *
     * A browser refuses to send credentials to a wildcard origin, so `*` is
     * echoed back as the caller's own origin rather than passed through. That
     * is only safe because it is paired with an explicit allowlist in
     * production: `CORS_ORIGINS` has no default there, so a misconfigured
     * deploy serves nothing rather than serving everyone.
     */
    const wildcard = config.corsOrigins.includes('*')
    app.use('/api/*', cors({
      origin: origin => (wildcard ? origin : config.corsOrigins.includes(origin) ? origin : null),
      allowMethods: ['GET', 'PUT', 'POST', 'DELETE', 'OPTIONS'],
      allowHeaders: ['content-type'],
      // without this the session cookie is never sent, and every call is a 401
      credentials: true,
    }))
  }

  // liveness for a load balancer or orchestrator
  app.get('/healthz', c => c.json({ ok: true, env: config.env }))

  if (auth) {
    // sign in, sign up, oauth callbacks, sign out
    app.on(['GET', 'POST'], '/api/auth/*', c => auth.handler(c.req.raw))

    /**
     * Public on purpose: the editor calls this before anyone is signed in, to
     * tell "signed out" apart from "this deployment has no accounts", and to
     * learn which social providers are actually configured.
     */
    app.get('/api/me', async c => {
      const session = await auth.api.getSession({ headers: c.req.raw.headers })
      const workspace = session
        ? session.session.activeOrganizationId ?? (await workspaceOf?.(session.user.id)) ?? null
        : null
      return c.json({
        user: session
          ? { id: session.user.id, email: session.user.email, name: session.user.name,
              image: session.user.image }
          : null,
        workspace,
        providers: config.auth
          ? [config.auth.google && 'google', config.auth.github && 'github'].filter(Boolean)
          : [],
      })
    })

    /**
     * Every other /api call carries the caller's workspace, or none.
     *
     * Resolving it here rather than per route means a route can never forget:
     * a handler asks for its store and gets one scoped to whoever is asking,
     * or a 401 before it runs.
     */
    app.use('/api/*', async (c, next) => {
      if (c.req.path.startsWith('/api/auth/') || c.req.path === '/api/me') return next()
      const session = await auth.api.getSession({ headers: c.req.raw.headers })
      if (!session) return c.json({ error: 'sign in required' }, 401)
      const workspace = session.session.activeOrganizationId
        ?? (await workspaceOf?.(session.user.id))
        ?? null
      if (!workspace) return c.json({ error: 'no workspace' }, 403)
      c.set('workspace', workspace)
      await next()
    })

  }

  app.get('/api/films', async c => {
    try {
      return c.json(await storeFor(c.get('workspace')).list())
    } catch (e) {
      return c.json({ error: `registry unavailable: ${String(e)}` }, 503)
    }
  })

  app.get('/api/assets', async c => {
    try {
      return c.json(await storeFor(c.get('workspace')).assets())
    } catch (e) {
      return c.json({ error: String(e) }, 503)
    }
  })

  app.get('/api/films/:slug', async c => {
    const slug = c.req.param('slug')
    if (!SLUG.test(slug)) return c.json({ error: 'bad slug' }, 400)
    const doc = await storeFor(c.get('workspace')).get(slug)
    return doc ? c.json(doc) : c.json({ error: 'not found' }, 404)
  })

  /**
   * PUT creates or replaces, which is what PUT means.
   *
   * It used to refuse a slug it had not seen, because the library was fixed and
   * a save could only ever overwrite. With accounts, a workspace starts empty
   * and the first save of a new film has to be able to land.
   *
   * A slug is only ever resolved inside the caller's own workspace, so this
   * cannot reach across to somebody else's film of the same name.
   */
  app.put('/api/films/:slug', async c => {
    const slug = c.req.param('slug')
    if (!SLUG.test(slug)) return c.json({ error: 'bad slug' }, 400)

    let body: unknown
    try {
      body = await c.req.json()
    } catch {
      return c.json({ error: 'body is not json' }, 400)
    }

    const checked = validateDoc(body)
    if ('error' in checked) return c.json(checked, 422)

    try {
      const store = storeFor(c.get('workspace'))
      const existed = await store.has(slug)
      await store.put(slug, checked)
      return c.json({ ok: true, slug, created: !existed }, existed ? 200 : 201)
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
      if (kind === 'film') {
        const blocks = Array.isArray(body.blocks) ? body.blocks : []
        if (!blocks.length) return c.json({ error: 'no block library supplied' }, 400)
        return c.json(await runFilm({
          prompt, model,
          size: body.size as [number, number],
          accent: typeof body.accent === 'string' ? body.accent : '#ff5c1a',
          blocks: blocks as BlockSpec[],
          enters: Array.isArray(body.enters) ? body.enters as string[] : [],
          transitions: Array.isArray(body.transitions) ? body.transitions as string[] : [],
        }))
      }
      if (kind === 'screen') {
        const blocks = Array.isArray(body.blocks) ? body.blocks : []
        if (!blocks.length) return c.json({ error: 'no block library supplied' }, 400)
        return c.json(await runScreen({
          prompt, model,
          size: body.size as [number, number],
          accent: typeof body.accent === 'string' ? body.accent : '#ff5c1a',
          blocks: blocks as BlockSpec[],
          // the client scores its own materialised proposal and sends back
          // what failed, so a retry is corrected rather than re-rolled
          feedback: typeof body.feedback === 'string' ? body.feedback : undefined,
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

  /**
   * Serving a local blob.
   *
   * Only exists for the filesystem store: with Azure the browser is handed a
   * SAS url and never comes back through us.
   *
   * Registered AFTER the auth gate on purpose. Hono runs middleware in
   * registration order, so a route declared above the gate is never gated at
   * all; this one was, and served any workspace's exports to anybody who could
   * guess a key.
   */
  if (blobs && !config.storage.connection) {
    app.get('/api/blob/:container/*', async c => {
      const container = c.req.param('container')
      if (container !== ASSETS && container !== EXPORTS) return c.json({ error: 'no' }, 404)
      const key = c.req.path.split(`/api/blob/${container}/`)[1] ?? ''
      // fail closed. an unauthenticated caller has no workspace, and a key
      // outside the caller's own prefix is somebody else's file: both are a
      // 404 rather than a read. ordering alone must never be the only guard
      const workspace = c.get('workspace')
      if (!workspace || !key.startsWith(`${workspace}/`)) return c.json({ error: 'not found' }, 404)
      const store = container === ASSETS ? blobs.assets : blobs.exports
      const body = await store.get(decodeURIComponent(key))
      if (!body) return c.json({ error: 'not found' }, 404)
      return new Response(Readable.toWeb(body) as ReadableStream, {
        headers: {
          'content-type': container === EXPORTS ? 'video/mp4' : 'application/octet-stream',
          'cache-control': 'private, max-age=300',
        },
      })
    })
  }

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
      }, c.get('workspace') ?? undefined)
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
      // with blob storage the browser fetches the file directly from a
      // short-lived url and never streams through us
      const key = queue.keyOf(id)
      if (key && blobs) return c.redirect(await blobs.exports.url(key, 600), 302)

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
