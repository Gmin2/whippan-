// Turning painted pixels back into objects.
//
// Every draw command now carries the node and scene it came from, so a node's
// box is the union of its commands' boxes. That is deliberately not the same
// as reading x/y/w/h out of the json: these are the numbers the painter
// actually used, so keyframes, reveals, morph clones, rotation and camera are
// already baked in. A selection box drawn from this cannot drift from what is
// on screen.

export interface Cmd {
  op: string
  id?: string
  scene?: string
  x: number
  y: number
  w?: number
  h?: number
  d?: string
  rot?: number
  scale: number
  opacity: number
  stroke?: number
}

export interface Box {
  x0: number
  y0: number
  x1: number
  y1: number
}

export interface NodeBox {
  scene: string
  id: string
  /** top-left and size in document space */
  x: number
  y: number
  w: number
  h: number
  /** paint order of the node's first command; higher draws later, so hits win */
  z: number
}

const EMPTY: Box = { x0: Infinity, y0: Infinity, x1: -Infinity, y1: -Infinity }

function grow(a: Box, b: Box): Box {
  return {
    x0: Math.min(a.x0, b.x0),
    y0: Math.min(a.y0, b.y0),
    x1: Math.max(a.x1, b.x1),
    y1: Math.max(a.y1, b.y1),
  }
}

const isReal = (b: Box) => b.x1 >= b.x0 && b.y1 >= b.y0

function cubic(p0: number, p1: number, p2: number, p3: number, u: number) {
  const v = 1 - u
  return v * v * v * p0 + 3 * v * v * u * p1 + 3 * v * u * u * p2 + u * u * u * p3
}

function quad(p0: number, p1: number, p2: number, u: number) {
  const v = 1 - u
  return v * v * p0 + 2 * v * u * p1 + u * u * p2
}

/**
 * Bounding box of an svg path in its own coordinates. Curves are sampled
 * rather than bounded by their control points, because control-point bounds
 * overshoot badly on the rounded shapes these documents are full of, and an
 * oversized selection box is immediately visible as wrong.
 */
