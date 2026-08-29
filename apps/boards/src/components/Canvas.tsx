import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { paintFrame } from '@whippan/engine-web/painter'
import { render } from '../engine'
import type { Doc } from '../engine/types'
import type { Artboard, NodePatch, Sel } from '../doc'
import type { Tool } from './ToolRail'
import { hitTest, measure } from '../measure'
import type { Cmd, NodeBox } from '../measure'
import { CURSORS, handleAt, resize, scaleType } from '../handles'
import { snap } from '../snap'
import type { Guide } from '../snap'
import { GAP_X, columnX, rowY, sampleTimes, wallSize } from '../layout'
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
  /** which sampled frame of the scene the selection was made in */
  selRow: number
  onSelect(box: NodeBox | null, row: number): void
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
  /** the active tool decides whether a canvas drag selects or draws */
  tool: Tool
  onCreate(sceneId: string, kind: 'rect' | 'text',
           box: { x: number; y: number; w: number; h: number }): void
  onAddScene(afterId?: string): void
  onCreatePath(sceneId: string, pts: { x: number; y: number }[], closed: boolean): void
  onToolDone(): void
  /** design samples each scene through time; motion follows one playhead */
  mode: 'design' | 'motion'
  playhead: number
  selectedSeam: string | null
  onSelectSeam(sceneId: string | null): void
}


