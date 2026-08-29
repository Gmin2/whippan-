import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { lanesOf, sceneAt, spanColor } from '../motion'
import type { Span } from '../motion'
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
const GUTTER = 150
const TRANSPORT_H = 34
const RULER_H = 38
/** one property band inside a lane, and the bar that sits in it */
const ROW_H = 16
const BAR_H = 13
const LANE_PAD = 3
/** a diamond is 7px on the diagonal; below this spacing they would touch */
const KEY_SIZE = 7
/** the rotated diamond's half-width, and the closest two may sit without touching */
const KEY_R = (KEY_SIZE * Math.SQRT2) / 2
const KEY_GAP = 12
const MAX_PPS = 1200
/** how much of the track the scene under the playhead should take in auto mode */
const SCENE_FILL = 0.72
/** the dock's height, in the same panel language as the side panels */
export const DOCK_H = 268

type Mode = 'fit' | 'scene' | 'free'

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v))

const fmt = (t: number) => {
  const m = Math.floor(t / 60)
  const s = t - m * 60
  return `${m}:${s.toFixed(2).padStart(5, '0')}`
}

/** the finest tick that still leaves room for its label */
function tickStep(pps: number): number {
  for (const step of [0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 30]) {
    if (step * pps >= 56) return step
  }
  return 60
}

/** key times are stored relative to the track's `at`, the span carries the shift */
function keyTimes(sp: Span): number[] {
  if (!sp.keys.length) return []
  let min = Infinity
  for (const k of sp.keys) min = Math.min(min, k.t)
  return sp.keys.map(k => sp.t0 - min + k.t)
}

interface Bar {
  t0: number
  t1: number
  keys: number[]
  color: string
  label: string
  title: string
}

const KIND_ORDER: Span['kind'][] = ['cam', 'reveal', 'state', 'enter', 'keys']

function barOf(group: Span[]): Bar {
  const t0 = Math.min(...group.map(s => s.t0))
  const t1 = Math.max(...group.map(s => s.t1))
  const props = [...new Set(group.map(s => s.prop))]
  const kind = KIND_ORDER.find(k => group.some(s => s.kind === k)) ?? 'keys'
  const keys = [...new Set(group.flatMap(keyTimes).map(v => Math.round(v * 1000)))]
    .sort((a, b) => a - b)
    .map(v => v / 1000)
  const looped = group.some(s => s.looped)
  return {
    t0,
    t1,
    keys,
    color: spanColor(kind),
    label: props.length <= 3 ? props.join(' · ') : `${props.length} props`,
    title: `${props.join(', ')}  ${t0.toFixed(2)}–${t1.toFixed(2)}s`
      + (keys.length ? `  ${keys.length} key${keys.length > 1 ? 's' : ''}` : '')
      + (looped ? '  looped' : ''),
  }
}

/** fold spans that overlap in time into one bar, so nothing is drawn on top of anything */
function clusters(spans: Span[]): Bar[] {
  const sorted = [...spans].sort((a, b) => a.t0 - b.t0)
  const out: Bar[] = []
  let group: Span[] = []
  let end = -Infinity
  for (const sp of sorted) {
    if (group.length && sp.t0 > end + 0.002) {
      out.push(barOf(group))
      group = []
      end = -Infinity
    }
    group.push(sp)
    end = Math.max(end, sp.t1)
  }
  if (group.length) out.push(barOf(group))
  return out
}

interface LaneRow {
  label: string
  bars: Bar[]
}

