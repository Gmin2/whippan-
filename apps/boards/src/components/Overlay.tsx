import type { Artboard, Sel } from '../doc'
import type { NodeBox } from '../measure'
import { handlePoints } from '../handles'
import { GAP_Y, HEADER, HEADER_GAP } from '../layout'
import type { Camera } from './Canvas'
import type { Guide } from '../snap'

interface Frame {
  t: number
  boxes: NodeBox[]
}

interface Props {
  cam: Camera
  boards: Artboard[]
  columns: Frame[][]
  worldX(i: number): number
  worldY(k: number): number
  selRow: number
  docSize: [number, number]
  title: string[]
  selected: Sel | null
  hover: NodeBox | null
  activeScene: string | null
  onSelectScene(scene: string): void
  /** alignment guides produced by the live drag, in document space */
  guides: Guide[]
  /** chrome hides while dragging: only artwork and guides stay */
  dragging: boolean
}

/** sampled off paper's own overlay canvas */
const ACCENT = '#5e92f4'
/** snap guides are crimson there, not the selection blue */
const GUIDE = '#dc4f70'

/** naive word wrap for the script card */
function wrapText(text: string, cols: number): string[] {
  if (cols < 8) return []
  const out: string[] = []
  let line = ''
  for (const word of text.split(/\s+/)) {
    if ((line + ' ' + word).trim().length > cols) { out.push(line.trim()); line = word }
    else line += ' ' + word
  }
  if (line.trim()) out.push(line.trim())
  return out
}
/** 8.5 css px outer square, white fill, 1.5px accent border, square corners */
const HANDLE = 8.5

