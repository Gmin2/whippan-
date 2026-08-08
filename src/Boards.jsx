/*
 * BOARDS — the storyboard canvas
 *
 * every scene of the film rendered side by side on one pannable,
 * zoomable surface: the wall of boards a motion designer pins up before
 * animating. each board is the engine's own render of that scene partway
 * through (so reveals and rises have landed), labels carry id, start and
 * duration, and clicking a board drops into the editor at that moment.
 */
import { useEffect, useRef, useState } from 'react'
import { render, paintFrame, timing } from './engine.js'

const GAP = 140
const LABEL = 74

export default function Boards({ ck, doc, onJump }) {
  const canvasRef = useRef(null)
  const surfRef = useRef(null)
  const [vp, setVp] = useState(null)
  const [hover, setHover] = useState(-1)

  const [sw, sh] = doc.stage.size ?? [1920, 1080]
  const tl = timing(doc.stage)
  const boards = tl.scenes.map((s, i) => ({
    ...s,
    x: i * (sw + GAP),
    // far enough in that entrances have settled, before exit motion
    at: s.start + Math.min(s.dur * 0.55, s.dur - 0.05),
  }))
  const worldW = boards.length * (sw + GAP) - GAP
  const worldH = sh + LABEL

  useEffect(() => {
    const el = canvasRef.current
    const fit = () => {
      const box = el.parentElement.getBoundingClientRect()
      el.width = box.width * devicePixelRatio
      el.height = box.height * devicePixelRatio
      el.style.width = box.width + 'px'
      el.style.height = box.height + 'px'
      const k = Math.min(box.width / (worldW + 240), (box.height - 120) / worldH)
      setVp(v => v ?? {
        k,
        x: (box.width - worldW * k) / 2,
        y: (box.height - worldH * k) / 2,
      })
    }
    fit()
    const surface = ck.MakeCanvasSurface(el)
    const paint = new ck.Paint()
    paint.setAntiAlias(true)
    surfRef.current = { surface, skc: surface.getCanvas(), paint }
    return () => { paint.delete(); surface.delete(); surfRef.current = null }
  }, [doc])

  useEffect(() => {
    const s = surfRef.current
    if (!s || !vp) return
    const { skc } = s
    skc.clear(ck.Color(23, 23, 23, 1))
    for (const b of boards) {
      const cmds = JSON.parse(render(
        JSON.stringify(doc.stage), JSON.stringify(doc.anim), b.at))
      skc.save()
      skc.scale(devicePixelRatio, devicePixelRatio)
      skc.translate(vp.x + b.x * vp.k, vp.y)
      skc.scale(vp.k, vp.k)
      skc.clipRect(ck.XYWHRect(0, 0, sw, sh), ck.ClipOp.Intersect, true)
      // the engine's leading clear would wipe the whole surface (clear
      // ignores clip); paint it as this board's backdrop instead
      if (cmds[0]?.op === 'clear') {
        s.paint.setColor(ck.parseColorString(cmds[0].color))
        skc.drawRect(ck.XYWHRect(0, 0, sw, sh), s.paint)
        cmds.shift()
      }
      paintFrame(ck, skc, s.paint, cmds, doc.images)
      skc.restore()
    }
    s.surface.flush()
  }, [vp, doc, hover])

  function toWorld(e) {
    const box = canvasRef.current.getBoundingClientRect()
    return [(e.clientX - box.left - vp.x) / vp.k,
            (e.clientY - box.top - vp.y) / vp.k]
  }

  function boardAt(e) {
    const [wx, wy] = toWorld(e)
    if (wy < 0 || wy > sh) return -1
    const slot = Math.floor(wx / (sw + GAP))
    if (slot < 0 || slot >= boards.length) return -1
    return wx - slot * (sw + GAP) <= sw ? slot : -1
  }

  function onWheel(e) {
    e.preventDefault()
    if (e.ctrlKey || e.metaKey) {
      const box = canvasRef.current.getBoundingClientRect()
      const mx = e.clientX - box.left
      const my = e.clientY - box.top
      setVp(v => {
        const k = Math.min(2, Math.max(0.02, v.k * Math.exp(-e.deltaY * 0.01)))
        return { k, x: mx - (mx - v.x) * (k / v.k), y: my - (my - v.y) * (k / v.k) }
      })
    } else {
      setVp(v => ({ ...v, x: v.x - e.deltaX, y: v.y - e.deltaY }))
    }
  }

  if (!vp) return <canvas ref={canvasRef} style={{ display: 'block' }} />

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%',
                  overflow: 'hidden' }}
         onWheel={onWheel}>
      <canvas ref={canvasRef} style={{ display: 'block' }}
              onMouseMove={e => setHover(boardAt(e))}
              onMouseLeave={() => setHover(-1)}
              onClick={e => {
                const i = boardAt(e)
                if (i >= 0) onJump(boards[i].start, boards[i].id)
              }} />
      {boards.map((b, i) => (
        <div key={b.id} style={{
          position: 'absolute', pointerEvents: 'none',
          left: vp.x + b.x * vp.k,
          top: vp.y + sh * vp.k + 10,
          width: sw * vp.k,
          display: 'flex', justifyContent: 'space-between',
          fontSize: 12, color: i === hover ? '#fff' : '#8a8a88',
          fontVariantNumeric: 'tabular-nums',
        }}>
          <span>{i + 1} · {b.id}</span>
          <span>{b.start.toFixed(1)}s + {b.dur.toFixed(1)}s</span>
        </div>
      ))}
      {boards.map((b, i) => i === hover && (
        <div key={'h' + b.id} style={{
          position: 'absolute', pointerEvents: 'none',
          left: vp.x + b.x * vp.k - 2, top: vp.y - 2,
          width: sw * vp.k + 4, height: sh * vp.k + 4,
          border: '2px solid #606de0', borderRadius: 3,
        }} />
      ))}
      <div style={{ position: 'absolute', top: 14, left: 18, fontSize: 12,
                    color: '#8a8a88' }}>
        {doc.entry.title} — {boards.length} boards, {tl.dur.toFixed(1)}s ·
        scroll to pan, ⌘scroll to zoom, click a board to edit
      </div>
    </div>
  )
}
