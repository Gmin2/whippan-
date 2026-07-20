// the canvas. react owns the <canvas> element and nothing inside it — every
// frame is engine draw commands through the shared skia painter. clicking
// hit-tests the active scene's nodes in doc space and reports the selection.
import { useEffect, useRef } from 'react'
import { render, paintFrame, timing } from './engine.js'

export default function Stage({ ck, doc, t, selection, onSelect }) {
  const canvasRef = useRef(null)
  const surfRef = useRef(null)

  const [w, h] = doc.stage.size

  useEffect(() => {
    const surface = ck.MakeCanvasSurface(canvasRef.current)
    const paint = new ck.Paint()
    paint.setAntiAlias(true)
    surfRef.current = { surface, skc: surface.getCanvas(), paint }
    return () => { paint.delete(); surface.delete(); surfRef.current = null }
  }, [ck, doc, w, h])

  useEffect(() => {
    const s = surfRef.current
    if (!s) return
    const cmds = JSON.parse(render(
      JSON.stringify(doc.stage), JSON.stringify(doc.anim), t))
    paintFrame(ck, s.skc, s.paint, cmds, doc.images)
    if (selection) drawSelection(ck, s.skc, doc, selection, t)
    s.surface.flush()
  })

  function docPoint(ev) {
    const r = canvasRef.current.getBoundingClientRect()
    return [(ev.clientX - r.left) * (w / r.width),
            (ev.clientY - r.top) * (h / r.height)]
  }

  function hit(ev) {
    const [px, py] = docPoint(ev)
    const { scenes } = timing(doc.stage)
    const sc = scenes.find(s => t >= s.start && t < s.start + s.dur)
      ?? scenes[scenes.length - 1]
    // front-most first: later nodes draw on top
    for (const n of [...sc.nodes].reverse()) {
      const bw = n.w ?? (n.text ? n.text.length * (n.font?.size ?? 48) * 0.5 : 80)
      const bh = n.h ?? (n.font?.size ?? 48) * 1.3
      if (Math.abs(px - n.x) <= bw / 2 && Math.abs(py - n.y) <= bh / 2)
        return { sceneId: sc.id, nodeId: n.id }
    }
    return null
  }

  return (
    <canvas
      ref={canvasRef}
      width={w}
      height={h}
      style={{
        maxWidth: '100%', maxHeight: '100%',
        borderRadius: 8, background: '#000',
        boxShadow: '0 1px 2px rgba(0,0,0,.5), 0 18px 60px rgba(0,0,0,.45)',
      }}
      onMouseDown={ev => onSelect(hit(ev))}
    />
  )
}

function drawSelection(ck, skc, doc, sel, t) {
  const { scenes } = timing(doc.stage)
  const sc = scenes.find(s => s.id === sel.sceneId)
  if (!sc || !(t >= sc.start && t < sc.start + sc.dur)) return
  const n = sc.nodes.find(n => n.id === sel.nodeId)
  if (!n) return
  const bw = n.w ?? (n.text ? n.text.length * (n.font?.size ?? 48) * 0.5 : 80)
  const bh = n.h ?? (n.font?.size ?? 48) * 1.3
  const p = new ck.Paint()
  p.setAntiAlias(true)
  p.setStyle(ck.PaintStyle.Stroke)
  p.setStrokeWidth(2)
  p.setColor(ck.Color(96, 109, 224, 1))
  skc.drawRect(ck.LTRBRect(n.x - bw / 2, n.y - bh / 2,
                           n.x + bw / 2, n.y + bh / 2), p)
  // corner handles, the editor-selection look from the references
  const hs = 5
  p.setStyle(ck.PaintStyle.Fill)
  p.setColor(ck.Color(255, 255, 255, 1))
  const edge = new ck.Paint()
  edge.setStyle(ck.PaintStyle.Stroke)
  edge.setColor(ck.Color(96, 109, 224, 1))
  for (const [cx, cy] of [[n.x - bw / 2, n.y - bh / 2], [n.x + bw / 2, n.y - bh / 2],
                          [n.x - bw / 2, n.y + bh / 2], [n.x + bw / 2, n.y + bh / 2]]) {
    skc.drawRect(ck.LTRBRect(cx - hs, cy - hs, cx + hs, cy + hs), p)
    skc.drawRect(ck.LTRBRect(cx - hs, cy - hs, cx + hs, cy + hs), edge)
  }
  p.delete(); edge.delete()
}