interface LaneView {
  target: string
  rows: LaneRow[]
  h: number
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

const IconMinus = () => (
  <svg width="10" height="10" viewBox="0 0 10 10" aria-hidden>
    <rect x="1" y="4.5" width="8" height="1" fill="currentColor" />
  </svg>
)

const IconPlus = () => (
  <svg width="10" height="10" viewBox="0 0 10 10" aria-hidden>
    <rect x="1" y="4.5" width="8" height="1" fill="currentColor" />
    <rect x="4.5" y="1" width="1" height="8" fill="currentColor" />
  </svg>
)

/**
 * The timeline dock: the film along the bottom, the active scene's nodes as
 * lanes, and a playhead you can drag. This is the after-effects-shaped half of
 * motion mode — the storyboard above stays the wall.
 *
 * The time axis has its own zoom (pixels per second) and scroll offset, so a
 * 28s film is not squeezed into the dock's width. Everything horizontal —
 * ruler, scene blocks, lanes, playhead — is placed from the same `pps`/`scroll`
 * pair, which is what keeps them lined up.
 */
export default function Timeline({
  doc, dur, t, playing, selected, onSeek, onPlay, onSelectNode,
}: Props) {
  const ruler = useRef<HTMLDivElement>(null)
  const lanesBox = useRef<HTMLDivElement>(null)
  const [viewW, setViewW] = useState(0)
  const [mode, setMode] = useState<Mode>('scene')
  const [pps, setPps] = useState(0)
  const [scroll, setScroll] = useState(0)
  const scrub = useRef(false)
  const ppsRef = useRef(0)
  const scrollRef = useRef(0)
  ppsRef.current = pps
  scrollRef.current = scroll

  useEffect(() => {
    const el = ruler.current
    if (!el) return
    const ro = new ResizeObserver(() => setViewW(el.getBoundingClientRect().width))
    ro.observe(el)
    setViewW(el.getBoundingClientRect().width)
    return () => ro.disconnect()
  }, [])

  const at = sceneAt(doc, t)
  const scene = doc.stage.scenes[at.index]
  const lanes = lanesOf(doc, at.id)
  const sceneDur = scene?.dur ?? 3

  // scene boundaries, for the block row and the lane background
  const blocks = useMemo(() => {
    let acc = 0
    return doc.stage.scenes.map(s => {
      const from = acc
      acc += s.dur ?? 3
      return { id: s.id, from, to: acc }
    })
  }, [doc])
  const base = blocks.find(b => b.id === at.id)?.from ?? 0

  const fitPps = viewW > 0 ? viewW / Math.max(dur, 0.001) : 0
  const contentW = dur * pps

  const clampScroll = useCallback(
    (s: number, p: number) => clamp(s, 0, Math.max(0, dur * p - viewW)),
    [dur, viewW],
  )

  useEffect(() => {
    if (!fitPps) return
    if (mode !== 'fit') return
    setPps(fitPps)
    setScroll(0)
  }, [mode, fitPps])

  // auto zoom: the scene under the playhead should own most of the track, since
  // the lanes only ever show that scene
  useEffect(() => {
    if (!fitPps || mode !== 'scene') return
    const next = clamp((viewW * SCENE_FILL) / Math.max(sceneDur, 0.05), fitPps, MAX_PPS)
    setPps(next)
    setScroll(clamp((base + sceneDur / 2) * next - viewW / 2, 0, Math.max(0, dur * next - viewW)))
  }, [mode, fitPps, viewW, base, sceneDur, dur, at.id])

  useEffect(() => {
    if (!pps) return
    setScroll(s => clampScroll(s, pps))
  }, [pps, clampScroll])

  // never let the playhead run off the edge of a zoomed view
  useEffect(() => {
    if (!pps || !viewW) return
    setScroll(s => {
      const px = t * pps - s
      if (px >= 8 && px <= viewW - 8) return s
      return clamp(t * pps - viewW / 2, 0, Math.max(0, dur * pps - viewW))
    })
  }, [t, pps, viewW, dur])

  const zoomAt = useCallback((factor: number, px: number) => {
    const cur = ppsRef.current || fitPps
    if (!cur) return
    const next = clamp(cur * factor, fitPps, MAX_PPS)
    const anchor = (scrollRef.current + px) / cur
    setMode('free')
    setPps(next)
    setScroll(clamp(anchor * next - px, 0, Math.max(0, dur * next - viewW)))
  }, [fitPps, dur, viewW])

  useEffect(() => {
    const els = [ruler.current, lanesBox.current].filter(Boolean) as HTMLElement[]
    if (!els.length) return
    const onWheel = (e: WheelEvent) => {
      const r = ruler.current?.getBoundingClientRect()
      if (!r || !pps) return
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault()
        const px = clamp(e.clientX - r.left, 0, viewW)
        zoomAt(Math.exp(-e.deltaY * 0.0018), px)
        return
      }
      const horiz = Math.abs(e.deltaX) > Math.abs(e.deltaY)
      const d = horiz ? e.deltaX : e.shiftKey || e.currentTarget === ruler.current ? e.deltaY : 0
      if (!d || dur * pps <= viewW) return
      e.preventDefault()
      setScroll(s => clampScroll(s + d, pps))
    }
    for (const el of els) el.addEventListener('wheel', onWheel, { passive: false })
    return () => { for (const el of els) el.removeEventListener('wheel', onWheel) }
  }, [pps, viewW, dur, zoomAt, clampScroll])

