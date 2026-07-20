/* ─────────────────────────────────────────────────────────
 * STAGE — the direct-manipulation surface
 *
 * engine renders every pixel; react owns the interactions:
 *   wheel            pan the viewport
 *   cmd/ctrl+wheel   zoom about the cursor
 *   space+drag       pan
 *   click            select (hover shows a light outline first)
 *   drag node        move, with snap guides to canvas + sibling centers
 *   corner/edge      resize (shift keeps aspect); text corners scale type
 *   handle above     rotate, magnetic near 0/90
 *   arrows           nudge 1px (shift 10px), esc deselects
 * ───────────────────────────────────────────────────────── */
import { useEffect, useRef, useState } from 'react'
import { render, paintFrame, timing } from './engine.js'

const UI = {
  accent: '#606de0',
  guide: '#f24822',
  handle: 8,          // css px, hit + draw size
  snap: 6,            // css px
  rotOffset: 26,      // css px above the box
  zoomMin: 0.05,
  zoomMax: 8,
}

export default function Stage({ ck, doc, t, selection, onSelect, onEdit }) {
  const wrapRef = useRef(null)
  const canvasRef = useRef(null)
  const surfRef = useRef(null)
  const [view, setView] = useState({ zoom: 1, x: 0, y: 0 })   // extra on top of fit
  const [fitW, setFitW] = useState(800)
  const [hover, setHover] = useState(null)
  const [guides, setGuides] = useState([])
  const [cursor, setCursor] = useState('default')
  const drag = useRef(null)
  const space = useRef(false)

  const [w, h] = doc.stage.size

  useEffect(() => {
    const measure = () => {
      const r = wrapRef.current?.getBoundingClientRect()
      if (!r) return
      const fit = Math.min((r.width - 90) / w, (r.height - 110) / h, 1)
      setFitW(Math.max(120, Math.round(w * fit)))
    }
    measure()
    addEventListener('resize', measure)
    return () => removeEventListener('resize', measure)
  }, [w, h, doc.entry.slug])

  useEffect(() => {
    const surface = ck.MakeCanvasSurface(canvasRef.current)
    const paint = new ck.Paint()
    paint.setAntiAlias(true)
    surfRef.current = { surface, skc: surface.getCanvas(), paint }
    return () => { paint.delete(); surface.delete(); surfRef.current = null }
  }, [ck, doc.entry.slug, w, h])

  // draw current frame + selection/hover/guide overlays
  useEffect(() => {
    const s = surfRef.current
    if (!s) return
    const cmds = JSON.parse(render(
      JSON.stringify(doc.stage), JSON.stringify(doc.anim), t))
    paintFrame(ck, s.skc, s.paint, cmds, doc.images)
    const scale = displayScale()
    if (hover && !isSame(hover, selection))
      drawBox(ck, s.skc, nodeBox(doc, hover, t), 1.5 / scale, false)
    if (selection) {
      const box = nodeBox(doc, selection, t)
      if (box) drawBox(ck, s.skc, box, 2 / scale, true, UI.handle / scale,
                       UI.rotOffset / scale)
    }
    for (const g of guides) drawGuide(ck, s.skc, g, w, h, 1.5 / scale)
    s.surface.flush()
  })

  // keyboard: nudge + deselect + spacebar pan mode
  useEffect(() => {
    const down = e => {
      if (e.code === 'Space') { space.current = true; setCursor('grab') }
      if (!selection) return
      const step = e.shiftKey ? 10 : 1
      const dx = e.key === 'ArrowLeft' ? -step : e.key === 'ArrowRight' ? step : 0
      const dy = e.key === 'ArrowUp' ? -step : e.key === 'ArrowDown' ? step : 0
      if (dx || dy) {
        e.preventDefault()
        onEdit(d => {
          const n = findNode(d, selection)
          if (n) { n.x += dx; n.y += dy }
        })
      }
      if (e.key === 'Escape') onSelect(null)
    }
    const up = e => {
      if (e.code === 'Space') { space.current = false; setCursor('default') }
    }
    addEventListener('keydown', down)
    addEventListener('keyup', up)
    return () => { removeEventListener('keydown', down); removeEventListener('keyup', up) }
  }, [selection, onEdit, onSelect])

  function displayScale() {
    const r = canvasRef.current?.getBoundingClientRect()
    return r ? r.width / w : 1
  }

  function docPoint(ev) {
    const r = canvasRef.current.getBoundingClientRect()
    return [(ev.clientX - r.left) * (w / r.width),
            (ev.clientY - r.top) * (h / r.height)]
  }

  function activeScene() {
    const { scenes } = timing(doc.stage)
    return scenes.find(s => t >= s.start && t < s.start + s.dur)
      ?? scenes[scenes.length - 1]
  }

  function hitNode(p) {
    const sc = activeScene()
    for (const n of [...sc.nodes].reverse()) {
      const b = boxOf(n)
      if (Math.abs(p[0] - n.x) <= b.w / 2 && Math.abs(p[1] - n.y) <= b.h / 2)
        return { sceneId: sc.id, nodeId: n.id }
    }
    return null
  }

  function hitHandle(p) {
    if (!selection) return null
    const box = nodeBox(doc, selection, t)
    if (!box) return null
    const s = displayScale()
    const hs = UI.handle / s
    const { x, y, w: bw, h: bh } = box
    const pts = {
      nw: [x - bw / 2, y - bh / 2], n: [x, y - bh / 2], ne: [x + bw / 2, y - bh / 2],
      e: [x + bw / 2, y], se: [x + bw / 2, y + bh / 2], s: [x, y + bh / 2],
      sw: [x - bw / 2, y + bh / 2], w: [x - bw / 2, y],
      rot: [x, y - bh / 2 - UI.rotOffset / s],
    }
    for (const [id, [hx, hy]] of Object.entries(pts))
      if (Math.abs(p[0] - hx) <= hs && Math.abs(p[1] - hy) <= hs) return id
    return null
  }

  function snapTargets() {
    const sc = activeScene()
    const xs = [w / 2], ys = [h / 2]
    for (const n of sc.nodes) {
      if (selection && n.id === selection.nodeId) continue
      xs.push(n.x); ys.push(n.y)
    }
    return { xs, ys }
  }

  function onDown(ev) {
    if (space.current || ev.button === 1) {
      drag.current = { kind: 'pan', sx: ev.clientX, sy: ev.clientY,
                       vx: view.x, vy: view.y }
      setCursor('grabbing')
      return
    }
    const p = docPoint(ev)
    const handle = hitHandle(p)
    if (handle) {
      const n = findNode(doc, selection)
      drag.current = {
        kind: handle === 'rot' ? 'rotate' : 'resize',
        handle, start: p,
        orig: { x: n.x, y: n.y, w: n.w, h: n.h, rot: n.rot ?? 0,
                size: n.font?.size },
      }
      return
    }
    const hitR = hitNode(p)
    onSelect(hitR)
    if (hitR) {
      const n = findNode(doc, hitR)
      drag.current = { kind: 'move', sel: hitR, start: p,
                       orig: { x: n.x, y: n.y } }
      setCursor('move')
    }
  }

  function onMove(ev) {
    const d = drag.current
    if (!d) {
      const p = docPoint(ev)
      const handle = hitHandle(p)
      if (handle) {
        setCursor(handleCursor(handle))
        setHover(null)
      } else {
        setCursor(space.current ? 'grab' : 'default')
        setHover(hitNode(p))
      }
      return
    }
    if (d.kind === 'pan') {
      setView(v => ({ ...v, x: d.vx + ev.clientX - d.sx, y: d.vy + ev.clientY - d.sy }))
      return
    }
    const p = docPoint(ev)
    const dx = p[0] - d.start[0]
    const dy = p[1] - d.start[1]
    const s = displayScale()

    if (d.kind === 'move') {
      let nx = d.orig.x + dx
      let ny = d.orig.y + dy
      const { xs, ys } = snapTargets()
      const gs = []
      const tol = UI.snap / s
      for (const cx of xs) if (Math.abs(nx - cx) < tol) { nx = cx; gs.push({ axis: 'x', at: cx }); break }
      for (const cy of ys) if (Math.abs(ny - cy) < tol) { ny = cy; gs.push({ axis: 'y', at: cy }); break }
      setGuides(gs)
      onEdit(dd => {
        const n = findNode(dd, d.sel)
        if (n) { n.x = Math.round(nx); n.y = Math.round(ny) }
      })
    }

    if (d.kind === 'resize') {
      onEdit(dd => {
        const n = findNode(dd, selection)
        if (!n) return
        resizeNode(n, d, dx, dy, ev.shiftKey)
      })
    }

    if (d.kind === 'rotate') {
      const n0 = findNode(doc, selection)
      const ang = Math.atan2(p[1] - n0.y, p[0] - n0.x) * 180 / Math.PI + 90
      let rot = ((ang + 540) % 360) - 180
      for (const m of [0, 90, -90, 180]) if (Math.abs(rot - m) < 4) rot = m
      onEdit(dd => {
        const n = findNode(dd, selection)
        if (n) n.rot = Math.round(rot * 10) / 10
      })
    }
  }

  function onUp() {
    if (drag.current?.kind === 'move' || drag.current?.kind === 'pan')
      setCursor(space.current ? 'grab' : 'default')
    drag.current = null
    setGuides([])
  }

  function onWheel(ev) {
    ev.preventDefault()
    if (ev.metaKey || ev.ctrlKey) {
      const factor = Math.exp(-ev.deltaY * 0.01)
      setView(v => {
        const zoom = clamp(v.zoom * factor, UI.zoomMin, UI.zoomMax)
        const k = zoom / v.zoom
        // zoom about the cursor: keep the point under the pointer fixed
        const r = wrapRef.current.getBoundingClientRect()
        const cx = ev.clientX - r.left - r.width / 2
        const cy = ev.clientY - r.top - r.height / 2
        return { zoom, x: cx - (cx - v.x) * k, y: cy - (cy - v.y) * k }
      })
    } else {
      setView(v => ({ ...v, x: v.x - ev.deltaX, y: v.y - ev.deltaY }))
    }
  }

  useEffect(() => {
    const el = wrapRef.current
    el.addEventListener('wheel', onWheel, { passive: false })
    return () => el.removeEventListener('wheel', onWheel)
  })

  return (
    <div
      ref={wrapRef}
      style={{ position: 'absolute', inset: 0, overflow: 'hidden',
               display: 'grid', placeItems: 'center', cursor }}
      onMouseDown={onDown}
      onMouseMove={onMove}
      onMouseUp={onUp}
      onMouseLeave={onUp}
    >
      <div style={{
        transform: `translate(${view.x}px, ${view.y}px) scale(${view.zoom})`,
      }}>
        <canvas
          ref={canvasRef}
          width={w}
          height={h}
          style={{
            width: fitW,
            borderRadius: 8, background: '#000',
            boxShadow: '0 1px 2px rgba(0,0,0,.5), 0 18px 60px rgba(0,0,0,.45)',
          }}
        />
      </div>
      <ZoomChip view={view} onReset={() => setView({ zoom: 1, x: 0, y: 0 })} />
    </div>
  )
}

