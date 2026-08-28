// one-time boot of canvaskit + the wasm engine + fonts + the film registry.
// every pixel the gallery draws goes through render() and paintFrame(); there
// is no second render path.
import init, { render, register_font, sfx } from '@whippan/engine-web'
import wasmUrl from '@whippan/engine-web/pkg/whippan_engine_bg.wasm?url'
import { paintFrame } from '@whippan/engine-web/painter'
import type { Anim, Doc, Entry, Stage } from './types'

export interface Engine {
  CK: CanvasKit
  registry: Entry[]
}

let booted: Promise<Engine> | null = null

export function boot(): Promise<Engine> {
  if (booted) return booted
  booted = (async () => {
    const [CK, , inter, mono, registry] = await Promise.all([
      window.CanvasKitInit({ locateFile: f => '/canvaskit/' + f }),
      init(wasmUrl),
      fetch('/fonts/Inter-Variable.ttf').then(r => r.arrayBuffer()),
      fetch('/fonts/JetBrainsMono-Regular.ttf').then(r => r.arrayBuffer()),
      fetch('/docs/examples/index.json').then(r => r.json() as Promise<Entry[]>),
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
    const stageUrl = entry.stage ?? `/docs/examples/${entry.slug}.stage.json`
    const animUrl = entry.anim ?? `/docs/examples/${entry.slug}.anim.json`
    const [stage, anim] = await Promise.all([
      fetch(stageUrl).then(r => {
        if (!r.ok) throw new Error(`missing ${stageUrl}`)
        return r.json() as Promise<Stage>
      }),
      fetch(animUrl).then(r => {
        if (!r.ok) throw new Error(`missing ${animUrl}`)
        return r.json() as Promise<Anim>
      }),
    ])
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

export { render, sfx, paintFrame }
