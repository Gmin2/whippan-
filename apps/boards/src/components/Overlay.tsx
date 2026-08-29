import type { Artboard, Sel } from '../doc'
import type { NodeBox } from '../measure'
import { handlePoints } from '../handles'
import { CARD, GAP_Y, HEADER_GAP, cardBox } from '../layout'
import { elbow } from '../wires'
import { glyph, isDefault, kindOf } from '../transitions'
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
  /** the rest of the selection: outlined, but only the primary gets handles */
  others: Sel[]
  hover: NodeBox | null
  activeScene: string | null
  onSelectScene(scene: string): void
  /** alignment guides produced by the live drag, in document space */
  guides: Guide[]
  /** chrome hides while dragging: only artwork and guides stay */
  dragging: boolean
  /** the path being drawn, in document space */
  pen: { board: number; pts: { x: number; y: number }[]; cursor: { x: number; y: number } | null } | null
  mode: 'design' | 'motion'
  /** the seam whose transition is being edited: the scene it enters */
  selectedSeam: string | null
  onSelectSeam(sceneId: string | null): void
}

/** sampled off paper's own overlay canvas */
const ACCENT = '#5e92f4'
/** snap guides are crimson there, not the selection blue */
const GUIDE = '#dc4f70'

/** the seam chip needs this much gap before its label fits between two boards */
const SEAM_FULL = 66
/** below that it becomes a round mark carrying only the transition's glyph */
const SEAM_MARK = 18
/** 8.5 css px outer square, white fill, 1.5px accent border, square corners */
const HANDLE = 8.5

