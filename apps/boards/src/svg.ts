/**
 * Turning a generated SVG into a whippan path node.
 *
 * A path node carries one outline and one fill, so a multi-coloured drawing
 * flattens: every subpath is merged and the first fill found wins. That is a
 * real loss, and the reason the vector action is for icons and marks rather
 * than illustrations. Arrow leans on primitives over stacked paths, so the
 * basic shapes are converted rather than skipped.
 */

const num = (el: Element, name: string, fallback = 0) => {
  const v = parseFloat(el.getAttribute(name) ?? '')
  return Number.isFinite(v) ? v : fallback
}

/** one ellipse as four arcs, which is exact and shorter than a bezier guess */
function ellipse(cx: number, cy: number, rx: number, ry: number): string {
  return `M${cx - rx},${cy}`
    + `a${rx},${ry} 0 1,0 ${rx * 2},0`
    + `a${rx},${ry} 0 1,0 ${-rx * 2},0Z`
}

function rounded(x: number, y: number, w: number, h: number, rx: number, ry: number): string {
  if (!rx && !ry) return `M${x},${y}h${w}v${h}h${-w}Z`
  const a = Math.min(rx || ry, w / 2)
  const b = Math.min(ry || rx, h / 2)
  return `M${x + a},${y}h${w - a * 2}a${a},${b} 0 0,1 ${a},${b}`
    + `v${h - b * 2}a${a},${b} 0 0,1 ${-a},${b}`
    + `h${-(w - a * 2)}a${a},${b} 0 0,1 ${-a},${-b}`
    + `v${-(h - b * 2)}a${a},${b} 0 0,1 ${a},${-b}Z`
}

function outlineOf(el: Element): string | null {
  switch (el.tagName.toLowerCase()) {
    case 'path': return el.getAttribute('d')
    case 'rect':
      return rounded(num(el, 'x'), num(el, 'y'), num(el, 'width'), num(el, 'height'),
                     num(el, 'rx'), num(el, 'ry'))
    case 'circle': {
      const r = num(el, 'r')
      return r ? ellipse(num(el, 'cx'), num(el, 'cy'), r, r) : null
    }
    case 'ellipse':
      return ellipse(num(el, 'cx'), num(el, 'cy'), num(el, 'rx'), num(el, 'ry'))
    case 'line':
      return `M${num(el, 'x1')},${num(el, 'y1')}L${num(el, 'x2')},${num(el, 'y2')}`
    case 'polygon': {
      const p = el.getAttribute('points')?.trim()
      return p ? `M${p}Z` : null
    }
    case 'polyline': {
      const p = el.getAttribute('points')?.trim()
      return p ? `M${p}` : null
    }
    default: return null
  }
}

export interface Vector {
  /** every outline merged into one path, still in the svg's own coordinates */
  d: string
  fill: string
  /** the viewBox, so the caller can scale the drawing to a sensible size */
  size: [number, number]
}

export function svgToPath(svg: string): Vector | null {
  const doc = new DOMParser().parseFromString(svg, 'image/svg+xml')
  if (doc.querySelector('parsererror')) return null
  const root = doc.querySelector('svg')
  if (!root) return null

  const parts: string[] = []
  let fill = ''
  for (const el of Array.from(root.querySelectorAll('*'))) {
    const d = outlineOf(el)
    if (!d) continue
    parts.push(d)
    const f = el.getAttribute('fill')
    if (!fill && f && f !== 'none') fill = f
  }
  if (!parts.length) return null

  const box = root.getAttribute('viewBox')?.trim().split(/[\s,]+/).map(Number)
  const size: [number, number] = box?.length === 4 && box.every(Number.isFinite)
    ? [box[2], box[3]]
    : [num(root, 'width', 24), num(root, 'height', 24)]

  return { d: parts.join(' '), fill: fill || '#000000', size }
}