export function pathBounds(d: string): Box {
  const nums = /[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?/g
  const cmds = d.match(/[MmLlHhVvCcSsQqTtAaZz][^MmLlHhVvCcSsQqTtAaZz]*/g)
  if (!cmds) return EMPTY
  let box = EMPTY
  let cx = 0, cy = 0, sx = 0, sy = 0
  const at = (x: number, y: number) => {
    box = grow(box, { x0: x, y0: y, x1: x, y1: y })
  }
  for (const seg of cmds) {
    const op = seg[0]
    const abs = op === op.toUpperCase()
    const a = (seg.slice(1).match(nums) ?? []).map(Number)
    const ox = abs ? 0 : cx
    const oy = abs ? 0 : cy
    switch (op.toUpperCase()) {
      case 'M':
        for (let i = 0; i + 1 < a.length; i += 2) {
          cx = (abs ? 0 : cx) + a[i]
          cy = (abs ? 0 : cy) + a[i + 1]
          if (i === 0) { sx = cx; sy = cy }
          at(cx, cy)
        }
        break
      case 'L':
        for (let i = 0; i + 1 < a.length; i += 2) {
          cx = (abs ? 0 : cx) + a[i]
          cy = (abs ? 0 : cy) + a[i + 1]
          at(cx, cy)
        }
        break
      case 'H':
        for (const v of a) { cx = (abs ? 0 : cx) + v; at(cx, cy) }
        break
      case 'V':
        for (const v of a) { cy = (abs ? 0 : cy) + v; at(cx, cy) }
        break
      case 'C':
        for (let i = 0; i + 5 < a.length; i += 6) {
          const [x1, y1, x2, y2, x3, y3] = [
            ox + a[i], oy + a[i + 1], ox + a[i + 2], oy + a[i + 3],
            ox + a[i + 4], oy + a[i + 5],
          ]
          for (let s = 0; s <= 8; s++) {
            const u = s / 8
            at(cubic(cx, x1, x2, x3, u), cubic(cy, y1, y2, y3, u))
          }
          cx = x3; cy = y3
        }
        break
      case 'Q':
        for (let i = 0; i + 3 < a.length; i += 4) {
          const [x1, y1, x2, y2] =
            [ox + a[i], oy + a[i + 1], ox + a[i + 2], oy + a[i + 3]]
          for (let s = 0; s <= 6; s++) {
            const u = s / 6
            at(quad(cx, x1, x2, u), quad(cy, y1, y2, u))
          }
          cx = x2; cy = y2
        }
        break
      case 'Z':
        cx = sx; cy = sy
        break
      default:
        // S/T/A are not emitted by the engine; fall back to the raw points so
        // an unexpected path still produces a usable box
        for (let i = 0; i + 1 < a.length; i += 2) at(ox + a[i], oy + a[i + 1])
    }
  }
  return box
}

const pathCache = new Map<string, Box>()

function cachedPathBounds(d: string): Box {
  let b = pathCache.get(d)
  if (!b) {
    b = pathBounds(d)
    if (pathCache.size > 4000) pathCache.clear()
    pathCache.set(d, b)
  }
  return b
}

/** the box one command covers, in document space */
export function cmdBounds(c: Cmd): Box {
  let local: Box
  if (c.op === 'rect' || c.op === 'image') {
    const w = c.w ?? 0
    const h = c.h ?? 0
    local = { x0: -w / 2, y0: -h / 2, x1: w / 2, y1: h / 2 }
  } else if (c.op === 'path' && c.d) {
    local = cachedPathBounds(c.d)
  } else {
    return EMPTY
  }
  if (!isReal(local)) return EMPTY

  // a stroked path spills half its width past the outline
  if (c.stroke) {
    const p = c.stroke / 2
    local = { x0: local.x0 - p, y0: local.y0 - p, x1: local.x1 + p, y1: local.y1 + p }
  }

  const s = c.scale ?? 1
  const rad = ((c.rot ?? 0) * Math.PI) / 180
  const cos = Math.cos(rad)
  const sin = Math.sin(rad)
  let out = EMPTY
  for (const [lx, ly] of [
    [local.x0, local.y0], [local.x1, local.y0],
    [local.x1, local.y1], [local.x0, local.y1],
  ]) {
    const px = lx * s
    const py = ly * s
    const x = c.x + px * cos - py * sin
    const y = c.y + px * sin + py * cos
    out = grow(out, { x0: x, y0: y, x1: x, y1: y })
  }
  return out
}

/**
 * Every node visible in this frame, with the box it actually occupies.
 * Fully transparent commands are ignored so a node that has faded out is not
 * selectable, which matches what the eye expects.
 */
export function measure(cmds: Cmd[]): NodeBox[] {
  const acc = new Map<string, { scene: string; box: Box; z: number }>()
  cmds.forEach((c, i) => {
    if (!c.id || (c.opacity ?? 1) <= 0.01) return
    const b = cmdBounds(c)
    if (!isReal(b)) return
    const key = `${c.scene}/${c.id}`
    const hit = acc.get(key)
    if (hit) hit.box = grow(hit.box, b)
    else acc.set(key, { scene: c.scene ?? '', box: b, z: i })
  })
  return [...acc.entries()].map(([key, v]) => ({
    scene: v.scene,
    id: key.slice(key.indexOf('/') + 1),
    x: v.box.x0,
    y: v.box.y0,
    w: v.box.x1 - v.box.x0,
    h: v.box.y1 - v.box.y0,
    z: v.z,
  }))
}

/** topmost node covering a point in document space */
export function hitTest(boxes: NodeBox[], x: number, y: number): NodeBox | null {
  let best: NodeBox | null = null
  for (const b of boxes) {
    if (x < b.x || y < b.y || x > b.x + b.w || y > b.y + b.h) continue
    if (!best || b.z > best.z) best = b
  }
  return best
}

/**
 * A group's box is the union of what it holds.
 *
 * Groups draw nothing, so unlike every other node there is no command to
 * measure. Everything downstream — the selection outline, the handles, the
 * inspector's on-screen size — asks for this instead.
 */
export function groupBox(
  boxes: NodeBox[], scene: string, memberIds: readonly string[],
): NodeBox | null {
  const set = new Set(memberIds)
  const held = boxes.filter(b => b.scene === scene && set.has(b.id))
  if (!held.length) return null
  const x0 = Math.min(...held.map(b => b.x))
  const y0 = Math.min(...held.map(b => b.y))
  const x1 = Math.max(...held.map(b => b.x + b.w))
  const y1 = Math.max(...held.map(b => b.y + b.h))
  return {
    scene,
    id: '',
    x: x0, y: y0, w: x1 - x0, h: y1 - y0,
    z: Math.max(...held.map(b => b.z)),
  }
}