  const seekFrom = useCallback((clientX: number) => {
    const el = ruler.current
    if (!el || !pps) return
    const r = el.getBoundingClientRect()
    onSeek(clamp((clientX - r.left + scroll) / pps, 0, dur))
  }, [dur, onSeek, pps, scroll])

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

  const step = tickStep(pps)
  const dec = step < 0.1 ? 2 : step < 1 ? 1 : 0
  const ticks: number[] = []
  if (pps) {
    const from = Math.max(0, Math.floor((scroll / pps) / step) * step)
    const to = Math.min(dur, (scroll + viewW) / pps)
    for (let s = from; s <= to + 1e-6; s += step) ticks.push(Math.round(s * 1000) / 1000)
  }

  const view: LaneView[] = useMemo(() => lanes.map(l => {
    if (!l.spans.length) {
      return { target: l.target, rows: [{ label: 'static', bars: [] }], h: ROW_H + LANE_PAD * 2 }
    }
    const props = [...new Set(l.spans.map(s => s.prop))]
    const expand = selected?.scene === at.id && selected?.id === l.target && props.length > 1
    const rows: LaneRow[] = expand
      ? props.map(p => ({ label: p, bars: clusters(l.spans.filter(s => s.prop === p)) }))
      : [{ label: props.length === 1 ? props[0] : `${props.length} props`, bars: clusters(l.spans) }]
    return { target: l.target, rows, h: rows.length * ROW_H + LANE_PAD * 2 }
  }), [lanes, selected, at.id])

  const sceneL = base * pps - scroll
  const sceneR = (base + sceneDur) * pps - scroll

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

        <div className="ml-auto flex items-center gap-1.5">
          <div className="flex items-center gap-[3px]">
            <ModeBtn label="fit" title="fit the whole film" on={mode === 'fit'}
                     onClick={() => setMode('fit')} />
            <ModeBtn label="scene" title="fill the scene under the playhead" on={mode === 'scene'}
                     onClick={() => setMode('scene')} />
          </div>
          <div className="flex items-center gap-[2px]">
            <StepBtn title="zoom out" onClick={() => zoomAt(1 / 1.6, viewW / 2)}><IconMinus /></StepBtn>
            <span className="w-[30px] text-center font-mono text-[10px] text-dim tabular-nums">
              {fitPps ? (pps / fitPps).toFixed(1) : '1.0'}×
            </span>
            <StepBtn title="zoom in" onClick={() => zoomAt(1.6, viewW / 2)}><IconPlus /></StepBtn>
          </div>
          <span className="h-3.5 w-px bg-hair" />
          <span className="font-mono text-[10px] text-faint tabular-nums">
            {doc.stage.fps ?? 30} fps
          </span>
        </div>
      </div>

      {/* ruler + scene blocks */}
      <div className="flex shrink-0 border-b border-hair" style={{ height: RULER_H }}>
        <div className="shrink-0 border-r border-hair px-3 py-1.5" style={{ width: GUTTER }}>
          <p className="text-[10px] uppercase tracking-[0.14em] text-faint">scenes</p>
        </div>
        <div
          ref={ruler}
          onPointerDown={e => { scrub.current = true; seekFrom(e.clientX) }}
          className="relative min-w-0 flex-1 cursor-ew-resize select-none overflow-hidden"
        >
          <div className="absolute inset-y-0"
               style={{ width: contentW, left: -scroll }}>
            {ticks.map(s => (
              <div key={s} className="absolute top-0 h-full" style={{ left: s * pps }}>
                <span className="absolute top-0 h-[6px] w-px bg-black/15" />
                <span className="absolute top-[7px] font-mono text-[9px] text-faint tabular-nums">
                  {s.toFixed(dec)}s
                </span>
              </div>
            ))}
            {blocks.map(b => {
              const left = b.from * pps
              const w = Math.max(2, (b.to - b.from) * pps - 2)
              if (left > scroll + viewW + 40 || left + w < scroll - 40) return null
              const on = b.id === at.id
              return (
                <button
                  key={b.id}
                  title={`${b.id}  ${(b.to - b.from).toFixed(2)}s`}
                  onPointerDown={e => e.stopPropagation()}
                  onClick={() => onSeek(b.from + 0.01)}
                  className={`absolute bottom-[3px] h-[15px] overflow-hidden rounded-[3px]
                              border text-left transition-colors
                              ${on
                                ? 'border-[#5e92f4] bg-[#5e92f4]/15'
                                : 'border-black/10 bg-black/[0.04] hover:bg-black/[0.07]'}`}
                  style={{ left: left + 1, width: w }}
                >
                  <span className={`block truncate pr-1 font-mono text-[9px] leading-[13px]
                                    ${on ? 'text-ink/70' : 'text-dim'}`}
                        style={{ paddingLeft: 4 + clamp(scroll - left, 0, Math.max(0, w - 26)) }}>
                    {b.id}
                  </span>
                </button>
              )
            })}
          </div>
        </div>
      </div>

