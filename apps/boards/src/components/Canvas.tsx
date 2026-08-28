import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { paintFrame } from '@whippan/engine-web/painter'
import { render } from '../engine'
import type { Doc } from '../engine/types'
import type { Artboard, NodePatch, Sel } from '../doc'
import { hitTest, measure } from '../measure'
import type { Cmd, NodeBox } from '../measure'
import { CURSORS, handleAt, resize, scaleType } from '../handles'
import { snap } from '../snap'
import type { Guide } from '../snap'
import type { Handle } from '../handles'
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
  /** resting geometry of the selected node, what a drag actually edits */
  geo: { x: number; y: number; w: number; h: number; fontSize?: number } | null
  onDrag(patch: NodePatch): void
  onDragEnd(): void
  /** the selected node's live box, so the inspector can report what is
   *  actually painted rather than what was painted when it was selected */
  onMeasure(box: NodeBox | null): void
  onSelectScene(scene: string): void
  activeScene: string | null
}

/** gap between artboards, in document pixels — the wall lives in doc space */
const GAP = 320
/**
 * where in a scene we take the still. 70% is past the entrance and before the
 * exit, so each board reads as the settled frame the scene is really about,
 * which is how AUTHORING says to compose a stage.
 */
const SETTLED = 0.7

interface Frame {
  cmds: Cmd[]
  boxes: NodeBox[]
}

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
  geo, onDrag, onDragEnd, onMeasure, onSelectScene, activeScene,
}: Props) {
  const wrap = useRef<HTMLDivElement>(null)
  const canvas = useRef<HTMLCanvasElement>(null)
  const surf = useRef<{ surface: SkSurface; skc: unknown; paint: SkPaint } | null>(null)
  const [size, setSize] = useState({ w: 0, h: 0 })
  const [cam, setCam] = useState<Camera>({ pan: { x: 120, y: 140 }, zoom: 0.12 })
  const [hover, setHover] = useState<NodeBox | null>(null)
  const [grab, setGrab] = useState<Handle | null>(null)
  const [guides, setGuides] = useState<Guide[]>([])
  const [dragging, setDragging] = useState(false)
  const drag = useRef<{
    kind: 'pan' | 'move' | 'resize'
    handle?: Handle
    x: number
    y: number
    startX?: number
    startY?: number
    moved: boolean
    geo?: { x: number; y: number; w: number; h: number; fontSize?: number }
    box?: NodeBox
    board?: number
  } | null>(null)

  const [dw, dh] = doc.stage.size

  // world position of each board: one row, laid out left to right
  const worldX = useCallback((i: number) => i * (dw + GAP), [dw])

  // The frame each board shows and the node boxes inside it. A patch replaces
  // only the edited scene object, so identity tells us which boards actually
  // need re-rendering — dragging one node does not re-render the wall. The
  // previous scene is part of the key because a morph reads across the cut.
  const cache = useRef(new Map<string, { self: unknown; prev: unknown; frame: Frame }>())
  const frames = useMemo(() => {
    const stage = JSON.stringify(doc.stage)
    const anim = JSON.stringify(doc.anim)
    return boards.map((b, i) => {
      const self = doc.stage.scenes[i]
      const prev = doc.stage.scenes[i - 1]
      const hit = cache.current.get(b.id)
      if (hit && hit.self === self && hit.prev === prev) return hit.frame
      const cmds: Cmd[] = JSON.parse(render(stage, anim, b.start + b.dur * SETTLED))
      const frame: Frame = { cmds: withGround(cmds, dw, dh), boxes: measure(cmds) }
      cache.current.set(b.id, { self, prev, frame })
      return frame
    })
  }, [doc, boards, rev, dw, dh])

  useEffect(() => { onZoom(cam.zoom) }, [cam.zoom, onZoom])

  // fit the whole wall when the document changes: a 15-scene film and a
  // single-scene one at 1148x712 need very different cameras
  const fitted = useRef('')
  useEffect(() => {
    const key = `${doc.entry.slug}:${size.w}x${size.h}`
    if (!size.w || !size.h || !boards.length || fitted.current === key) return
    fitted.current = key
    const contentW = boards.length * dw + (boards.length - 1) * GAP
    const pad = 80
    const zoom = Math.min(
      (size.w - pad * 2) / contentW,
      (size.h - pad * 2 - 120) / dh,
      1,
    )
    setCam({
      zoom,
      pan: {
        x: (size.w - contentW * zoom) / 2,
        y: (size.h - dh * zoom) / 2 + 20,
      },
    })
  }, [doc.entry.slug, size, boards.length, dw, dh])

  useEffect(() => {
    if (!selected) { onMeasure(null); return }
    for (const f of frames) {
      const b = f.boxes.find(n => n.id === selected.id && n.scene === selected.scene)
      if (b) { onMeasure(b); return }
    }
    onMeasure(null)
  }, [frames, selected, onMeasure])

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

  /** the selected node's box on screen, which is where the handles live */
  const selRect = useCallback(() => {
    if (!selected) return null
    for (let i = 0; i < frames.length; i++) {
      const b = frames[i].boxes.find(n => n.id === selected.id && n.scene === selected.scene)
      if (!b) continue
      return {
        x: (worldX(i) + b.x) * cam.zoom + cam.pan.x,
        y: b.y * cam.zoom + cam.pan.y,
        w: b.w * cam.zoom,
        h: b.h * cam.zoom,
        box: b,
      }
    }
    return null
  }, [selected, frames, cam, worldX])

  const local = (clientX: number, clientY: number) => {
    const r = wrap.current!.getBoundingClientRect()
    return { x: clientX - r.left, y: clientY - r.top }
  }

  const onDown = (e: React.PointerEvent) => {
    const pt = local(e.clientX, e.clientY)
    const rect = selRect()
    const handle = rect ? handleAt(rect, pt.x, pt.y) : null

    if (handle && geo) {
      drag.current = {
        kind: 'resize', handle, x: e.clientX, y: e.clientY, moved: false,
        geo: { ...geo }, box: rect!.box,
      }
      return
    }
    const node = pick(e.clientX, e.clientY)
    if (node && geo && selected
        && node.id === selected.id && node.scene === selected.scene) {
      const at = locate(e.clientX, e.clientY)
      drag.current = {
        kind: 'move', x: e.clientX, y: e.clientY, moved: false,
        geo: { ...geo }, box: node, board: at?.board ?? 0,
      }
      return
    }
    drag.current = { kind: 'pan', x: e.clientX, y: e.clientY, moved: false }
  }

  const onMove = (e: React.PointerEvent) => {
    const d = drag.current
    if (!d) {
      const pt = local(e.clientX, e.clientY)
      const rect = selRect()
      setGrab(rect ? handleAt(rect, pt.x, pt.y) : null)
      setHover(pick(e.clientX, e.clientY))
      return
    }
    const dxs = e.clientX - d.x
    const dys = e.clientY - d.y
    if (Math.abs(dxs) + Math.abs(dys) > 2) d.moved = true

    if (d.kind === 'pan') {
      setCam(c => ({ ...c, pan: { x: c.pan.x + dxs, y: c.pan.y + dys } }))
      d.x = e.clientX
      d.y = e.clientY
      return
    }
    // document-space delta from where the drag began
    const dx = (e.clientX - d.startX!) / cam.zoom
    const dy = (e.clientY - d.startY!) / cam.zoom

    setDragging(true)
    if (d.kind === 'move') {
      const board = d.board ?? 0
      const box = d.box!
      // snap against every other node in the same scene, plus the artboard
      const siblings = frames[board].boxes.filter(
        b => !(b.id === box.id && b.scene === box.scene))
      const s = snap(
        d.geo!.x + dx, d.geo!.y + dy, box.w, box.h,
        siblings, [dw, dh], board, cam.zoom,
      )
      setGuides(s.guides)
      onDrag({ x: Math.round(s.x), y: Math.round(s.y) })
      return
    }
    if (d.geo!.fontSize != null) {
      // text has no box of its own; corners scale the type
      onDrag({ fontSize: scaleType(d.geo!.fontSize, d.box!, dx, dy) })
      return
    }
    const g = resize(d.geo!, d.handle!, dx, dy, e.shiftKey, e.altKey)
    onDrag({
      x: Math.round(g.x), y: Math.round(g.y),
      w: Math.round(g.w), h: Math.round(g.h),
    })
  }

  const onUp = (e: React.PointerEvent) => {
    const d = drag.current
    drag.current = null
    setGuides([])
    setDragging(false)
    if (!d) return
    if (d.kind !== 'pan' && d.moved) { onDragEnd(); return }
    if (d.moved) return
    const node = pick(e.clientX, e.clientY)
    if (node) { onSelect(node); return }
    // no node under the cursor: inside a board selects the board, outside
    // clears the selection entirely
    const at = locate(e.clientX, e.clientY)
    if (at?.inside) { onSelectScene(boards[at.board].id); return }
    onSelect(null)
  }

  const cursor = grab ? CURSORS[grab] : hover ? 'default' : 'grab'

  return (
    <div
      ref={wrap}
      onPointerDown={e => {
        ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
        onDown(e)
        const d = drag.current
        if (d) { d.startX = e.clientX; d.startY = e.clientY }
      }}
      onPointerMove={onMove}
      onPointerUp={onUp}
      onPointerLeave={() => { setHover(null); setGrab(null) }}
      className="relative h-full flex-1 overflow-hidden"
      style={{ background: ground, cursor }}
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
        activeScene={activeScene}
        onSelectScene={onSelectScene}
        guides={guides}
        dragging={dragging}
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
