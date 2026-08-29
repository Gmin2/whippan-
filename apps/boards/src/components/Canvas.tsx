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
import TextEditor from './TextEditor'
import StaggerStrip from './StaggerStrip'
import { lanesOf } from '../motion'

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
  /** additive means shift or cmd was held: add to or drop from the selection */
  onSelect(box: NodeBox | null, row: number, additive?: boolean): void
  /** everything picked alongside the primary, outlined but not handled */
  others: Sel[]
  /** a marquee inside a board replaces the selection with what it enclosed */
  onSelectMany(picked: Sel[], row: number): void
  onZoom(z: number): void
  /** resting geometry of the selected node, what a drag actually edits */
  geo: { x: number; y: number; w: number; h: number; fontSize?: number } | null
  /** follow is the distance the primary actually moved, for the rest to match */
  onDrag(patch: NodePatch, follow?: { dx: number; dy: number }): void
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
  /** double-clicking a text node edits it here; this streams every keystroke */
  onEditText(text: string): void
  /** one snapshot at the start of an edit, so undo steps over the whole word */
  onEditStart(): void
  /** a cancelled edit drops that snapshot again, leaving no empty undo step */
  onEditEnd(commit: boolean): void
  /** picking a lane on a stagger strip selects the node it belongs to */
  onSelectTarget(scene: string, id: string): void
  /** restagger from a strip: move a node's whole track to a new scene-local at */
  onShiftTrack(target: string, at: number, done: boolean): void
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
  ck, doc, rev, ground, title, boards, selected, selRow, onSelect, others,
  onSelectMany, onZoom,
  geo, onDrag, onDragEnd, onMeasure, onSelectScene, activeScene,
  tool, onCreate, onAddScene, onCreatePath, onToolDone, mode, playhead,
  selectedSeam, onSelectSeam, onEditText, onEditStart, onEditEnd,
  onSelectTarget, onShiftTrack,
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
    kind: 'pan' | 'move' | 'resize' | 'draw' | 'marquee'
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
    /** where the primary node was left on the previous move, for the followers */
    lastX?: number
    lastY?: number
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

  /** the text node being edited in place, if any */
  const [editing, setEditing] = useState<{ id: string; scene: string; row: number } | null>(null)
  // the field draws the glyphs while it is open, so the engine must not
  const hidden = editing
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
        paintFrameSafe(ck, skc, s.paint, hidden ? f.cmds.filter(c => !(c.id === hidden.id && c.scene === hidden.scene)) : f.cmds, doc.images)
        skc.restore()
      })
    })
    skc.restore()
    s.surface.flush()
  }, [ck, columns, cam, size, ground, doc.images, dw, dh, worldX, worldY, hidden])

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

  const editNode = useMemo(() => {
    if (!editing) return null
    const sc = doc.stage.scenes.find(s => s.id === editing.scene)
    return sc?.nodes.find(n => n.id === editing.id) ?? null
  }, [editing, doc.stage.scenes])

  // an open field leaves the wall alone if its node vanishes under it
  useEffect(() => { if (editing && !editNode) setEditing(null) }, [editing, editNode])

  /** lanes for every column, rebuilt only when the document actually changes */
  const strips = useMemo(
    () => (mode === 'motion'
      ? boards.map((b, i) => ({ b, i, lanes: lanesOf(doc, b.id) }))
      : []),
    [mode, boards, doc])

  /** the smallest type worth putting a caret in */
  const LEGIBLE = 13

  /** true when the node was a text node and the field opened */
  const startEdit = useCallback((box: NodeBox, row: number) => {
    const sc = doc.stage.scenes.find(s => s.id === box.scene)
    const node = sc?.nodes.find(n => n.id === box.id)
    if (node?.type !== 'text') return false
    onSelect(box, row)
    onEditStart()
    setEditing({ id: box.id, scene: box.scene, row })

    // at wall zoom a headline is two pixels tall, so editing it would mean
    // typing into nothing. zoom until it is legible and centre it
    const type = node.font?.size ?? 48
    const col = boards.findIndex(b => b.id === box.scene)
    setCam(prev => {
      if (type * prev.zoom >= LEGIBLE || col < 0) return prev
      const zoom = Math.min(1.5, LEGIBLE / type)
      const wx = worldX(col) + box.x + box.w / 2
      const wy = worldY(row) + box.y + box.h / 2
      return { zoom, pan: { x: size.w / 2 - wx * zoom, y: size.h / 2 - wy * zoom } }
    })
    return true
  }, [onSelect, onEditStart, doc.stage.scenes, boards, worldX, worldY, size.w, size.h])

  /** a recognised double click, waiting for the press to finish */
  const pendingEdit = useRef<{ box: NodeBox; row: number } | null>(null)

  /** the previous click, for recognising a double click on the same node */
  const lastClick = useRef<
    { id: string; scene: string; t: number; x: number; y: number } | null
  >(null)

  const local = (clientX: number, clientY: number) => {
    const r = wrap.current!.getBoundingClientRect()
    return { x: clientX - r.left, y: clientY - r.top }
  }

  const onDown = (e: React.PointerEvent) => {
    const pt = local(e.clientX, e.clientY)

    // pointer capture is taken on every down, and Chrome will not raise a
    // native dblclick through it, so the second click is recognised here
    if (tool === 'select') {
      const hit = pick(e.clientX, e.clientY)
      const last = lastClick.current
      const again = hit && last && last.id === hit.box.id && last.scene === hit.box.scene
        && e.timeStamp - last.t < 450
        && Math.hypot(e.clientX - last.x, e.clientY - last.y) < 6
      lastClick.current = hit
        ? { id: hit.box.id, scene: hit.box.scene, t: e.timeStamp, x: e.clientX, y: e.clientY }
        : null
      if (again) {
        
        lastClick.current = null
        if (startEdit(hit!.box, hit!.row)) { drag.current = null; return }
      }
    }

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
    // a resize acts on one node, so a multi-selection offers no handles
    const handle = rect && !others.length ? handleAt(rect, pt.x, pt.y) : null

    if (handle && geo) {
      drag.current = {
        kind: 'resize', handle, x: e.clientX, y: e.clientY, moved: false,
        geo: { ...geo }, box: rect!.box,
      }
      return
    }
    const hit = pick(e.clientX, e.clientY)
    const held = hit && (selected?.id === hit.box.id && selected.scene === hit.box.scene
      || others.some(o => o.id === hit.box.id && o.scene === hit.box.scene))
    if (hit && geo && held) {
      drag.current = {
        kind: 'move', x: e.clientX, y: e.clientY, moved: false,
        geo: { ...geo }, box: hit.box, board: locate(e.clientX, e.clientY)?.board ?? 0,
        row: hit.row,
      }
      return
    }
    // a press on a board's empty area sweeps a marquee; the wall behind the
    // boards is the thing you pan by, the way the hand tool always does
    const at = locate(e.clientX, e.clientY)
    if (!hit && at?.inside && tool === 'select') {
      const pt2 = local(e.clientX, e.clientY)
      drag.current = {
        kind: 'marquee', x: e.clientX, y: e.clientY, moved: false,
        board: at.board, row: at.row, origin: { x: at.x, y: at.y },
        screen: { x: pt2.x, y: pt2.y },
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
      setGrab(rect && !others.length ? handleAt(rect, pt.x, pt.y) : null)
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

    if (d.kind === 'draw' || d.kind === 'marquee') {
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
      const nx = Math.round(s.x)
      const ny = Math.round(s.y)
      // the rest of the selection follows the snapped distance, not the raw one
      const step = { dx: nx - (d.lastX ?? d.geo!.x), dy: ny - (d.lastY ?? d.geo!.y) }
      d.lastX = nx
      d.lastY = ny
      onDrag({ x: nx, y: ny }, step)
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
    const pending = pendingEdit.current
    pendingEdit.current = null
    if (pending) {
      // focus settles after the press, so mount the field a frame later
      requestAnimationFrame(() => startEdit(pending.box, pending.row))
      return
    }
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
    if (d.kind === 'marquee') {
      if (!d.moved) { onSelectScene(boards[d.board!].id); return }
      const at = locate(e.clientX, e.clientY)
      const o = d.origin!
      const end = at ? { x: at.x, y: at.y } : o
      const x0 = Math.min(o.x, end.x)
      const y0 = Math.min(o.y, end.y)
      const x1 = Math.max(o.x, end.x)
      const y1 = Math.max(o.y, end.y)
      const frame = columns[d.board!][d.row!] ?? columns[d.board!][0]
      // enclosed, not touched: a sweep that clips a headline should not take it
      const inside = frame.boxes.filter(
        b => b.x >= x0 && b.y >= y0 && b.x + b.w <= x1 && b.y + b.h <= y1)
      onSelectMany(inside.map(b => ({ scene: b.scene, id: b.id })), d.row!)
      return
    }
    if (d.kind !== 'pan' && d.moved) { onDragEnd(); return }
    if (d.moved) return
    const hit = pick(e.clientX, e.clientY)
    if (hit) { onSelect(hit.box, hit.row, e.shiftKey || e.metaKey || e.ctrlKey); return }
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
        // capture keeps a drag alive past the window edge; a pointer that has
        // already been released has nothing to capture, which is not an error
        try {
          ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
        } catch { /* the gesture still works without it */ }
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
      {editing && editNode && (() => {
        const r = selRect()
        return r ? (
          <TextEditor
            key={`${editing.scene}/${editing.id}`}
            rect={r}
            node={editNode}
            zoom={cam.zoom}
            onChange={onEditText}
            onDone={commit => { setEditing(null); onEditEnd(commit) }}
          />
        ) : null
      })()}
      {/* one strip under each column, so the stagger reads per beat rather
          than as one long film-length timeline */}
      {mode === 'motion' && strips.map(({ b, i, lanes }) => {
        const w = dw * cam.zoom
        const x = worldX(i) * cam.zoom + cam.pan.x
        const y = (worldY(0) + dh) * cam.zoom + cam.pan.y + 12
        if (x + w < 0 || x > size.w || y > size.h) return null
        const local = playhead - b.start
        return (
          <div key={b.id} className="absolute" style={{ left: x, top: y, width: w }}>
            <StaggerStrip
              lanes={lanes}
              dur={b.dur}
              playhead={local >= 0 && local <= b.dur ? local : null}
              width={w}
              fps={doc.stage.fps}
              selected={selected?.scene === b.id ? selected.id : null}
              onSelect={id => onSelectTarget(b.id, id)}
              onShift={onShiftTrack}
            />
          </div>
        )
      })}

      <Overlay
        others={others}
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
