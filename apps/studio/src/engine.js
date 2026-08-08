// one-time boot of everything the canvas needs: canvaskit, the wasm engine,
// fonts, and the doc registry. react components await `boot()` and then draw
// synchronously through the shared painter.
import init, { render, register_font } from '../vendor/engine-pkg/whippan_engine.js'
import { paintFrame } from '../vendor/painter.js'

let booted = null

export function boot() {
  if (booted) return booted
  booted = (async () => {
    const [CK, , inter, mono, registry] = await Promise.all([
      window.CanvasKitInit({ locateFile: f => '/canvaskit/' + f }),
      init(),
      fetch('/fonts/Inter-Variable.ttf').then(r => r.arrayBuffer()),
      fetch('/fonts/JetBrainsMono-Regular.ttf').then(r => r.arrayBuffer()),
      fetch('/docs/examples/index.json').then(r => r.json()),
    ])
    register_font('inter', new Uint8Array(inter))
    register_font('mono', new Uint8Array(mono))
    return { CK, registry }
  })()
  return booted
}

export async function loadDoc(entry) {
  const stageUrl = entry.stage || `/docs/examples/${entry.slug}.stage.json`
  const animUrl = entry.anim || `/docs/examples/${entry.slug}.anim.json`
  const [stage, anim] = await Promise.all([
    fetch(stageUrl).then(r => r.json()),
    fetch(animUrl).then(r => r.json()),
  ])
  const { CK } = await boot()
  const images = new Map()
  const srcs = [...new Set(stage.scenes.flatMap(s => s.nodes)
    .filter(n => n.type === 'image' && n.src).map(n => n.src))]
  await Promise.all(srcs.map(async src => {
    const buf = await fetch(src).then(r => r.arrayBuffer())
    images.set(src, CK.MakeImageFromEncoded(new Uint8Array(buf)))
  }))
  return { entry, stage, anim, images, stageUrl, animUrl }
}

export { render, paintFrame }

// total length and per-scene global start times, derived from the stage
export function timing(stage) {
  let acc = 0
  const scenes = stage.scenes.map(s => {
    const start = acc
    acc += s.dur ?? 3
    return { id: s.id, start, dur: s.dur ?? 3, nodes: s.nodes }
  })
  return { dur: acc, scenes }
}