// Chrome drawn over the engine surface: board labels and captions, the hover
// outline and the selection box with its handles. Everything is positioned in
// screen space from the camera, so it tracks pan and zoom exactly without
// being scaled by them — a handle is always the same size under the cursor.
export default function Overlay({
  cam, boards, columns, worldX, worldY, selRow, docSize, title, selected, others, hover,
  activeScene, onSelectScene, guides, dragging, pen, mode,
  selectedSeam, onSelectSeam,
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

  /**
   * What a script card actually needs.
   *
   * The height follows the copy rather than the zoom. The card's text is drawn
   * in screen pixels so it stays legible, which means a card scaled by zoom
   * ends up either cramped or mostly empty; sizing it to the wrapped lines
   * keeps it honest at every scale. When there is no room for the copy the card
   * shrinks to a label strip instead of staying a slab you cannot read.
   */
  const cardOf = (b: Artboard) => cardBox(b.note, dw * zoom, mode === 'motion')

  /** the tallest card decides where the film title sits, so it never collides */
  const bandH = Math.max(0, ...boards.map(b => cardOf(b).h))

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
      <text x={sx(0, 0)} y={ry(0, 0) - HEADER_GAP * zoom - bandH - 34}
            fill="rgba(255,255,255,0.75)" fontSize={20}>
        {title[0]}
      </text>
      <text x={sx(0, 0)} y={ry(0, 0) - HEADER_GAP * zoom - bandH - 14}
            fill="rgba(255,255,255,0.55)" fontSize={13}>
        {title[1]}
      </text>

      {boards.map((b, i) => {
        const x = sx(i, 0)
        const w = dw * zoom
        if (x > 4000 || x + w < -400) return null
        const active = activeScene === b.id
        // it grows upward from the first frame, so a tall card can never eat
        // into the artwork it is labelling
        const { h: cardH, lines, pad } = cardOf(b)
        const cardY = ry(0, 0) - HEADER_GAP * zoom - cardH
        const roomForText = lines.length > 0

        return (
          <g key={b.id}>
            {cardH > 0 && (
              <rect x={x} y={cardY} width={w} height={cardH}
                    rx={Math.min(10, w * 0.03, cardH / 2)}
                    fill="#16241d"
                    className="pointer-events-auto cursor-pointer"
                    onPointerDown={e => { e.stopPropagation(); onSelectScene(b.id) }} />
            )}
            {cardH > 0 && (
              <text x={x + Math.max(5, pad)}
                    y={roomForText ? cardY + pad + 10 : cardY + cardH / 2 + 3.5}
                    fill="rgba(255,255,255,0.6)"
                    fontSize={10} fontFamily="monospace">
                {/* the duration is the first thing to go: a clipped "10 · 2.4"
                    is worse than a clean "10" */}
                {w > 68 ? `${b.label} · ${b.dur.toFixed(1)}s` : b.label}
              </text>
            )}
            {lines.map((line, li) => (
              <text key={li} x={x + pad} y={cardY + pad + CARD.title + 12 + li * CARD.lh}
                    fill="rgba(255,255,255,0.9)" fontSize={CARD.fs}>
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
                {/* row zero's gap is the header gap, not the row gap; using the
                    wrong one puts the timestamp under the script card */}
                {w > 70 && (k === 0 ? HEADER_GAP : GAP_Y) * zoom >= 13 && (
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

      {/* the followers: same outline, no handles, so it is obvious which node
          a resize belongs to */}
      {others.map(o => {
        const f = find(o)
        if (!f) return null
        const r = rectOf(f.i, f.k, f.b)
        return (
          <rect key={`${o.scene}/${o.id}`} x={r.x} y={r.y} width={r.w} height={r.h}
                fill="none" stroke={ACCENT} strokeWidth={1} strokeOpacity={0.7} />
        )
      })}

      {sel && !dragging && (() => {
        const r = rectOf(sel.i, sel.k, sel.b)
        const label = others.length
          ? `${others.length + 1} selected`
          : `${Math.round(sel.b.w)} × ${Math.round(sel.b.h)}`
        const pillW = label.length * 6.6 + 16
        return (
          <g>
            <rect x={r.x} y={r.y} width={r.w} height={r.h}
                  fill="none" stroke={ACCENT} strokeWidth={1.5} />
            {/* handles belong to one node; a set gets outlines and a count */}
            {!others.length && handlePoints(r).map(([hx, hy], k) => (
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

      {/* the seam: the gap between two boards is where the transition lives.
          clicking it edits that transition; morph threads show which nodes
          carry across the cut and which die at it. */}
      {boards.map((b, i) => {
        if (i === 0) return null
        const x1 = sx(i - 1, dw)
        const x2 = sx(i, 0)
        if (x2 < -300 || x1 > 4200) return null
        const midY = ry(0, dh / 2)
        const cx = (x1 + x2) / 2
        const gap = x2 - x1
        const on = selectedSeam === b.id
        const quiet = isDefault(b.transition)
        const stroke = on ? ACCENT : quiet ? 'rgba(0,0,0,0.16)' : 'rgba(0,0,0,0.34)'
        const threads = b.transition?.morph ? b.carried.slice(0, 10) : []

        return (
          <g key={`seam-${b.id}`}>
            <path d={elbow(x1, midY, x2, midY, 10 * zoom)} fill="none"
                  stroke={stroke} strokeWidth={on ? 1.6 : 1}
                  strokeDasharray={quiet ? '3 4' : undefined} />

            {threads.map(id => {
              const a = columns[i - 1]?.[0]?.boxes.find(n => n.id === id)
              const c = columns[i]?.[0]?.boxes.find(n => n.id === id)
              if (!a || !c) return null
              return (
                <path
                  key={id}
                  d={elbow(sx(i - 1, a.x + a.w), ry(0, a.y + a.h / 2),
                           sx(i, c.x), ry(0, c.y + c.h / 2), 14 * zoom)}
                  fill="none" stroke={ACCENT} strokeWidth={1}
                  opacity={0.45} strokeDasharray="3 3"
                />
              )
            })}

            {/* the chip has to live in the gap between two boards, so it
                degrades with it: label, then glyph, then nothing but a target.
                a 60px pill dropped into a 7px gap lands on the artwork either
                side and turns a wall of scenes into a row of collisions. */}
            <g className="pointer-events-auto cursor-pointer"
               onPointerDown={e => { e.stopPropagation(); onSelectSeam(on ? null : b.id) }}>
              {gap >= SEAM_FULL ? (
                <>
                  <rect x={cx - 30} y={midY - 11} width={60} height={22} rx={11}
                        fill={on ? ACCENT : '#fff'}
                        stroke={on ? ACCENT : 'rgba(0,0,0,0.14)'} strokeWidth={1} />
                  <text x={cx} y={midY + 4} textAnchor="middle" fontSize={10}
                        fill={on ? '#fff' : quiet ? 'rgba(0,0,0,0.45)' : ACCENT}>
                    {glyph(b.transition)} {b.transition?.morph ? 'morph' : kindOf(b.transition)}
                  </text>
                </>
              ) : gap >= SEAM_MARK ? (
                <>
                  <circle cx={cx} cy={midY} r={Math.min(9, gap / 2 - 1)}
                          fill={on ? ACCENT : '#fff'}
                          stroke={on ? ACCENT : 'rgba(0,0,0,0.14)'} strokeWidth={1} />
                  <text x={cx} y={midY + 3} textAnchor="middle" fontSize={9}
                        fill={on ? '#fff' : quiet ? 'rgba(0,0,0,0.45)' : ACCENT}>
                    {glyph(b.transition)}
                  </text>
                </>
              ) : (
                <>
                  {/* nothing to draw but the seam still has to be clickable */}
                  <rect x={cx - 5} y={midY - 9} width={10} height={18} fill="transparent" />
                  {(on || !quiet) && (
                    <rect x={cx - 1} y={midY - 5} width={2} height={10} rx={1}
                          fill={on ? ACCENT : 'rgba(0,0,0,0.34)'} />
                  )}
                </>
              )}
            </g>
          </g>
        )
      })}

      {/* the path in progress: committed segments, a rubber band to the
          cursor, and anchors sized the way paper draws them */}
      {pen && pen.pts.length > 0 && (() => {
        const px = (p: { x: number; y: number }) => [sx(pen.board, p.x), ry(0, p.y)] as const
        const pts = pen.pts.map(px)
        const line = pts.map(([x, y], i) => `${i ? 'L' : 'M'}${x} ${y}`).join(' ')
        const last = pts[pts.length - 1]
        const cur = pen.cursor ? px(pen.cursor) : null
        return (
          <g>
            <path d={line} fill="none" stroke="#111" strokeWidth={1} />
            {cur && (
              <line x1={last[0]} y1={last[1]} x2={cur[0]} y2={cur[1]}
                    stroke={ACCENT} strokeWidth={2} />
            )}
            {pts.map(([x, y], i) => (
              <circle key={i} cx={x} cy={y} r={i === 0 ? 5.5 : 3.5}
                      fill={i === 0 ? ACCENT : '#fff'}
                      stroke={i === 0 ? '#fff' : ACCENT} strokeWidth={2} />
            ))}
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
