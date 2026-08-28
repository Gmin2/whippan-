import { useEffect, useRef, useState } from 'react'
import { cachedScene, queueScene } from '../engine'
import type { Doc } from '../engine/types'
import type { Artboard } from '../doc'

interface Props {
  ck: CanvasKit
  doc: Doc
  ground: string
  title: string[]
  boards: Artboard[]
  selected: string | null
  onSelect(id: string | null): void
  onZoom(z: number): void
}

const BOARD_W = 300
const GAP = 56
/** frames are cut at 2x the on-canvas width so they stay sharp when zoomed in */
const CUT_W = BOARD_W * 2

function Card({ ck, doc, a, selected, onSelect }: {
  ck: CanvasKit
  doc: Doc
  a: Artboard
  selected: boolean
  onSelect(): void
}) {
  const ref = useRef<HTMLDivElement>(null)
  const key = `${doc.entry.slug}:${a.index}`
  const [src, setSrc] = useState<string | undefined>(() => cachedScene(key))
  const h = Math.round((BOARD_W * a.h) / a.w)

  useEffect(() => {
    if (src || !ref.current) return
    let alive = true
    const io = new IntersectionObserver(([e]) => {
      if (!e.isIntersecting) return
      io.disconnect()
      queueScene(ck, doc, a.index, CUT_W).then(u => { if (alive && u) setSrc(u) })
    }, { rootMargin: '600px' })
    io.observe(ref.current)
    return () => { alive = false; io.disconnect() }
  }, [ck, doc, a.index, src])

  return (
    <div ref={ref} className="shrink-0" style={{ width: BOARD_W }}>
      <button
        onClick={e => { e.stopPropagation(); onSelect() }}
        className={`mb-1.5 block text-left transition-colors
                    ${selected ? 'text-ink' : 'text-black/40 hover:text-black/65'}`}
        style={{ fontSize: 13 }}
      >
        {a.label}
      </button>
      <button
        onClick={e => { e.stopPropagation(); onSelect() }}
        className="block w-full overflow-hidden bg-white"
        style={{
          height: h,
          outline: selected ? '1.5px solid #2d52f0' : '1px solid rgba(0,0,0,0.07)',
          outlineOffset: selected ? 1 : 0,
        }}
      >
        {src
          ? <img src={src} alt="" className="h-full w-full" draggable={false} />
          : <span className="grid h-full place-items-center text-[10px] text-black/30">
              cutting frame
            </span>}
      </button>
      <div className="mt-1.5 flex items-baseline gap-2 text-[10px] text-black/40">
        <span className="truncate" title={a.note}>{a.note}</span>
        <span className="ml-auto shrink-0 font-mono">{a.dur.toFixed(1)}s</span>
      </div>
    </div>
  )
}

export default function Canvas({
  ck, doc, ground, title, boards, selected, onSelect, onZoom,
}: Props) {
  const ref = useRef<HTMLDivElement>(null)
  const [pan, setPan] = useState({ x: 96, y: 110 })
  const [zoom, setZoom] = useState(0.55)
  const drag = useRef<{ x: number; y: number } | null>(null)

  useEffect(() => { onZoom(zoom) }, [zoom, onZoom])

  // wheel pans, cmd/ctrl wheel zooms at the pointer
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
          const next = Math.min(4, Math.max(0.08, z * Math.exp(-e.deltaY * 0.0015)))
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
      onPointerDown={e => { drag.current = { x: e.clientX, y: e.clientY } }}
      onPointerMove={e => {
        const d = drag.current
        if (!d) return
        setPan(p => ({ x: p.x + e.clientX - d.x, y: p.y + e.clientY - d.y }))
        drag.current = { x: e.clientX, y: e.clientY }
      }}
      onPointerUp={() => { drag.current = null }}
      onPointerLeave={() => { drag.current = null }}
      onClick={() => onSelect(null)}
      className="relative h-full flex-1 cursor-grab overflow-hidden active:cursor-grabbing"
      style={{ background: ground }}
    >
      <div
        className="absolute origin-top-left"
        style={{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})` }}
      >
        {/* free text on the canvas itself, above the boards */}
        <div className="mb-8 select-none" style={{ color: 'rgba(255,255,255,0.75)' }}>
          {title.map(t => (
            <div key={t} className="leading-tight" style={{ fontSize: 26 }}>{t}</div>
          ))}
        </div>

        <div className="flex items-start" style={{ gap: GAP }}>
          {boards.map(a => (
            <Card key={a.id} ck={ck} doc={doc} a={a} selected={a.id === selected}
                  onSelect={() => onSelect(a.id)} />
          ))}
        </div>
      </div>

      {/* another editor in the file */}
      <div className="pointer-events-none absolute" style={{ left: '54%', top: '58%' }}>
        <svg width="14" height="18" viewBox="0 0 12 15">
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