// Chrome drawn over the engine surface: board labels and captions, the hover
// outline and the selection box with its handles. Everything is positioned in
// screen space from the camera, so it tracks pan and zoom exactly without
// being scaled by them — a handle is always the same size under the cursor.
export default function Overlay({
  cam, boards, columns, worldX, worldY, selRow, docSize, title, selected, hover,
  activeScene, onSelectScene, guides, dragging,
}: Props) {
  const [dw, dh] = docSize
  const { pan, zoom } = cam
  const sx = (i: number, x: number) => (worldX(i) + x) * zoom + pan.x
  const sy = (y: number) => y * zoom + pan.y
  const ry = (k: number, y: number) => (worldY(k) + y) * zoom + pan.y

  const find = (s: { scene: string; id: string } | null) => {
    if (!s) return null
    for (let i = 0; i < columns.length; i++) {
      const k = columns[i][selRow] ? selRow : 0
      const b = columns[i][k]?.boxes.find(n => n.id === s.id && n.scene === s.scene)
      if (b) return { i, k, b }
    }
    return null
  }
  const sel = find(selected)
  const same = hover && selected &&
    hover.id === selected.id && hover.scene === selected.scene
  const hov = same ? null : find(hover)

  const rectOf = (i: number, k: number, b: NodeBox) => ({
    x: sx(i, b.x),
    y: ry(k, b.y),
    w: b.w * zoom,
    h: b.h * zoom,
  })

  return (
    <svg className="pointer-events-none absolute inset-0 h-full w-full"
         style={{ overflow: 'visible' }}>
      {/* the film name, living on the canvas rather than in any board */}
      <text x={sx(0, 0)} y={ry(0, 0) - HEADER_GAP * zoom - Math.max(HEADER * zoom, 82) - 34}
            fill="rgba(255,255,255,0.75)" fontSize={20}>
        {title[0]}
      </text>
      <text x={sx(0, 0)} y={ry(0, 0) - HEADER_GAP * zoom - Math.max(HEADER * zoom, 82) - 14}
            fill="rgba(255,255,255,0.55)" fontSize={13}>
        {title[1]}
      </text>

      {boards.map((b, i) => {
        const x = sx(i, 0)
        const w = dw * zoom
        if (x > 4000 || x + w < -400) return null
        const active = activeScene === b.id
        // the card grows with the wall but never shrinks below legible, and it
        // grows upward from the first frame so it can never eat into one
        const cardH = Math.max(HEADER * zoom, 82)
        const cardY = ry(0, 0) - HEADER_GAP * zoom - cardH

        // the card is laid out in world space so it scales with the wall, but
        // its text is measured in screen pixels: a line of copy has to stay
        // legible at any zoom, or vanish when there is genuinely no room
        const pad = Math.min(14, Math.max(6, w * 0.04))
        const fs = 12
        const lh = 16
        const roomForText = w > 104
        const cols = Math.floor((w - pad * 2) / (fs * 0.52))
        const maxLines = Math.floor((cardH - pad * 2 - 18) / lh)
        const lines = roomForText ? wrapText(b.note, cols).slice(0, Math.max(0, maxLines)) : []

        return (
          <g key={b.id}>
            <rect x={x} y={cardY} width={w} height={cardH} rx={Math.min(10, w * 0.03)}
                  fill="#16241d"
                  className="pointer-events-auto cursor-pointer"
                  onPointerDown={e => { e.stopPropagation(); onSelectScene(b.id) }} />
            {roomForText && (
              <text x={x + pad} y={cardY + pad + 10} fill="rgba(255,255,255,0.42)"
                    fontSize={10} fontFamily="monospace">
                {b.label} · {b.dur.toFixed(1)}s
              </text>
            )}
            {lines.map((line, li) => (
              <text key={li} x={x + pad} y={cardY + pad + 30 + li * lh}
                    fill="rgba(255,255,255,0.9)" fontSize={fs}>
                {line}
              </text>
            ))}

            {(columns[i] ?? []).map((f, k) => (
              <g key={k}>
                {active && !selected && (
                  <rect x={x} y={ry(k, 0)} width={w} height={dh * zoom}
                        fill="none" stroke={ACCENT} strokeWidth={1.5} />
                )}
                {/* the time sits in the gap above its own frame, and only
                    when the gap is actually tall enough to hold it */}
                {w > 70 && GAP_Y * zoom >= 13 && (
                  <text x={x} y={ry(k, 0) - 5} fill="rgba(0,0,0,0.38)"
                        fontSize={10} fontFamily="monospace">
                    {f.t.toFixed(2)}s
                  </text>
                )}
              </g>
            ))}
          </g>
        )
      })}

      {!dragging && hov && (() => {
        const r = rectOf(hov.i, hov.k, hov.b)
        return <rect x={r.x} y={r.y} width={r.w} height={r.h}
                     fill="none" stroke={ACCENT} strokeWidth={1} />
      })()}

      {sel && !dragging && (() => {
        const r = rectOf(sel.i, sel.k, sel.b)
        const label = `${Math.round(sel.b.w)} × ${Math.round(sel.b.h)}`
        const pillW = label.length * 6.6 + 16
        return (
          <g>
            <rect x={r.x} y={r.y} width={r.w} height={r.h}
                  fill="none" stroke={ACCENT} strokeWidth={1.5} />
            {handlePoints(r).map(([hx, hy], k) => (
              <rect key={k} x={hx - HANDLE / 2} y={hy - HANDLE / 2}
                    width={HANDLE} height={HANDLE}
                    fill="#ffffff" stroke={ACCENT} strokeWidth={1.5} />
            ))}
            <g transform={`translate(${r.x + r.w / 2 - pillW / 2}, ${r.y + r.h + 6.5})`}>
              <rect width={pillW} height={20} rx={10} fill={ACCENT} />
              <text x={pillW / 2} y={14} textAnchor="middle" fill="#fff" fontSize={11}>
                {label}
              </text>
            </g>
            <text x={r.x} y={r.y - 7} fill={ACCENT} fontSize={11}>{sel.b.id}</text>
          </g>
        )
      })()}

      {/* alignment guides, drawn only while a drag is live */}
      {guides.map((g, k) => (
        g.axis === 'x'
          ? <line key={k} x1={sx(g.board, g.at)} y1={sy(g.from)}
                  x2={sx(g.board, g.at)} y2={sy(g.to)}
                  stroke={GUIDE} strokeWidth={1} />
          : <line key={k} x1={sx(g.board, g.from)} y1={sy(g.at)}
                  x2={sx(g.board, g.to)} y2={sy(g.at)}
                  stroke={GUIDE} strokeWidth={1} />
      ))}

    </svg>
  )
}