      {/* lanes for the scene under the playhead */}
      <div ref={lanesBox} className="min-h-0 flex-1 overflow-x-hidden overflow-y-auto">
        <div className="relative min-h-full">
          {view.map((l, i) => {
            const on = selected?.scene === at.id && selected.id === l.target
            return (
              <button
                key={l.target}
                type="button"
                onClick={() => onSelectNode(at.id, l.target)}
                style={{ height: l.h }}
                className={`relative flex w-full border-b border-hair/70 text-left
                            ${on ? 'bg-[#5e92f4]/[0.10]' : i % 2 ? 'bg-black/[0.018]' : ''}
                            ${on ? '' : 'hover:bg-black/[0.045]'}`}
              >
                {on && <span className="absolute inset-y-0 left-0 w-[2px]" style={{ background: ACCENT }} />}
                <span className="flex shrink-0 flex-col justify-center border-r border-hair pl-3 pr-2"
                      style={{ width: GUTTER, paddingTop: LANE_PAD, paddingBottom: LANE_PAD }}>
                  {l.rows.map((r, ri) => (
                    <span key={ri} className="flex items-center gap-1.5" style={{ height: ROW_H }}>
                      {ri === 0 && (
                        <span className={`truncate text-[11px] ${on ? 'text-ink' : 'text-ink/80'}`}
                              title={l.target}>
                          {l.target}
                        </span>
                      )}
                      <span className="ml-auto shrink-0 truncate font-mono text-[9px] text-faint"
                            title={r.label} style={{ maxWidth: ri === 0 ? 66 : 96 }}>
                        {r.label}
                      </span>
                    </span>
                  ))}
                </span>

                <span className="relative block min-w-0 flex-1 overflow-hidden">
                  <span className="absolute inset-y-0 block"
                        style={{ width: contentW, left: -scroll }}>
                    {l.rows.map((r, ri) => r.bars.map((b, bi) => (
                      <BarView key={`${ri}-${bi}`} bar={b} pps={pps} base={base}
                               top={LANE_PAD + ri * ROW_H + (ROW_H - BAR_H) / 2}
                               scroll={scroll} viewW={viewW} strong={on} />
                    )))}
                  </span>
                </span>
              </button>
            )
          })}
          {!view.length && (
            <p className="px-3 py-2 text-[10px] text-faint">no nodes in this scene</p>
          )}

          {/* everything outside the scene under the playhead is not in these lanes */}
          <div className="pointer-events-none absolute inset-y-0 right-0 overflow-hidden"
               style={{ left: GUTTER }}>
            <div className="absolute inset-y-0 left-0 bg-panel/60"
                 style={{ width: Math.max(0, sceneL) }} />
            <div className="absolute inset-y-0 bg-panel/60"
                 style={{ left: Math.max(0, sceneR), right: 0 }} />
            {[sceneL, sceneR].map((px, i) => (
              <div key={i} className="absolute inset-y-0 w-px bg-black/[0.10]" style={{ left: px }} />
            ))}
          </div>
        </div>
      </div>

      {/* playhead, clipped to the track so it can never drift off the axis */}
      <div className="pointer-events-none absolute right-0 overflow-hidden"
           style={{ left: GUTTER, top: TRANSPORT_H, bottom: 0 }}>
        <div className="absolute inset-y-0" style={{ left: t * pps - scroll }}>
          <span className="absolute -left-px inset-y-0 w-[1.5px]" style={{ background: ACCENT }} />
          <span className="absolute -left-[5px] top-0 h-[9px] w-[11px] rounded-b-[2px]"
                style={{ background: ACCENT }} />
        </div>
      </div>
    </div>
  )
}

