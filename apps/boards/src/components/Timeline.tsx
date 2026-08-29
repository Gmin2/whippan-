import { useCallback, useEffect, useRef, useState } from 'react'
import { lanesOf, sceneAt, spanColor } from '../motion'
import type { Doc } from '../engine/types'
import type { Sel } from '../doc'

interface Props {
  doc: Doc
  dur: number
  t: number
  playing: boolean
  selected: Sel | null
  onSeek(t: number): void
  onPlay(playing: boolean): void
  onSelectNode(scene: string, id: string): void
}

const ACCENT = '#5e92f4'
const LANE_H = 22
const GUTTER = 132
/** the dock's height, in the same panel language as the side panels */
export const DOCK_H = 248

const fmt = (t: number) => {
  const m = Math.floor(t / 60)
  const s = t - m * 60
  return `${m}:${s.toFixed(2).padStart(5, '0')}`
}

/** a tick every 1s, or every 5s once the film is long enough that 1s crowds */
function tickStep(dur: number, px: number): number {
  const perSec = px / Math.max(dur, 0.001)
  for (const step of [0.5, 1, 2, 5, 10, 30]) {
    if (step * perSec >= 54) return step
  }
  return 60
}

const IconPlay = () => (
  <svg width="12" height="12" viewBox="0 0 20 20" aria-hidden>
    <polygon points="6 4 16 10 6 16 6 4" fill="currentColor" />
  </svg>
)

const IconPause = () => (
  <svg width="12" height="12" viewBox="0 0 20 20" aria-hidden>
    <rect x="5.5" y="4" width="3.5" height="12" fill="currentColor" />
    <rect x="11" y="4" width="3.5" height="12" fill="currentColor" />
  </svg>
)

/**
 * The timeline dock: the film along the bottom, the active scene's nodes as
 * lanes, and a playhead you can drag. This is the after-effects-shaped half of
 * motion mode — the storyboard above stays the wall.
 */
