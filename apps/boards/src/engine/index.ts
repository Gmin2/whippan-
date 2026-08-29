// one-time boot of canvaskit + the wasm engine + fonts + the film registry.
// every pixel the gallery draws goes through render() and paintFrame(); there
// is no second render path.
import init, { render, register_font, sfx, timeline } from '@whippan/engine-web'
import wasmUrl from '@whippan/engine-web/pkg/whippan_engine_bg.wasm?url'
import { paintFrame } from '@whippan/engine-web/painter'
import type { Anim, Asset, Doc, Entry, Stage } from './types'
import { hitTest, measure } from '../measure'

export interface Engine {
  CK: CanvasKit
  registry: Entry[]
}

/**
 * Where the film API lives. Same origin by default, which is how it runs
 * deployed behind one host; VITE_API_BASE points it elsewhere for a split
 * deployment or a remote backend during development.
 */
const API = import.meta.env.VITE_API_BASE ?? ''

let booted: Promise<Engine> | null = null

export function boot(): Promise<Engine> {
  if (booted) return booted
  booted = (async () => {
    const [CK, , inter, mono, registry] = await Promise.all([
      window.CanvasKitInit({ locateFile: f => '/canvaskit/' + f }),
      init(wasmUrl),
      fetch('/fonts/Inter-Variable.ttf').then(r => r.arrayBuffer()),
      fetch('/fonts/JetBrainsMono-Regular.ttf').then(r => r.arrayBuffer()),
      fetch(`${API}/api/films`).then(r => {
        if (!r.ok) throw new Error(`registry unavailable (${r.status})`)
        return r.json() as Promise<Entry[]>
      }),
    ])
    // the engine shapes its own text, so an unregistered font is a blank
    // film rather than a fallback face
    register_font('inter', new Uint8Array(inter))
    register_font('mono', new Uint8Array(mono))
    return { CK, registry }
  })()
  return booted
}

function imageSources(stage: Stage): string[] {
  const srcs = stage.scenes
    .flatMap(s => s.nodes)
    .flatMap(n => {
      if (n.type === 'image' && n.src) return [n.src]
      if (n.type === 'seq' && n.src) {
        return Array.from({ length: n.count ?? 0 },
          (_, i) => n.src + 'f' + String(i).padStart(3, '0') + '.png')
      }
      return []
    })
  return [...new Set(srcs)]
}

const docCache = new Map<string, Promise<Doc>>()

export function loadDoc(entry: Entry): Promise<Doc> {
  const hit = docCache.get(entry.slug)
  if (hit) return hit
  const job = (async (): Promise<Doc> => {
    // documents come from the api, not from static files: that is what lets
    // the editor behave the same locally and deployed
    const res = await fetch(`${API}/api/films/${encodeURIComponent(entry.slug)}`)
    if (!res.ok) throw new Error(`could not load ${entry.slug} (${res.status})`)
    const { stage, anim } = await res.json() as { stage: Stage; anim: Anim }
    const { CK } = await boot()
    const images = new Map<string, unknown>()
    await Promise.all(imageSources(stage).map(async src => {
      const buf = await fetch(src).then(r => r.arrayBuffer())
      images.set(src, CK.MakeImageFromEncoded(new Uint8Array(buf)))
    }))
    return { entry, stage, anim, images }
  })()
  docCache.set(entry.slug, job)
  return job
}

export function docDur(stage: Stage): number {
  return stage.scenes.reduce((a, s) => a + (s.dur ?? 3), 0)
}

/** the frame at t, painted onto an already-prepared surface */
export function drawFrame(
  CK: CanvasKit, skc: unknown, paint: SkPaint, doc: Doc, t: number,
): void {
  paintFrame(CK, skc, paint,
    JSON.parse(render(JSON.stringify(doc.stage), JSON.stringify(doc.anim), t)),
    doc.images)
}

// One engine-rendered still per film, cached as a data url. The index wall
// and the hover cards share this map, so a film is rasterized at most once
// per session.
const posterCache = new Map<string, string>()

export function cachedPoster(slug: string): string | undefined {
  return posterCache.get(slug)
}

async function cutPoster(CK: CanvasKit, entry: Entry): Promise<string> {
  const hit = posterCache.get(entry.slug)
  if (hit) return hit
  const doc = await loadDoc(entry)
  const [w, h] = doc.stage.size
  const canvas = document.createElement('canvas')
  canvas.width = w
  canvas.height = h
  const make = CK.MakeSWCanvasSurface ?? CK.MakeCanvasSurface
  const surface = make.call(CK, canvas)
  const paint = new CK.Paint()
  paint.setAntiAlias(true)
  // 40% in lands past the entrance and before the exit on nearly every doc
  drawFrame(CK, surface.getCanvas(), paint, doc,
    entry.poster ?? docDur(doc.stage) * 0.4)
  surface.flush()
  const url = canvas.toDataURL('image/png')
  paint.delete()
  surface.delete()
  posterCache.set(entry.slug, url)
  return url
}

// Cutting a poster pulls a doc's json, fonts and images, so the wall cuts
// them one at a time in request order rather than 37 at once on first paint.
let queue: Promise<unknown> = Promise.resolve()

