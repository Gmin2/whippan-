import { useEffect, useRef, useState } from 'react'
import type { Artboard, Board } from '../doc'

interface Props {
  board: Board
  selected: string | null
  onSelect(id: string | null): void
  onZoom(z: number): void
}

const BOARD_W = 260
const GAP = 68

function Card({ a, selected, onSelect }: {
  a: Artboard
  selected: boolean
  onSelect(): void
}) {
  const h = Math.round((BOARD_W * a.h) / a.w)
  return (
    <div className="shrink-0" style={{ width: BOARD_W }}>
      <button
        onClick={e => { e.stopPropagation(); onSelect() }}
        className={`mb-2 block text-left transition-colors
                    ${selected ? 'text-ink' : 'text-black/35 hover:text-black/60'}`}
        style={{ fontSize: 13 }}
      >
        {a.label}
      </button>
      <button
        onClick={e => { e.stopPropagation(); onSelect() }}
        className="block w-full bg-white text-left"
        style={{
          height: h,
          outline: selected ? '1.5px solid #2d52f0' : '1px solid rgba(0,0,0,0.06)',
          outlineOffset: selected ? 1 : 0,
        }}
      >
        {/* placeholder for the engine frame that will render here */}
        <span className="block px-3 pt-3 text-[9px] leading-snug text-black/40">
          {a.note}
        </span>
      </button>
      <div className="mt-1.5 flex items-baseline gap-2 text-[9px] text-black/35">
        <span className="truncate">{a.name}</span>
        <span className="ml-auto shrink-0 font-mono">{a.dur.toFixed(1)}s</span>
      </div>
    </div>
  )
}

export default function Canvas({ board, selected, onSelect, onZoom }: Props) {
  const ref = useRef<HTMLDivElement>(null)
  const [pan, setPan] = useState({ x: 96, y: 96 })
  const [zoom, setZoom] = useState(1)
  const drag = useRef<{ x: number; y: number } | null>(null)

  useEffect(() => { onZoom(zoom) }, [zoom, onZoom])

  // wheel pans, cmd/ctrl wheel zooms at the pointer, drag on empty pans
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const onWheel = (e: WheelEvent) => {
      e.preventDefault()
      if (e.metaKey || e.ctrlKey) {
        const r = el.getBoundingClientRect()
        const mx = e.clientX - r.left
        const my = e.clientY - r.top
        setZoom(z => {
          const next = Math.min(4, Math.max(0.1, z * Math.exp(-e.deltaY * 0.0015)))
          const k = next / z
          setPan(p => ({ x: mx - (mx - p.x) * k, y: my - (my - p.y) * k }))
          return next
        })
      } else {
        setPan(p => ({ x: p.x - e.deltaX, y: p.y - e.deltaY }))
      }
    }
    el.addEventListener('wheel', onWheel, { passive: false })
    return () => el.removeEventListener('wheel', onWheel)
  }, [])

  return (
    <div
      ref={ref}
      onPointerDown={e => {
        drag.current = { x: e.clientX, y: e.clientY }
        ;(e.target as HTMLElement).setPointerCapture?.(e.pointerId)
      }}
      onPointerMove={e => {
        const d = drag.current
        if (!d) return
        setPan(p => ({ x: p.x + e.clientX - d.x, y: p.y + e.clientY - d.y }))
        drag.current = { x: e.clientX, y: e.clientY }
      }}
      onPointerUp={() => { drag.current = null }}
      onClick={() => onSelect(null)}
      className="relative h-full flex-1 cursor-grab overflow-hidden active:cursor-grabbing"
      style={{ background: board.ground }}
    >
      <div
        className="absolute origin-top-left"
        style={{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})` }}
      >
        {/* free text living on the canvas itself, not inside any board */}
        <div className="mb-7 select-none" style={{ color: 'rgba(255,255,255,0.72)' }}>
          {board.canvasText.map(t => (
            <div key={t} className="leading-tight" style={{ fontSize: 21 }}>{t}</div>
          ))}
        </div>

        <div className="flex items-start" style={{ gap: GAP }}>
          {board.artboards.map(a => (
            <Card key={a.id} a={a} selected={a.id === selected}
                  onSelect={() => onSelect(a.id)} />
          ))}
        </div>
      </div>

      {/* another editor in the file */}
      <div className="pointer-events-none absolute" style={{ left: '52%', top: '38%' }}>
        <svg width="14" height="18" viewBox="0 0 12 15" className="drop-shadow-sm">
          <path d="M1 1l9.5 6.2-4.3.6-2 4.1z" fill="#d6407f" stroke="#fff" strokeWidth="1" />
        </svg>
        <span className="mt-0.5 block rounded-[4px] px-1.5 py-0.5 text-[10px] text-white"
              style={{ background: '#d6407f' }}>
          Anonymous
        </span>
      </div>
    </div>
  )
}
