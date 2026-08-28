import type { Artboard, Sel } from '../doc'
import type { NodeBox } from '../measure'
import { handlePoints } from '../handles'
import { elbow } from '../wires'
import type { Camera } from './Canvas'
import type { Guide } from '../snap'

interface Frame {
  boxes: NodeBox[]
}

interface Props {
  cam: Camera
  boards: Artboard[]
  frames: Frame[]
  worldX(i: number): number
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
/** connector grey, quiet enough to read as structure rather than content */
const WIRE = 'rgba(0,0,0,0.22)'
const PORT = 5
/** snap guides are crimson there, not the selection blue */
const GUIDE = '#dc4f70'
/** trim a caption to the width of its board so boards never overwrite each
 *  other's text at low zoom */
function fit(text: string, px: number): string {
  const max = Math.floor(px / 5.6)
  if (max < 4) return ''
  return text.length > max ? text.slice(0, max - 1) + '…' : text
}
/** 8.5 css px outer square, white fill, 1.5px accent border, square corners */
const HANDLE = 8.5

// Chrome drawn over the engine surface: board labels and captions, the hover
// outline and the selection box with its handles. Everything is positioned in
// screen space from the camera, so it tracks pan and zoom exactly without
// being scaled by them — a handle is always the same size under the cursor.
export default function Overlay({
  cam, boards, frames, worldX, docSize, title, selected, hover,
  activeScene, onSelectScene, guides, dragging,
}: Props) {
  const [dw, dh] = docSize
  const { pan, zoom } = cam
  const sx = (i: number, x: number) => (worldX(i) + x) * zoom + pan.x
  const sy = (y: number) => y * zoom + pan.y

  const find = (s: { scene: string; id: string } | null) => {
    if (!s) return null
    for (let i = 0; i < frames.length; i++) {
      const b = frames[i].boxes.find(n => n.id === s.id && n.scene === s.scene)
      if (b) return { i, b }
    }
    return null
  }
  const sel = find(selected)
  const same = hover && selected &&
    hover.id === selected.id && hover.scene === selected.scene
  const hov = same ? null : find(hover)

  const rectOf = (i: number, b: NodeBox) => ({
    x: sx(i, b.x),
    y: sy(b.y),
    w: b.w * zoom,
    h: b.h * zoom,
  })

  return (
    <svg className="pointer-events-none absolute inset-0 h-full w-full"
         style={{ overflow: 'visible' }}>
      {/* the film name, living on the canvas rather than in any board */}
      <text x={sx(0, 0)} y={sy(0) - 78} fill="rgba(255,255,255,0.75)" fontSize={22}>
        {title[0]}
      </text>
      <text x={sx(0, 0)} y={sy(0) - 50} fill="rgba(255,255,255,0.6)" fontSize={15}>
        {title[1]}
      </text>

      {/* seams: how each scene enters the one before it, and the node ids
          that carry across the cut. a linear film gives straight wires; the
          fan appears wherever a morph pairs several nodes at once. */}
      {boards.map((b, i) => {
        if (i === 0) return null
        const x1 = sx(i - 1, dw)
        const x2 = sx(i, 0)
        if (x2 < -200 || x1 > 4000) return null
        const midY = sy(dh / 2)
        const kind = b.transition?.kind ?? 'cut'
        const morph = b.transition?.morph
        const threads = morph ? b.carried.slice(0, 8) : []
        return (
          <g key={`seam-${b.id}`}>
            <circle cx={x1} cy={midY} r={PORT / 2} fill={WIRE} />
            <path d={elbow(x1, midY, x2, midY, 10 * zoom)} fill="none"
                  stroke={WIRE} strokeWidth={1} />
            <circle cx={x2} cy={midY} r={PORT / 2} fill={WIRE} />
            {zoom > 0.05 && (
              <g transform={`translate(${(x1 + x2) / 2}, ${midY})`}>
                <rect x={-26} y={-9} width={52} height={18} rx={9}
                      fill="#fff" stroke="rgba(0,0,0,0.12)" />
                <text y={4} textAnchor="middle" fontSize={10}
                      fill={morph ? ACCENT : 'rgba(0,0,0,0.55)'}>
                  {morph ? 'morph' : kind}
                </text>
              </g>
            )}
            {threads.map(id => {
              const a = frames[i - 1]?.boxes.find(n => n.id === id)
              const c = frames[i]?.boxes.find(n => n.id === id)
              if (!a || !c) return null
              return (
                <path
                  key={id}
                  d={elbow(sx(i - 1, a.x + a.w), sy(a.y + a.h / 2),
                           sx(i, c.x), sy(c.y + c.h / 2), 12 * zoom)}
                  fill="none" stroke={ACCENT} strokeWidth={1} opacity={0.5}
                  strokeDasharray="3 3"
                />
              )
            })}
          </g>
        )
      })}

      {boards.map((b, i) => {
        const x = sx(i, 0)
        const w = dw * zoom
        if (x > 4000 || x + w < -400) return null
        return (
          <g key={b.id}>
            <text
              x={x} y={sy(0) - 10} fontSize={12}
              className="pointer-events-auto cursor-pointer"
              fill={activeScene === b.id ? ACCENT : 'rgba(0,0,0,0.45)'}
              fontWeight={activeScene === b.id ? 600 : 400}
              onPointerDown={e => { e.stopPropagation(); onSelectScene(b.id) }}
            >
              {b.label}
            </text>
            <text x={x} y={sy(dh) + 18} fill="rgba(0,0,0,0.4)" fontSize={11}>
              {fit(b.note, w - 34)}
            </text>
            <text x={x + w} y={sy(dh) + 18} textAnchor="end"
                  fill="rgba(0,0,0,0.4)" fontSize={11} fontFamily="monospace">
              {b.dur.toFixed(1)}s
            </text>
            {/* no outline at rest: a board is defined by its own ground
                against the canvas, not by a box drawn around it */}
            {activeScene === b.id && !selected && (
              <rect x={x} y={sy(0)} width={w} height={dh * zoom}
                    fill="none" stroke={ACCENT} strokeWidth={1.5} />
            )}
          </g>
        )
      })}

      {!dragging && hov && (() => {
        const r = rectOf(hov.i, hov.b)
        return <rect x={r.x} y={r.y} width={r.w} height={r.h}
                     fill="none" stroke={ACCENT} strokeWidth={1} />
      })()}

      {sel && !dragging && (() => {
        const r = rectOf(sel.i, sel.b)
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