function ZoomChip({ view, onReset }) {
  return (
    <div
      onMouseDown={e => { e.stopPropagation(); onReset() }}
      title="reset view"
      style={{
        position: 'absolute', top: 12, right: 14, padding: '3px 10px',
        background: '#101010', border: '1px solid #262626', borderRadius: 8,
        fontSize: 11, color: '#9a9a97', cursor: 'pointer',
        fontFamily: 'ui-monospace, monospace',
      }}
    >{Math.round(view.zoom * 100)}%</div>
  )
}

/* ---------- doc helpers ---------- */

function findNode(doc, sel) {
  if (!sel) return null
  const stage = doc.stage ?? doc
  const sc = stage.scenes.find(s => s.id === sel.sceneId)
  return sc?.nodes.find(n => n.id === sel.nodeId)
}

function boxOf(n) {
  return {
    w: n.w ?? (n.text ? n.text.length * (n.font?.size ?? 48) * 0.5 : 80),
    h: n.h ?? (n.font?.size ?? 48) * 1.3,
  }
}

function nodeBox(doc, sel, t) {
  const { scenes } = timing(doc.stage)
  const sc = scenes.find(s => s.id === sel.sceneId)
  if (!sc || !(t >= sc.start && t < sc.start + sc.dur)) return null
  const n = sc.nodes.find(n => n.id === sel.nodeId)
  if (!n) return null
  return { x: n.x, y: n.y, ...boxOf(n) }
}

