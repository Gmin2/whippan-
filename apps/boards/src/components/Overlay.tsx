import type { Artboard, Sel } from '../doc'
import type { NodeBox } from '../measure'
import type { Camera } from './Canvas'

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
}

const BLUE = '#2d52f0'
/** trim a caption to the width of its board so boards never overwrite each
 *  other's text at low zoom */
function fit(text: string, px: number): string {
  const max = Math.floor(px / 5.6)
  if (max < 4) return ''
  return text.length > max ? text.slice(0, max - 1) + '…' : text
}
/** resize handle size in screen pixels, so it stays grabbable at any zoom */
const HANDLE = 7

// Chrome drawn over the engine surface: board labels and captions, the hover
// outline and the selection box with its handles. Everything is positioned in
// screen space from the camera, so it tracks pan and zoom exactly without
// being scaled by them — a handle is always the same size under the cursor.
export default function Overlay({
  cam, boards, frames, worldX, docSize, title, selected, hover,
  activeScene, onSelectScene,
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

      {boards.map((b, i) => {
        const x = sx(i, 0)
        const w = dw * zoom
        if (x > 4000 || x + w < -400) return null
        return (
          <g key={b.id}>
            <text
              x={x} y={sy(0) - 10} fontSize={12}
              className="pointer-events-auto cursor-pointer"
              fill={activeScene === b.id ? BLUE : 'rgba(0,0,0,0.45)'}
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
            <rect x={x} y={sy(0)} width={w} height={dh * zoom} fill="none"
                  stroke={activeScene === b.id && !selected ? BLUE : 'rgba(0,0,0,0.10)'}
                  strokeWidth={activeScene === b.id && !selected ? 1.5 : 1} />
          </g>
        )
      })}

      {hov && (() => {
        const r = rectOf(hov.i, hov.b)
        return <rect x={r.x} y={r.y} width={r.w} height={r.h}
                     fill="none" stroke={BLUE} strokeWidth={1} opacity={0.55} />
      })()}

      {sel && (() => {
        const r = rectOf(sel.i, sel.b)
        const pts: [number, number][] = [
          [r.x, r.y], [r.x + r.w / 2, r.y], [r.x + r.w, r.y],
          [r.x + r.w, r.y + r.h / 2],
          [r.x + r.w, r.y + r.h], [r.x + r.w / 2, r.y + r.h], [r.x, r.y + r.h],
          [r.x, r.y + r.h / 2],
        ]
        return (
          <g>
            <rect x={r.x} y={r.y} width={r.w} height={r.h}
                  fill="none" stroke={BLUE} strokeWidth={1.5} />
            {pts.map(([hx, hy], k) => (
              <rect key={k} x={hx - HANDLE / 2} y={hy - HANDLE / 2}
                    width={HANDLE} height={HANDLE} rx={1.5}
                    fill="#fff" stroke={BLUE} strokeWidth={1.25} />
            ))}
            <text x={r.x} y={r.y - 7} fill={BLUE} fontSize={11}>
              {sel.b.id}
            </text>
            <text x={r.x + r.w} y={r.y + r.h + 14} textAnchor="end"
                  fill={BLUE} fontSize={10} fontFamily="monospace">
              {Math.round(sel.b.w)} × {Math.round(sel.b.h)}
            </text>
          </g>
        )
      })()}
    </svg>
  )
}
