import { useEffect, useRef } from 'react'
import { docDur, drawFrame } from '../engine'
import type { Doc } from '../engine/types'

interface Props {
  ck: CanvasKit
  doc: Doc
  /** drive the film from an outside clock; omit and it free-runs its own */
  t?: number
  className?: string
  style?: React.CSSProperties
}

export default function Film({ ck, doc, t, className, style }: Props) {
  const ref = useRef<HTMLCanvasElement>(null)
  const surf = useRef<{ surface: SkSurface; skc: unknown; paint: SkPaint } | null>(null)
  const [w, h] = doc.stage.size
  const dur = docDur(doc.stage)
  const controlled = typeof t === 'number'

  useEffect(() => {
    if (!ref.current) return
    const surface = ck.MakeCanvasSurface(ref.current)
    const paint = new ck.Paint()
    paint.setAntiAlias(true)
    surf.current = { surface, skc: surface.getCanvas(), paint }
    return () => {
      paint.delete()
      surface.delete()
      surf.current = null
    }
  }, [ck, doc])

  // controlled: repaint whenever the clock prop moves
  useEffect(() => {
    const s = surf.current
    if (!s || !controlled) return
    drawFrame(ck, s.skc, s.paint, doc, t)
    s.surface.flush()
  })

  // uncontrolled: free-running loop off its own clock
  useEffect(() => {
    if (controlled) return
    let raf = 0
    const t0 = performance.now()
    const draw = (now: number) => {
      const s = surf.current
      if (s) {
        drawFrame(ck, s.skc, s.paint, doc, ((now - t0) / 1000) % dur)
        s.surface.flush()
      }
      raf = requestAnimationFrame(draw)
    }
    raf = requestAnimationFrame(draw)
    return () => cancelAnimationFrame(raf)
  }, [ck, doc, controlled, dur])

  return (
    <canvas ref={ref} width={w} height={h} className={className} style={style}
            data-film />
  )
}
