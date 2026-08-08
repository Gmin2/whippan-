/*
 * BOARDS — the storyboard canvas
 *
 * laid out the way motion designers pin boards in figma: one COLUMN per
 * scene with its script note on a dark card up top, and the scene's
 * progression flowing downward — sampled moments through the scene so
 * you see entrance, settled state and exit at a glance. pannable,
 * zoomable, click any frame to drop into the editor at that moment.
 *
 * every frame is the engine's own render, cached once per doc into
 * half-res snapshots so pan/zoom repaints stay cheap.
 */
import { useEffect, useRef, useState } from 'react'
import { render, paintFrame, timing } from './engine.js'

const GAP = 90
const VGAP = 56
const NOTE_H = 150

export default function Boards({ ck, doc, onJump }) {
  const canvasRef = useRef(null)
  const surfRef = useRef(null)
  const cacheRef = useRef(null)
  const [vp, setVp] = useState(null)
  const [hover, setHover] = useState(null)

  const [sw, sh] = doc.stage.size ?? [1920, 1080]
  const bw = sw / 2
  const bh = sh / 2
  const tl = timing(doc.stage)

  // one column per scene, 2-5 sampled moments spread through its length
  const cols = tl.scenes.map((s, i) => {
    const n = Math.max(2, Math.min(5, Math.round(s.dur / 1.1)))
    const frames = Array.from({ length: n }, (_, j) => {
      const f = n === 1 ? 0.5 : j / (n - 1)
      return {
        at: s.start + s.dur * (0.12 + f * 0.84),
        y: NOTE_H + VGAP + j * (bh + VGAP),
      }
    })
    return {
      ...s, i, frames,
      x: i * (bw + GAP),
      note: doc.stage.scenes[i].note ?? null,
    }
  })
  const worldW = cols.length * (bw + GAP) - GAP
  const worldH = Math.max(...cols.map(c => NOTE_H + VGAP +
    c.frames.length * (bh + VGAP)))

  useEffect(() => {
    const el = canvasRef.current
    const box = el.parentElement.getBoundingClientRect()
    el.width = box.width * devicePixelRatio
    el.height = box.height * devicePixelRatio
    el.style.width = box.width + 'px'
    el.style.height = box.height + 'px'
    setVp({
      k: Math.min(box.width / (worldW + 200), (box.height - 60) / worldH, 1.2),
      x: 100 * Math.min(box.width / (worldW + 200), 1),
      y: 40,
    })
    const surface = ck.MakeCanvasSurface(el)
    const paint = new ck.Paint()
    paint.setAntiAlias(true)
    surfRef.current = { surface, skc: surface.getCanvas(), paint }

    // render every sampled frame once into half-res snapshots
    const cache = new Map()
    const off = ck.MakeSurface(bw, bh)
    const oc = off.getCanvas()
    const op = new ck.Paint()
    op.setAntiAlias(true)
    for (const c of cols) {
      for (const f of c.frames) {
        const cmds = JSON.parse(render(
          JSON.stringify(doc.stage), JSON.stringify(doc.anim), f.at))
        oc.save()
        oc.scale(0.5, 0.5)
        if (cmds[0]?.op === 'clear') {
          op.setColor(ck.parseColorString(cmds[0].color))
          oc.drawRect(ck.XYWHRect(0, 0, sw, sh), op)
          cmds.shift()
        }
        paintFrame(ck, oc, op, cmds, doc.images)
        oc.restore()
        cache.set(c.id + ':' + f.at, off.makeImageSnapshot())
      }
    }
    op.delete()
    off.delete()
    cacheRef.current = cache
    return () => {
      paint.delete()
      surface.delete()
      for (const img of cache.values()) img.delete()
      surfRef.current = null
      cacheRef.current = null
    }
  }, [doc])

  useEffect(() => {
    const s = surfRef.current
    const cache = cacheRef.current
    if (!s || !cache || !vp) return
    const { skc } = s
    skc.clear(ck.Color(23, 23, 23, 1))
    skc.save()
    skc.scale(devicePixelRatio, devicePixelRatio)
    skc.translate(vp.x, vp.y)
    skc.scale(vp.k, vp.k)
    for (const c of cols) {
      for (const f of c.frames) {
        const img = cache.get(c.id + ':' + f.at)
        if (img) skc.drawImageRect(img,
          ck.XYWHRect(0, 0, bw, bh),
          ck.XYWHRect(c.x, f.y, bw, bh), s.paint)
      }
    }
    skc.restore()
    s.surface.flush()
  }, [vp, doc])

  function frameAt(e) {
    const box = canvasRef.current.getBoundingClientRect()
    const wx = (e.clientX - box.left - vp.x) / vp.k
    const wy = (e.clientY - box.top - vp.y) / vp.k
    for (const c of cols) {
      if (wx < c.x || wx > c.x + bw) continue
      for (const f of c.frames) {
        if (wy >= f.y && wy <= f.y + bh) return { col: c, frame: f }
      }
    }
    return null
  }

  function onWheel(e) {
    e.preventDefault()
    if (e.ctrlKey || e.metaKey) {
      const box = canvasRef.current.getBoundingClientRect()
      const mx = e.clientX - box.left
      const my = e.clientY - box.top
      setVp(v => {
        const k = Math.min(3, Math.max(0.02, v.k * Math.exp(-e.deltaY * 0.01)))
        return { k, x: mx - (mx - v.x) * (k / v.k), y: my - (my - v.y) * (k / v.k) }
      })
    } else {
      setVp(v => ({ ...v, x: v.x - e.deltaX, y: v.y - e.deltaY }))
    }
  }

  if (!vp) {
    return (
      <div style={{ width: '100%', height: '100%' }}>
        <canvas ref={canvasRef} style={{ display: 'block' }} />
      </div>
    )
  }

  const px = (wx, wy) => [vp.x + wx * vp.k, vp.y + wy * vp.k]

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%',
                  overflow: 'hidden' }}
         onWheel={onWheel}>
      <canvas ref={canvasRef} style={{ display: 'block' }}
              onMouseMove={e => {
                const h = frameAt(e)
                setHover(h ? h.col.id + ':' + h.frame.at : null)
              }}
              onMouseLeave={() => setHover(null)}
              onClick={e => {
                const h = frameAt(e)
                if (h) onJump(h.frame.at, h.col.id)
              }} />
      {cols.map(c => {
        const [lx, ly] = px(c.x, 0)
        return (
          <div key={'n' + c.id} style={{
            position: 'absolute', pointerEvents: 'none',
            left: lx, top: ly, width: bw * vp.k, height: NOTE_H * vp.k,
            background: '#101d16', border: '1px solid #1d3327',
            borderRadius: 6 * vp.k, boxSizing: 'border-box',
            padding: `${14 * vp.k}px ${18 * vp.k}px`,
            color: '#cfe3d6', fontSize: Math.max(4, 15 * vp.k),
            lineHeight: 1.45, overflow: 'hidden',
          }}>
            <div style={{ color: '#6fa887', fontSize: Math.max(4, 12 * vp.k),
                          marginBottom: 5 * vp.k }}>
              {c.i + 1} · {c.id} · {c.start.toFixed(1)}s + {c.dur.toFixed(1)}s
            </div>
            {c.note ?? ''}
          </div>
        )
      })}
      {cols.map(c => c.frames.map(f => {
        const key = c.id + ':' + f.at
        const [lx, ly] = px(c.x, f.y)
        return (
          <div key={key} style={{
            position: 'absolute', pointerEvents: 'none',
            left: lx - 1.5, top: ly - 1.5,
            width: bw * vp.k + 3, height: bh * vp.k + 3,
            border: hover === key ? '2px solid #606de0'
                                  : '1px solid rgba(255,255,255,.08)',
            borderRadius: 3,
          }}>
            <span style={{
              position: 'absolute', top: '100%', right: 0, marginTop: 3,
              fontSize: 11, color: hover === key ? '#aab2f0' : '#6a6a68',
              fontVariantNumeric: 'tabular-nums',
            }}>{f.at.toFixed(2)}s</span>
          </div>
        )
      }))}
      <div style={{ position: 'absolute', top: 12, left: 16, fontSize: 12,
                    color: '#8a8a88' }}>
        {doc.entry.title} — {cols.length} scenes, {tl.dur.toFixed(1)}s ·
        scroll to pan, ⌘scroll to zoom, click a frame to edit
      </div>
    </div>
  )
}