export default function Timeline({
  doc, dur, t, playing, selected, onSeek, onPlay, onSelectNode,
}: Props) {
  const track = useRef<HTMLDivElement>(null)
  const [width, setWidth] = useState(0)
  const scrub = useRef(false)

  useEffect(() => {
    const el = track.current
    if (!el) return
    const ro = new ResizeObserver(() => setWidth(el.getBoundingClientRect().width))
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  const at = sceneAt(doc, t)
  const scene = doc.stage.scenes[at.index]
  const lanes = lanesOf(doc, at.id)
  const sceneDur = scene?.dur ?? 3

  const x = useCallback((sec: number) => (sec / Math.max(dur, 0.001)) * width, [dur, width])
  const secAt = useCallback((px: number) => (px / Math.max(width, 1)) * dur, [dur, width])

  const seekFrom = useCallback((clientX: number) => {
    const el = track.current
    if (!el) return
    const r = el.getBoundingClientRect()
    onSeek(Math.min(dur, Math.max(0, secAt(clientX - r.left))))
  }, [dur, onSeek, secAt])

  useEffect(() => {
    const move = (e: PointerEvent) => { if (scrub.current) seekFrom(e.clientX) }
    const up = () => { scrub.current = false }
    window.addEventListener('pointermove', move)
    window.addEventListener('pointerup', up)
    return () => {
      window.removeEventListener('pointermove', move)
      window.removeEventListener('pointerup', up)
    }
  }, [seekFrom])

  const step = tickStep(dur, width)
  const ticks: number[] = []
  for (let s = 0; s <= dur + 0.001; s += step) ticks.push(s)

  // scene boundaries, for the block row and the lane background
  let acc = 0
  const blocks = doc.stage.scenes.map(s => {
    const from = acc
    acc += s.dur ?? 3
    return { id: s.id, from, to: acc }
  })

  return (
    <div className="relative flex shrink-0 flex-col border-t border-hair bg-panel"
         style={{ height: DOCK_H }}>
      {/* transport */}
      <div className="flex h-[34px] shrink-0 items-center gap-3 border-b border-hair px-3">
        <button
          onClick={() => onPlay(!playing)}
          title={playing ? 'pause  space' : 'play  space'}
          className="grid h-6 w-6 place-items-center rounded-[5px] text-ink/70
                     transition-colors hover:bg-black/[0.05] hover:text-ink"
        >
          {playing ? <IconPause /> : <IconPlay />}
        </button>
        <span className="font-mono text-[11px] tabular-nums">{fmt(t)}</span>
        <span className="font-mono text-[11px] text-faint tabular-nums">/ {fmt(dur)}</span>
        <span className="h-3.5 w-px bg-hair" />
        <span className="text-dim">
          scene <span className="text-ink">{at.id}</span>
          <span className="ml-1.5 font-mono text-[10px] text-faint tabular-nums">
            {at.local.toFixed(2)}s of {sceneDur.toFixed(2)}s
          </span>
        </span>
        <span className="ml-auto font-mono text-[10px] text-faint tabular-nums">
          {doc.stage.fps ?? 30} fps
        </span>
      </div>

      {/* ruler + scene blocks */}
      <div className="flex h-[38px] shrink-0 border-b border-hair">
        <div className="w-[132px] shrink-0 border-r border-hair px-3 py-1.5">
          <p className="text-[10px] uppercase tracking-[0.14em] text-faint">scenes</p>
        </div>
        <div
          ref={track}
          onPointerDown={e => { scrub.current = true; seekFrom(e.clientX) }}
          className="relative min-w-0 flex-1 cursor-ew-resize select-none"
        >
          {ticks.map(s => (
            <div key={s} className="absolute top-0 h-full" style={{ left: x(s) }}>
              <span className="absolute top-0 h-[6px] w-px bg-black/15" />
              <span className="absolute top-[7px] font-mono text-[9px] text-faint">
                {s.toFixed(step < 1 ? 1 : 0)}s
              </span>
            </div>
          ))}
          {blocks.map(b => (
            <button
              key={b.id}
              onPointerDown={e => e.stopPropagation()}
              onClick={() => onSeek(b.from + 0.01)}
              className={`absolute bottom-[3px] h-[15px] overflow-hidden rounded-[3px]
                          border text-left transition-colors
                          ${b.id === at.id
                            ? 'border-[#5e92f4] bg-[#5e92f4]/15'
                            : 'border-black/10 bg-black/[0.04] hover:bg-black/[0.07]'}`}
              style={{ left: x(b.from) + 1, width: Math.max(2, x(b.to) - x(b.from) - 2) }}
            >
              <span className="px-1 font-mono text-[9px] leading-[13px] text-dim">{b.id}</span>
            </button>
          ))}
        </div>
      </div>

      {/* lanes for the scene under the playhead */}
      <div className="flex min-h-0 flex-1">
        <div className="w-[132px] shrink-0 overflow-y-auto border-r border-hair">
          {lanes.map(l => (
            <button
              key={l.target}
              onClick={() => onSelectNode(at.id, l.target)}
              className={`flex w-full items-center gap-1.5 px-3 text-left
                          ${selected?.id === l.target ? 'bg-row' : 'hover:bg-black/[0.035]'}`}
              style={{ height: LANE_H }}
            >
              <span className="truncate text-[11px]">{l.target}</span>
              {!l.spans.length && (
                <span className="ml-auto text-[9px] text-faint">static</span>
              )}
            </button>
          ))}
          {!lanes.length && (
            <p className="px-3 py-2 text-[10px] text-faint">no nodes in this scene</p>
          )}
        </div>

        <div className="relative min-w-0 flex-1 overflow-y-auto">
          {/* the active scene's extent, so lane times read against it */}
          {blocks.map(b => (
            <div key={b.id} className="pointer-events-none absolute top-0 h-full"
                 style={{
                   left: x(b.from),
                   width: Math.max(1, x(b.to) - x(b.from)),
                   background: b.id === at.id ? 'rgba(94,146,244,0.05)' : 'transparent',
                   borderRight: '1px solid rgba(0,0,0,0.07)',
                 }} />
          ))}
          {lanes.map(l => {
            const base = blocks.find(b => b.id === at.id)?.from ?? 0
            return (
              <div key={l.target} className="relative" style={{ height: LANE_H }}>
                {l.spans.map((sp, i) => {
                  const left = x(base + sp.t0)
                  const w = Math.max(3, x(base + sp.t1) - x(base + sp.t0))
                  return (
                    <div
                      key={i}
                      title={`${sp.prop}  ${sp.t0.toFixed(2)}–${sp.t1.toFixed(2)}s${sp.looped ? '  looped' : ''}`}
                      className="absolute top-[4px] h-[14px] rounded-[3px] px-1"
                      style={{
                        left,
                        width: w,
                        background: `${spanColor(sp.kind)}22`,
                        border: `1px solid ${spanColor(sp.kind)}`,
                      }}
                    >
                      {w > 46 && (
                        <span className="font-mono text-[9px] leading-[12px]"
                              style={{ color: spanColor(sp.kind) }}>
                          {sp.prop}
                        </span>
                      )}
                      {/* keyframe diamonds sit on the span at their own times */}
                      {sp.keys.map((k, ki) => {
                        const kx = x(base + (sp.t0 - Math.min(...sp.keys.map(q => q.t)) + k.t))
                        return (
                          <span
                            key={ki}
                            className="absolute top-[3.5px] h-[7px] w-[7px] rotate-45"
                            style={{
                              left: kx - left - 3.5,
                              background: '#fff',
                              border: `1.25px solid ${spanColor(sp.kind)}`,
                            }}
                          />
                        )
                      })}
                    </div>
                  )
                })}
              </div>
            )
          })}
        </div>

      </div>

      <Playhead x={x(t) + GUTTER} />
    </div>
  )
}

function Playhead({ x }: { x: number }) {
  return (
    <div className="pointer-events-none absolute bottom-0 z-10"
         style={{ left: x, top: 34, height: DOCK_H - 34 }}>
      <span className="absolute -left-px top-0 h-full w-[1.5px]" style={{ background: ACCENT }} />
      <span className="absolute -left-[5px] top-0 h-[9px] w-[11px] rounded-b-[2px]"
            style={{ background: ACCENT }} />
    </div>
  )
}
