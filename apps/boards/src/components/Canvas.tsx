import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { paintFrame } from '@whippan/engine-web/painter'
import { render } from '../engine'
import type { Doc } from '../engine/types'
import type { Artboard, Sel } from '../doc'
import { hitTest, measure } from '../measure'
import type { Cmd, NodeBox } from '../measure'
import Overlay from './Overlay'

interface Props {
  ck: CanvasKit
  doc: Doc
  rev: number
  ground: string
  title: string[]
  boards: Artboard[]
  selected: Sel | null
  onSelect(box: NodeBox | null): void
  onZoom(z: number): void
}

/** gap between artboards, in document pixels — the wall lives in doc space */
const GAP = 320
/**
 * where in a scene we take the still. 70% is past the entrance and before the
 * exit, so each board reads as the settled frame the scene is really about,
 * which is how AUTHORING says to compose a stage.
 */
const SETTLED = 0.7

export interface Camera {
  pan: { x: number; y: number }
  zoom: number
}

/** the engine clears the whole surface; on a shared wall that has to become a
 *  filled rect so a board only paints its own ground */
function withGround(cmds: Cmd[], w: number, h: number): Cmd[] {
  return cmds.map(c =>
    c.op === 'clear'
      ? { ...c, op: 'rect', x: w / 2, y: h / 2, w, h, radius: 0, opacity: 1, scale: 1 }
      : c)
}