export function queuePoster(CK: CanvasKit, entry: Entry): Promise<string | null> {
  const job = queue.then(() => cutPoster(CK, entry).catch(() => null))
  queue = job
  return job
}

export { render, sfx, timeline, paintFrame }

/** absolute start time of each scene, in order */
export function sceneStarts(stage: Stage): number[] {
  let t = 0
  return stage.scenes.map(s => { const at = t; t += s.dur ?? 3; return at })
}

// One still per SCENE rather than per film: boards shows a whole document
// laid out, so every scene needs its own frame. Cut at the scene midpoint,
// which is past the entrance and before the exit on nearly every scene.
const sceneCache = new Map<string, string>()

export function sceneKey(doc: Doc, i: number, rev: number): string {
  return `${doc.entry.slug}:${rev}:${i}`
}

export function cachedScene(key: string): string | undefined {
  return sceneCache.get(key)
}

async function cutScene(
  CK: CanvasKit, doc: Doc, i: number, w: number, rev: number,
): Promise<string> {
  const key = sceneKey(doc, i, rev)
  const hit = sceneCache.get(key)
  if (hit) return hit
  const [dw, dh] = doc.stage.size
  const h = Math.round((w * dh) / dw)
  const canvas = document.createElement('canvas')
  canvas.width = w
  canvas.height = h
  const make = CK.MakeSWCanvasSurface ?? CK.MakeCanvasSurface
  const surface = make.call(CK, canvas)
  const paint = new CK.Paint()
  paint.setAntiAlias(true)
  const skc = surface.getCanvas() as { scale(x: number, y: number): void }
  skc.scale(w / dw, h / dh)
  const starts = sceneStarts(doc.stage)
  drawFrame(CK, skc, paint, doc, starts[i] + (doc.stage.scenes[i].dur ?? 3) * 0.5)
  surface.flush()
  const url = canvas.toDataURL('image/png')
  paint.delete()
  surface.delete()
  sceneCache.set(key, url)
  return url
}

let sceneQueue: Promise<unknown> = Promise.resolve()

export function queueScene(
  CK: CanvasKit, doc: Doc, i: number, w: number, rev: number,
): Promise<string | null> {
  const job = sceneQueue.then(() => cutScene(CK, doc, i, w, rev).catch(() => null))
  sceneQueue = job
  return job
}

// dev hook: the booted engine on window, so the editor work can be probed
// from the console and from automation without a second wasm instance
if (import.meta.env.DEV) {
  boot().then(({ CK, registry }) => {
    ;(window as unknown as Record<string, unknown>).whippan =
      { CK, registry, render, sfx, timeline, loadDoc, docDur, sceneStarts, measure, hitTest }
  })
}

/** the images a document can reference */
export async function listAssets(): Promise<Asset[]> {
  const res = await fetch(`${API}/api/assets`)
  if (!res.ok) throw new Error(`assets unavailable (${res.status})`)
  return res.json() as Promise<Asset[]>
}

/** load an image the engine has not seen yet, so a new node paints at once */
export async function ensureImage(CK: CanvasKit, doc: Doc, src: string): Promise<void> {
  if (doc.images.has(src)) return
  const buf = await fetch(src).then(r => r.arrayBuffer())
  doc.images.set(src, CK.MakeImageFromEncoded(new Uint8Array(buf)))
}

/** write a document back to the repo through the dev server */
export async function saveDoc(
  slug: string, stage: Stage, anim: Anim,
): Promise<void> {
  const res = await fetch(`${API}/api/films/${encodeURIComponent(slug)}`, {
    method: 'PUT',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ stage, anim }),
  })
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ error: res.statusText }))
    throw new Error((detail as { error?: string }).error ?? `save failed (${res.status})`)
  }
}

/** an export job, as the api reports it */
export interface ExportJob {
  id: string
  slug: string
  status: 'queued' | 'running' | 'done' | 'failed' | 'cancelled'
  progress: number | null
  frames?: number
  totalFrames?: number
  bytes?: number
  error?: string
  log?: string
  downloadUrl?: string
  options: { fps: number; supersample: 1 | 2 }
  queuedAt: number
  startedAt?: number
  finishedAt?: number
}

/** queue a render of the document as it stands, unsaved edits included */
export async function startExport(
  slug: string, stage: Stage, anim: Anim,
  opts: { fps?: number; supersample?: 1 | 2 } = {},
): Promise<ExportJob> {
  const res = await fetch(`${API}/api/films/${encodeURIComponent(slug)}/export`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ stage, anim, ...opts }),
  })
  const body = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error((body as { error?: string }).error ?? `export failed (${res.status})`)
  return body as ExportJob
}

export async function pollExport(id: string): Promise<ExportJob> {
  const res = await fetch(`${API}/api/exports/${encodeURIComponent(id)}`)
  if (!res.ok) throw new Error(`job ${id} is gone`)
  return res.json() as Promise<ExportJob>
}

export async function cancelExport(id: string): Promise<void> {
  await fetch(`${API}/api/exports/${encodeURIComponent(id)}`, { method: 'DELETE' })
}

export const exportFileUrl = (id: string) => `${API}/api/exports/${id}/file`