function ModeBtn({ label, title, on, onClick }: {
  label: string; title: string; on: boolean; onClick(): void
}) {
  return (
    <button
      type="button"
      title={title}
      onClick={onClick}
      className={`h-[18px] rounded-[5px] px-1.5 text-[10px] uppercase tracking-[0.10em]
                  transition-colors
                  ${on
                    ? 'inset-control text-ink'
                    : 'text-faint hover:bg-black/[0.05] hover:text-dim'}`}
    >
      {label}
    </button>
  )
}

function StepBtn({ title, onClick, children }: {
  title: string; onClick(): void; children: ReactNode
}) {
  return (
    <button
      type="button"
      title={title}
      onClick={onClick}
      className="grid h-[18px] w-[18px] place-items-center rounded-[5px] text-dim
                 transition-colors hover:bg-black/[0.05] hover:text-ink"
    >
      {children}
    </button>
  )
}

/**
 * One bar in a lane. Diamonds are only drawn when the keys are far enough apart
 * to stay separate, and they are clamped inside the bar; otherwise the bar
 * carries a count, and the tooltip carries the rest.
 */
function BarView({ bar, pps, base, top, scroll, viewW, strong }: {
  bar: Bar; pps: number; base: number; top: number
  scroll: number; viewW: number; strong: boolean
}) {
  const left = (base + bar.t0) * pps
  const raw = (bar.t1 - bar.t0) * pps
  if (left > scroll + viewW + 40 || left + Math.max(raw, 8) < scroll - 40) return null

  // a bar with no length at all is a single key: draw the key, not a sliver
  if (raw < 5) {
    return (
      <span
        title={bar.title}
        className="absolute rotate-45"
        style={{
          left: left - KEY_SIZE / 2, top: top + (BAR_H - KEY_SIZE) / 2,
          width: KEY_SIZE, height: KEY_SIZE,
          background: '#fff', border: `1.25px solid ${bar.color}`,
        }}
      />
    )
  }

  const w = Math.max(3, raw)
  const inner = w - 2
  const half = KEY_SIZE / 2
  const xs = bar.keys.map(k => clamp((k - bar.t0) * pps - 1, KEY_R, inner - KEY_R))
  const spread = xs.every((x, i) => i === 0 || x - xs[i - 1] >= KEY_GAP)
  const drawKeys = xs.length > 0 && spread && inner >= KEY_R * 2

  const labelW = bar.label.length * 5.3 + 8
  let slotLeft = 0
  let slotW = 0
  if (drawKeys) {
    // the label goes in the widest gap between diamonds, if it fits whole
    const edges = [3 - KEY_R, ...xs, inner - 3 + KEY_R]
    for (let i = 1; i < edges.length; i++) {
      const g = edges[i] - KEY_R - (edges[i - 1] + KEY_R) - 6
      if (g > slotW) { slotW = g; slotLeft = edges[i - 1] + KEY_R + 3 }
    }
    if (slotW < labelW) slotW = 0
  }

  // keys too dense to separate: say how many there are instead of piling them up
  const count = !drawKeys && bar.keys.length > 1 && inner >= 16 ? String(bar.keys.length) : ''
  if (!drawKeys) {
    slotLeft = 4
    slotW = inner - 8 - (count ? count.length * 5.3 + 6 : 0)
    if (slotW < 24) slotW = 0
  }

  return (
    <span
      title={bar.title}
      className="absolute block rounded-[3px]"
      style={{
        left, top, width: w, height: BAR_H,
        background: `${bar.color}${strong ? '30' : '1f'}`,
        border: `1px solid ${bar.color}`,
      }}
    >
      {slotW > 0 && (
        <span
          className="absolute top-0 block overflow-hidden text-ellipsis whitespace-nowrap
                     font-mono text-[9px] leading-[11px]"
          style={{ left: slotLeft, width: slotW, color: bar.color }}
        >
          {bar.label}
        </span>
      )}
      {count && (
        <span className="absolute right-[3px] top-0 font-mono text-[9px] leading-[11px]"
              style={{ color: bar.color }}>
          {count}
        </span>
      )}
      {drawKeys && xs.map((x, i) => (
        <span
          key={i}
          className="absolute rotate-45"
          style={{
            left: x - half, top: (BAR_H - 2 - KEY_SIZE) / 2,
            width: KEY_SIZE, height: KEY_SIZE,
            background: '#fff', border: `1.25px solid ${bar.color}`,
          }}
        />
      ))}
    </span>
  )
}