function isSame(a, b) {
  return a && b && a.nodeId === b.nodeId && a.sceneId === b.sceneId
}

function resizeNode(n, d, dx, dy, keepAspect) {
  const o = d.orig
  const sx = d.handle.includes('w') ? -1 : d.handle.includes('e') ? 1 : 0
  const sy = d.handle.includes('n') ? -1 : d.handle.includes('s') ? 1 : 0
  if (n.font && sx && sy) {
    // text corners scale the type
    const base = Math.hypot((o.w ?? 200), (o.h ?? 60))
    const now = Math.hypot((o.w ?? 200) + sx * dx * 2, (o.h ?? 60) + sy * dy * 2)
    n.font.size = Math.max(6, Math.round((o.size ?? 48) * now / base))
    return
  }
  if (o.w == null) return
  let nw = sx ? Math.max(4, o.w + sx * dx * 2) : o.w
  let nh = sy ? Math.max(4, o.h + sy * dy * 2) : o.h
  if (keepAspect && sx && sy) {
    const k = Math.max(nw / o.w, nh / o.h)
    nw = o.w * k; nh = o.h * k
  }
  n.w = Math.round(nw)
  n.h = Math.round(nh)
}

function handleCursor(h) {
  return {
    n: 'ns-resize', s: 'ns-resize', e: 'ew-resize', w: 'ew-resize',
    ne: 'nesw-resize', sw: 'nesw-resize', nw: 'nwse-resize', se: 'nwse-resize',
    rot: 'crosshair',
  }[h] ?? 'default'
}