interface Frame {
  /** absolute film time this frame was rendered at */
  t: number
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
  ck, doc, rev, ground, title, boards, selected, selRow, onSelect, onZoom,
  geo, onDrag, onDragEnd, onMeasure, onSelectScene, activeScene,
  tool, onCreate, onAddScene, onCreatePath, onToolDone, mode, playhead,
  selectedSeam, onSelectSeam,
}: Props) {
  const wrap = useRef<HTMLDivElement>(null)
  const canvas = useRef<HTMLCanvasElement>(null)
  const surf = useRef<{ surface: SkSurface; skc: unknown; paint: SkPaint } | null>(null)
  const [size, setSize] = useState({ w: 0, h: 0 })
  const [cam, setCam] = useState<Camera>({ pan: { x: 120, y: 140 }, zoom: 0.12 })
  const [hover, setHover] = useState<NodeBox | null>(null)
  const [grab, setGrab] = useState<Handle | null>(null)
  const [guides, setGuides] = useState<Guide[]>([])
  /** the rubber band shown while a shape is being drawn, in screen pixels */
  const [band, setBand] = useState<{ x: number; y: number; w: number; h: number } | null>(null)
  const [dragging, setDragging] = useState(false)
  /** the path being drawn: points in document space, plus the live cursor */
  const [pen, setPen] = useState<{
    board: number
    pts: { x: number; y: number }[]
    cursor: { x: number; y: number } | null
  } | null>(null)
  const drag = useRef<{
    kind: 'pan' | 'move' | 'resize' | 'draw'
    handle?: Handle
    x: number
    y: number
    startX?: number
    startY?: number
    moved: boolean
    geo?: { x: number; y: number; w: number; h: number; fontSize?: number }
    box?: NodeBox
    board?: number
    row?: number
    origin?: { x: number; y: number }
    screen?: { x: number; y: number }
  } | null>(null)

  const [dw, dh] = doc.stage.size

  // one column per scene, frames stacked down it
  const worldX = useCallback((i: number) => columnX(i, dw), [dw])
  const worldY = useCallback((k: number) => rowY(k, dh), [dh])

  // The frame each board shows and the node boxes inside it. A patch replaces
  // only the edited scene object, so identity tells us which boards actually
  // need re-rendering — dragging one node does not re-render the wall. The
  // previous scene is part of the key because a morph reads across the cut.
  const cache = useRef(new Map<string, { self: unknown; prev: unknown; frame: Frame }>())
  const columns = useMemo(() => {
    const stage = JSON.stringify(doc.stage)
    const anim = JSON.stringify(doc.anim)
    return boards.map((b, i) => {
      const self = doc.stage.scenes[i]
      const prev = doc.stage.scenes[i - 1]
      // in motion mode a column is one frame: the scene under the playhead
      // plays, the rest hold at whichever edge is nearest, so the film reads
      // in context rather than as a wall of stills
      const times = mode === 'motion'
        ? [Math.min(Math.max(playhead, b.start), b.start + b.dur - 0.001)]
        : sampleTimes(b)
      return times.map((t, k) => {
        // the playhead moves continuously, so a motion frame is keyed by its
        // own time and never served from the design-mode cache
        const key = mode === 'motion' ? `${b.id}:m:${t.toFixed(3)}` : `${b.id}:${k}`
        const hit = cache.current.get(key)
        if (hit && hit.self === self && hit.prev === prev) return hit.frame
        const cmds: Cmd[] = JSON.parse(render(stage, anim, t))
        const frame: Frame = { t, cmds: withGround(cmds, dw, dh), boxes: measure(cmds) }
        if (cache.current.size > 400) cache.current.clear()
        cache.current.set(key, { self, prev, frame })
        return frame
      })
    })
  }, [doc, boards, rev, dw, dh, mode, playhead])

  useEffect(() => { onZoom(cam.zoom) }, [cam.zoom, onZoom])

  // fit the whole wall when the document changes: a 15-scene film and a
  // single-scene one at 1148x712 need very different cameras
  const fitted = useRef('')
  useEffect(() => {
    const key = `${doc.entry.slug}:${mode}:${size.w}x${size.h}`
    if (!size.w || !size.h || !boards.length || fitted.current === key) return
    fitted.current = key
    const pad = 70

    if (mode === 'motion') {
      // watching the film means one scene at a readable size, not fifteen
      // thumbnails; the camera follows the playhead from here
      const zoom = Math.min((size.w * 0.52) / dw, (size.h - pad * 2) / dh, 1)
      setCam({ zoom, pan: { x: pad, y: pad } })
      return
    }

    const wall = wallSize(boards, dw, dh, mode)
    const zoom = Math.min(
      (size.w - pad * 2) / wall.w,
      (size.h - pad * 2) / wall.h,
      1,
    )
    setCam({
      zoom,
      pan: { x: (size.w - wall.w * zoom) / 2, y: pad + 40 },
    })
  }, [doc.entry.slug, size, boards, dw, dh, mode])

  // in motion mode the wall scrolls under the playhead: the scene being played
  // stays centred, and its neighbours stay visible at the edges as context
  const activeBoard = useMemo(() => {
    if (mode !== 'motion') return -1
    return boards.findIndex(b => playhead >= b.start && playhead < b.start + b.dur)
  }, [mode, boards, playhead])

  useEffect(() => {
    if (mode !== 'motion' || activeBoard < 0 || !size.w) return
    setCam(c => {
      const wantX = size.w / 2 - (worldX(activeBoard) + dw / 2) * c.zoom
      // only chase when the scene actually changes, so a manual pan sticks
      return Math.abs(wantX - c.pan.x) < 1 ? c : { ...c, pan: { ...c.pan, x: wantX } }
    })
  }, [activeBoard, mode, size.w, dw, worldX])

  useEffect(() => {
    if (!selected) { onMeasure(null); return }
    for (const col of columns) {
      const f = col[selRow] ?? col[0]
      const b = f?.boxes.find(n => n.id === selected.id && n.scene === selected.scene)
      if (b) { onMeasure(b); return }
    }
    onMeasure(null)
  }, [columns, selected, selRow, onMeasure])

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
    columns.forEach((col, i) => {
      const cx = worldX(i) * zoom + pan.x
      if (cx > size.w || cx + dw * zoom < 0) return
      col.forEach((f, k) => {
        const cy = worldY(k) * zoom + pan.y
        if (cy > size.h || cy + dh * zoom < 0) return
        skc.save()
        skc.translate(cx, cy)
        skc.scale(zoom, zoom)
        // a scene with a camera zoom transforms about the canvas centre and
        // would otherwise spill across its neighbours
        skc.clipRect(ck.LTRBRect(0, 0, dw, dh), ck.ClipOp.Intersect, true)
        paintFrameSafe(ck, skc, s.paint, f.cmds, doc.images)
        skc.restore()
      })
    })
    skc.restore()
    s.surface.flush()
  }, [ck, columns, cam, size, ground, doc.images, dw, dh, worldX, worldY])

  useEffect(() => {
    if (tool !== 'pen') { setPen(null); return }
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== 'Enter' && e.key !== 'Escape') return
      e.preventDefault()
      setPen(prev => {
        if (prev && e.key === 'Enter' && prev.pts.length > 1) {
          onCreatePath(boards[prev.board].id, prev.pts, false)
        }
        return null
      })
      onToolDone()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [tool, pen, boards, onCreatePath, onToolDone])

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
    const i = Math.floor(wx / (dw + GAP_X))
    if (i < 0 || i >= columns.length) return null
    const x = wx - worldX(i)
    if (x < 0 || x > dw) return { board: i, row: 0, x, y: 0, inside: false }
    for (let k = 0; k < columns[i].length; k++) {
      const y = wy - worldY(k)
      if (y >= 0 && y <= dh) return { board: i, row: k, x, y, inside: true }
    }
    return { board: i, row: 0, x, y: wy, inside: false }
  }, [cam, dw, dh, columns, worldX, worldY])

  const pick = useCallback((clientX: number, clientY: number) => {
    const at = locate(clientX, clientY)
    if (!at || !at.inside) return null
    const box = hitTest(columns[at.board][at.row].boxes, at.x, at.y)
    return box ? { box, row: at.row } : null
  }, [locate, columns])

  // dev hook so automation can ask what the canvas thinks is under a point
  useEffect(() => {
    if (!import.meta.env.DEV) return
    ;(window as unknown as Record<string, unknown>).boards = { cam, columns, locate, pick, worldX, worldY }
  }, [cam, columns, locate, pick, worldX, worldY])

  /** the selected node's box on screen, which is where the handles live */
  const selRect = useCallback(() => {
    if (!selected) return null
    for (let i = 0; i < columns.length; i++) {
      const f = columns[i][selRow] ?? columns[i][0]
      const b = f?.boxes.find(n => n.id === selected.id && n.scene === selected.scene)
      if (!b) continue
      const k = columns[i][selRow] ? selRow : 0
      return {
        x: (worldX(i) + b.x) * cam.zoom + cam.pan.x,
        y: (worldY(k) + b.y) * cam.zoom + cam.pan.y,
        w: b.w * cam.zoom,
        h: b.h * cam.zoom,
        box: b,
      }
    }
    return null
  }, [selected, columns, selRow, cam, worldX, worldY])

  const local = (clientX: number, clientY: number) => {
    const r = wrap.current!.getBoundingClientRect()
    return { x: clientX - r.left, y: clientY - r.top }
  }

  const onDown = (e: React.PointerEvent) => {
    const pt = local(e.clientX, e.clientY)

    if (tool === 'hand') {
      drag.current = { kind: 'pan', x: e.clientX, y: e.clientY, moved: false }
      return
    }

    if (tool === 'frame') {
      // a frame is a scene here: the wall lays columns out itself, so the
      // gesture is "add a beat after this one" rather than "draw a box"
      const at = locate(e.clientX, e.clientY)
      onAddScene(at ? boards[at.board]?.id : undefined)
      onToolDone()
      drag.current = null
      return
    }

    if (tool === 'pen') {
      const at = locate(e.clientX, e.clientY)
      if (!at?.inside) return
      setPen(prev => {
        if (!prev || prev.board !== at.board) {
          return { board: at.board, pts: [{ x: at.x, y: at.y }], cursor: null }
        }
        // clicking the first anchor closes the path, the way paper does it
        const first = prev.pts[0]
        const near = Math.hypot(at.x - first.x, at.y - first.y) < 12 / cam.zoom
        if (near && prev.pts.length > 2) {
          onCreatePath(boards[prev.board].id, prev.pts, true)
          onToolDone()
          return null
        }
        return { ...prev, pts: [...prev.pts, { x: at.x, y: at.y }] }
      })
      drag.current = null
      return
    }

    if (tool === 'rect' || tool === 'text') {
      const at = locate(e.clientX, e.clientY)
      if (at?.inside) {
        drag.current = {
          kind: 'draw', x: e.clientX, y: e.clientY, moved: false,
          board: at.board, row: at.row,
          origin: { x: at.x, y: at.y }, screen: { x: pt.x, y: pt.y },
        }
        return
      }
    }

    const rect = selRect()
    const handle = rect ? handleAt(rect, pt.x, pt.y) : null

    if (handle && geo) {
      drag.current = {
        kind: 'resize', handle, x: e.clientX, y: e.clientY, moved: false,
        geo: { ...geo }, box: rect!.box,
      }
      return
    }
    const hit = pick(e.clientX, e.clientY)
    if (hit && geo && selected
        && hit.box.id === selected.id && hit.box.scene === selected.scene) {
      drag.current = {
        kind: 'move', x: e.clientX, y: e.clientY, moved: false,
        geo: { ...geo }, box: hit.box, board: locate(e.clientX, e.clientY)?.board ?? 0,
        row: hit.row,
      }
      return
    }
    drag.current = { kind: 'pan', x: e.clientX, y: e.clientY, moved: false }
  }

  const onMove = (e: React.PointerEvent) => {
    const d = drag.current
    if (pen && tool === 'pen') {
      const at = locate(e.clientX, e.clientY)
      if (at) setPen(p => (p ? { ...p, cursor: { x: at.x, y: at.y } } : p))
      return
    }
    if (!d) {
      const pt = local(e.clientX, e.clientY)
      const rect = selRect()
      setGrab(rect ? handleAt(rect, pt.x, pt.y) : null)
      setHover(pick(e.clientX, e.clientY)?.box ?? null)
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

    if (d.kind === 'draw') {
      const pt = local(e.clientX, e.clientY)
      setBand({
        x: Math.min(d.screen!.x, pt.x),
        y: Math.min(d.screen!.y, pt.y),
        w: Math.abs(pt.x - d.screen!.x),
        h: Math.abs(pt.y - d.screen!.y),
      })
      return
    }
    setDragging(true)
    if (d.kind === 'move') {
      const board = d.board ?? 0
      const box = d.box!
      // snap against every other node in the same scene, plus the artboard
      const siblings = (columns[board][d.row ?? 0] ?? columns[board][0]).boxes.filter(
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
    setBand(null)
    if (!d) return

    if (d.kind === 'draw') {
      const at = locate(e.clientX, e.clientY)
      const o = d.origin!
      const end = at ? { x: at.x, y: at.y } : o
      const w = Math.abs(end.x - o.x)
      const h = Math.abs(end.y - o.y)
      const kind = tool === 'text' ? 'text' : 'rect'
      // a click with no drag gets a sensible default size, the way every
      // design tool behaves
      const box = kind === 'text' || w < 4 || h < 4
        ? { x: o.x, y: o.y, w: 200, h: 100 }
        : { x: (o.x + end.x) / 2, y: (o.y + end.y) / 2, w, h }
      onCreate(boards[d.board!].id, kind, box)
      onToolDone()
      return
    }
    if (d.kind !== 'pan' && d.moved) { onDragEnd(); return }
    if (d.moved) return
    const hit = pick(e.clientX, e.clientY)
    if (hit) { onSelect(hit.box, hit.row); return }
    // no node under the cursor: inside a board selects the board, outside
    // clears the selection entirely
    const at = locate(e.clientX, e.clientY)
    if (at?.inside) { onSelectScene(boards[at.board].id); return }
    onSelect(null, 0)
  }

  const drawing = tool === 'rect' || tool === 'text' || tool === 'frame' || tool === 'pen'
  const cursor = tool === 'hand' ? 'grab'
    : drawing ? 'crosshair'
    : grab ? CURSORS[grab]
    : hover ? 'default' : 'grab'

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
      {band && (
        <div className="pointer-events-none absolute border border-[#5e92f4]
                        bg-[#5e92f4]/10"
             style={{ left: band.x, top: band.y, width: band.w, height: band.h }} />
      )}
      <Overlay
        cam={cam}
        boards={boards}
        columns={columns}
        worldX={worldX}
        worldY={worldY}
        selRow={selRow}
        docSize={[dw, dh]}
        title={title}
        selected={selected}
        hover={hover}
        activeScene={activeScene}
        onSelectScene={onSelectScene}
        guides={guides}
        dragging={dragging}
        pen={pen}
        mode={mode}
        selectedSeam={selectedSeam}
        onSelectSeam={onSelectSeam}
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