export default function Canvas({
  ck, doc, rev, ground, title, boards, selected, onSelect, onZoom,
}: Props) {
  const wrap = useRef<HTMLDivElement>(null)
  const canvas = useRef<HTMLCanvasElement>(null)
  const surf = useRef<{ surface: SkSurface; skc: unknown; paint: SkPaint } | null>(null)
  const [size, setSize] = useState({ w: 0, h: 0 })
  const [cam, setCam] = useState<Camera>({ pan: { x: 120, y: 140 }, zoom: 0.12 })
  const [hover, setHover] = useState<NodeBox | null>(null)
  const drag = useRef<{ x: number; y: number; moved: boolean } | null>(null)

  const [dw, dh] = doc.stage.size

  // world position of each board: one row, laid out left to right
  const worldX = useCallback((i: number) => i * (dw + GAP), [dw])

  // the frame each board shows, and the node boxes inside it. recomputed only
  // when the document actually changes, never on pan or zoom.
  const frames = useMemo(() => {
    const stage = JSON.stringify(doc.stage)
    const anim = JSON.stringify(doc.anim)
    return boards.map(b => {
      const cmds: Cmd[] = JSON.parse(render(stage, anim, b.start + b.dur * SETTLED))
      return { cmds: withGround(cmds, dw, dh), boxes: measure(cmds) }
    })
  }, [doc, boards, rev, dw, dh])

  useEffect(() => { onZoom(cam.zoom) }, [cam.zoom, onZoom])

  // keep the drawing buffer matched to the element and the display density
  useEffect(() => {
    const el = wrap.current
    if (!el) return
    const ro = new ResizeObserver(() => {
      const r = el.getBoundingClientRect()
      setSize({ w: Math.round(r.width), h: Math.round(r.height) })
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  useEffect(() => {
    const el = canvas.current
    if (!el || !size.w || !size.h) return
    const dpr = Math.min(2, window.devicePixelRatio || 1)
    el.width = Math.round(size.w * dpr)
    el.height = Math.round(size.h * dpr)
    const surface = ck.MakeCanvasSurface(el)
    const paint = new ck.Paint()
    paint.setAntiAlias(true)
    surf.current = { surface, skc: surface.getCanvas(), paint }
    return () => {
      paint.delete()
      surface.delete()
      surf.current = null
    }
  }, [ck, size.w, size.h])

  // one surface, every board drawn through the camera
  useEffect(() => {
    const s = surf.current
    if (!s) return
    const dpr = Math.min(2, window.devicePixelRatio || 1)
    const skc = s.skc as {
      save(): void; restore(): void; clear(c: unknown): void
      translate(x: number, y: number): void; scale(x: number, y: number): void
      clipRect(r: unknown, op: unknown, aa: boolean): void
    }
    skc.save()
    skc.clear(ck.parseColorString(ground))
    skc.scale(dpr, dpr)
    const { pan, zoom } = cam
    frames.forEach((f, i) => {
      const sx = worldX(i) * zoom + pan.x
      const sy = 0 * zoom + pan.y
      // skip boards entirely off screen
      if (sx > size.w || sx + dw * zoom < 0) return
      skc.save()
      skc.translate(sx, sy)
      skc.scale(zoom, zoom)
      // an artboard holds its own content: a scene with a camera zoom
      // transforms about the canvas centre and would otherwise spill across
      // its neighbours
      skc.clipRect(ck.LTRBRect(0, 0, dw, dh), ck.ClipOp.Intersect, true)
      paintFrameSafe(ck, skc, s.paint, f.cmds, doc.images)
      skc.restore()
    })
    skc.restore()
    s.surface.flush()
  }, [ck, frames, cam, size, ground, doc.images, dw, worldX])

  // wheel pans, cmd/ctrl wheel zooms at the pointer
  useEffect(() => {
    const el = wrap.current
    if (!el) return
    const onWheel = (e: WheelEvent) => {
      e.preventDefault()
      if (e.metaKey || e.ctrlKey) {
        const r = el.getBoundingClientRect()
        const mx = e.clientX - r.left
        const my = e.clientY - r.top
        setCam(c => {
          const zoom = Math.min(4, Math.max(0.02, c.zoom * Math.exp(-e.deltaY * 0.0015)))
          const k = zoom / c.zoom
          return {
            zoom,
            pan: { x: mx - (mx - c.pan.x) * k, y: my - (my - c.pan.y) * k },
          }
        })
      } else {
        setCam(c => ({ ...c, pan: { x: c.pan.x - e.deltaX, y: c.pan.y - e.deltaY } }))
      }
    }
    el.addEventListener('wheel', onWheel, { passive: false })
    return () => el.removeEventListener('wheel', onWheel)
  }, [])

  /** screen point -> which board, and where inside it in document space */
  const locate = useCallback((clientX: number, clientY: number) => {
    const el = wrap.current
    if (!el) return null
    const r = el.getBoundingClientRect()
    const wx = (clientX - r.left - cam.pan.x) / cam.zoom
    const wy = (clientY - r.top - cam.pan.y) / cam.zoom
    const i = Math.floor(wx / (dw + GAP))
    if (i < 0 || i >= boards.length) return null
    const x = wx - worldX(i)
    const y = wy
    if (x < 0 || x > dw || y < 0 || y > dh) return { board: i, x, y, inside: false }
    return { board: i, x, y, inside: true }
  }, [cam, dw, dh, boards.length, worldX])

  const pick = useCallback((clientX: number, clientY: number): NodeBox | null => {
    const at = locate(clientX, clientY)
    if (!at || !at.inside) return null
    return hitTest(frames[at.board].boxes, at.x, at.y)
  }, [locate, frames])

  // dev hook so automation can ask what the canvas thinks is under a point
  useEffect(() => {
    if (!import.meta.env.DEV) return
    ;(window as unknown as Record<string, unknown>).boards = { cam, frames, locate, pick }
  }, [cam, frames, locate, pick])

  return (
    <div
      ref={wrap}
      onPointerDown={e => { drag.current = { x: e.clientX, y: e.clientY, moved: false } }}
      onPointerMove={e => {
        const d = drag.current
        if (d) {
          if (Math.abs(e.clientX - d.x) + Math.abs(e.clientY - d.y) > 2) d.moved = true
          setCam(c => ({ ...c, pan: { x: c.pan.x + e.clientX - d.x, y: c.pan.y + e.clientY - d.y } }))
          drag.current = { x: e.clientX, y: e.clientY, moved: d.moved }
          return
        }
        setHover(pick(e.clientX, e.clientY))
      }}
      onPointerUp={e => {
        const d = drag.current
        drag.current = null
        if (d?.moved) return
        onSelect(pick(e.clientX, e.clientY))
      }}
      onPointerLeave={() => { drag.current = null; setHover(null) }}
      className="relative h-full flex-1 overflow-hidden"
      style={{ background: ground, cursor: hover ? 'default' : 'grab' }}
    >
      <canvas ref={canvas} className="absolute inset-0 h-full w-full" />
      <Overlay
        cam={cam}
        boards={boards}
        frames={frames}
        worldX={worldX}
        docSize={[dw, dh]}
        title={title}
        selected={selected}
        hover={hover}
      />
    </div>
  )
}

// paintFrame throws if a command references an image that has not loaded; one
// bad node should not blank the whole wall
function paintFrameSafe(
  ck: CanvasKit, skc: unknown, paint: SkPaint, cmds: Cmd[], images: Map<string, unknown>,
) {
  try {
    paintFrame(ck, skc, paint, cmds, images)
  } catch {
    /* a single board failing to paint is not worth losing the others */
  }
}
