export interface Key { t: number; v: number; ease?: unknown }

export const NAMED = ['linear', 'outCubic', 'inCubic', 'inOutCubic', 'spring'] as const

export const SPRING_DEFAULT: [number, number] = [6, 1]

/** the bezier the reference films reach for most often */
export const BEZIER_DEFAULT: [number, number, number, number] = [0.22, 1, 0.36, 1]

function cubicBezier(x1: number, y1: number, x2: number, y2: number) {
  const cx = 3 * x1
  const bx = 3 * (x2 - x1) - cx
  const ax = 1 - cx - bx
  const cy = 3 * y1
  const by = 3 * (y2 - y1) - cy
  const ay = 1 - cy - by
  const sx = (t: number) => ((ax * t + bx) * t + cx) * t
  const dx = (t: number) => (3 * ax * t + 2 * bx) * t + cx
  const sy = (t: number) => ((ay * t + by) * t + cy) * t

  // newton with a bisection fallback, the usual way to invert x(t)
  return (x: number) => {
    let t = x
    for (let i = 0; i < 8; i++) {
      const err = sx(t) - x
      if (Math.abs(err) < 1e-5) return sy(t)
      const d = dx(t)
      if (Math.abs(d) < 1e-6) break
      t -= err / d
    }
    let lo = 0
    let hi = 1
    t = x
    for (let i = 0; i < 20; i++) {
      const err = sx(t) - x
      if (Math.abs(err) < 1e-5) break
      if (err > 0) hi = t
      else lo = t
      t = (lo + hi) / 2
    }
    return sy(t)
  }
}

const spring = (damping: number, cycles: number) => (t: number) =>
  1 - Math.exp(-damping * t) * Math.cos(cycles * 2 * Math.PI * t)

export function springArgs(ease: unknown): [number, number] {
  if (ease && typeof ease === 'object' && !Array.isArray(ease)) {
    const s = (ease as { spring?: unknown }).spring
    if (Array.isArray(s)) return [Number(s[0]) || SPRING_DEFAULT[0], Number(s[1]) || SPRING_DEFAULT[1]]
  }
  return SPRING_DEFAULT
}

export function bezierArgs(ease: unknown): [number, number, number, number] {
  if (Array.isArray(ease) && ease.length === 4) {
    return [Number(ease[0]), Number(ease[1]), Number(ease[2]), Number(ease[3])]
  }
  return BEZIER_DEFAULT
}

/** which entry in the picker an ease value corresponds to */
export function easeKind(ease: unknown): string {
  if (ease == null) return 'linear'
  if (typeof ease === 'string') return (NAMED as readonly string[]).includes(ease) ? ease : 'linear'
  if (Array.isArray(ease)) return 'bezier'
  if (typeof ease === 'object' && 'spring' in (ease as object)) return 'spring'
  return 'linear'
}

export function easeLabel(ease: unknown): string {
  const kind = easeKind(ease)
  if (kind === 'spring') {
    const [d, c] = springArgs(ease)
    return `spring ${d}/${c}`
  }
  if (kind === 'bezier') return bezierArgs(ease).map(n => n.toFixed(2)).join(' ')
  return kind
}

/** a 0..1 -> 0..1 curve, which may overshoot past 1 */
export function easeFn(ease: unknown): (t: number) => number {
  const kind = easeKind(ease)
  if (kind === 'outCubic') return t => 1 - Math.pow(1 - t, 3)
  if (kind === 'inCubic') return t => t * t * t
  if (kind === 'inOutCubic') return t => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2)
  if (kind === 'spring') {
    const [d, c] = springArgs(ease)
    return spring(d, c)
  }
  if (kind === 'bezier') {
    const [a, b, c, d] = bezierArgs(ease)
    return cubicBezier(a, b, c, d)
  }
  return t => t
}

export const sortKeys = (keys: Key[]) => [...keys].sort((a, b) => a.t - b.t)

/** the value a property holds at a track-relative time */
export function valueAt(keys: Key[], t: number): number {
  if (!keys.length) return 0
  const s = sortKeys(keys)
  if (t <= s[0].t) return s[0].v
  const last = s[s.length - 1]
  if (t >= last.t) return last.v
  for (let i = 1; i < s.length; i++) {
    if (t <= s[i].t) {
      const a = s[i - 1]
      const b = s[i]
      const span = b.t - a.t || 1e-6
      return a.v + (b.v - a.v) * easeFn(b.ease)((t - a.t) / span)
    }
  }
  return last.v
}
