// one-time boot of canvaskit + the wasm engine + fonts + the registry;
// the gallery draws through the shared painter exactly like the studio.
import init, { render, register_font } from '@whippan/engine-web'
import wasmUrl from '@whippan/engine-web/pkg/whippan_engine_bg.wasm?url'
import { paintFrame } from '@whippan/engine-web/painter'

let booted = null

export function boot() {
  if (booted) return booted
  booted = (async () => {
    const [CK, , inter, mono, registry] = await Promise.all([
      window.CanvasKitInit({ locateFile: f => '/canvaskit/' + f }),
      init(wasmUrl),
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
    fetch(stageUrl).then(r => {
      if (!r.ok) throw new Error(`missing ${stageUrl}`)
      return r.json()
    }),
    fetch(animUrl).then(r => {
      if (!r.ok) throw new Error(`missing ${animUrl}`)
      return r.json()
    }),
  ])
  const { CK } = await boot()
  const images = new Map()
  const srcs = [...new Set(stage.scenes.flatMap(s => s.nodes)
    .flatMap(n => {
      if (n.type === 'image' && n.src) return [n.src]
      if (n.type === 'seq' && n.src) {
        return Array.from({ length: n.count ?? 0 },
          (_, i) => n.src + 'f' + String(i).padStart(3, '0') + '.png')
      }
      return []
    }))]
  await Promise.all(srcs.map(async src => {
    const buf = await fetch(src).then(r => r.arrayBuffer())
    images.set(src, CK.MakeImageFromEncoded(new Uint8Array(buf)))
  }))
  return { entry, stage, anim, images }
}

export function docDur(stage) {
  return stage.scenes.reduce((a, s) => a + (s.dur ?? 3), 0)
}

export { render, paintFrame }