/* ---------- overlay drawing (in doc space) ---------- */

function drawBox(ck, skc, box, sw, withHandles, hs = 0, rotOff = 0) {
  if (!box) return
  const { x, y, w, h } = box
  const p = new ck.Paint()
  p.setAntiAlias(true)
  p.setStyle(ck.PaintStyle.Stroke)
  p.setStrokeWidth(sw)
  p.setColor(ck.Color(96, 109, 224, 1))
  skc.drawRect(ck.LTRBRect(x - w / 2, y - h / 2, x + w / 2, y + h / 2), p)
  if (withHandles) {
    const fill = new ck.Paint()
    fill.setAntiAlias(true)
    fill.setColor(ck.Color(255, 255, 255, 1))
    const half = hs / 2
    const corners = [
      [x - w / 2, y - h / 2], [x, y - h / 2], [x + w / 2, y - h / 2],
      [x + w / 2, y], [x + w / 2, y + h / 2], [x, y + h / 2],
      [x - w / 2, y + h / 2], [x - w / 2, y],
    ]
    for (const [cx, cy] of corners) {
      skc.drawRect(ck.LTRBRect(cx - half, cy - half, cx + half, cy + half), fill)
      skc.drawRect(ck.LTRBRect(cx - half, cy - half, cx + half, cy + half), p)
    }
    // rotation stem + knob
    skc.drawLine(x, y - h / 2, x, y - h / 2 - rotOff, p)
    skc.drawCircle(x, y - h / 2 - rotOff, half, fill)
    skc.drawCircle(x, y - h / 2 - rotOff, half, p)
    fill.delete()
  }
  p.delete()
}

function drawGuide(ck, skc, g, w, h, sw) {
  const p = new ck.Paint()
  p.setAntiAlias(true)
  p.setStyle(ck.PaintStyle.Stroke)
  p.setStrokeWidth(sw)
  p.setColor(ck.Color(242, 72, 34, 1))
  if (g.axis === 'x') skc.drawLine(g.at, 0, g.at, h, p)
  else skc.drawLine(0, g.at, w, g.at, p)
  p.delete()
}

function clamp(v, a, b) {
  return Math.max(a, Math.min(b, v))
}
