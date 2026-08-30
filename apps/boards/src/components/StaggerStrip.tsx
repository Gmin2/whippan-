import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { spanColor } from '../motion'
import type { Lane, Span } from '../motion'

interface Props {
  lanes: Lane[]
  /** scene duration in seconds; the strip's full width */
  dur: number
  /** scene-local playhead, or null when the playhead is in another scene */
  playhead: number | null
  /** width in px the strip must fit into */
  width: number
  selected: string | null
  onSelect(target: string): void
  /** restagger: shift this node's track by delta seconds. `done` ends the gesture */
  onShift(target: string, at: number, done: boolean): void
  /** the document's frame rate, which is the grid a drag snaps to */
  fps?: number
  /** collapsed to the header alone; one flag for every strip on the wall */
  collapsed?: boolean
  onCollapse?(next: boolean): void
}

/** the stage default, used when the caller does not say */
const FPS = 30
const ACCENT = '#5e92f4'
const ROW_H = 13
const BAR_H = 8
const HEAD_H = 15
const FOOT_H = 12
const GUTTER = 92
const PAD = 5
/** below this the node ids stop fitting next to a usable track */
const LABEL_MIN = 215
/** below this even one bar per row is too short to aim at */
const BARS_MIN = 118
const SUMMARY_H = 15
/** room the "even 0.06s" caption needs, so it can flip sides near the edge */
const CAP_W = 58
/** the stagger the 29 measured launch films sit inside, quoted, never enforced */
const HOUSE_LO = 0.04
const HOUSE_HI = 0.08

type Mode = 'full' | 'bars' | 'summary'

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v))

/** the loudest thing a node does decides its colour, same order the dock uses */
const KIND_ORDER: Span['kind'][] = ['cam', 'reveal', 'state', 'enter', 'keys']

interface Row {
  target: string
  kind: string
  /** scene-local seconds of the node's first motion */
  entry: number
  end: number
  /** the `at` a restagger moves, taken from the span that enters first */
  at: number
  color: string
  index: number
}

interface Drag {
  target: string
  startX: number
  startAt: number
  /** live value, for the readout while the gesture runs */
  at: number
}

function rowOf(lane: Lane, index: number): Row | null {
  if (!lane.spans.length) return null
  let first = lane.spans[0]
  let end = -Infinity
  for (const s of lane.spans) {
    if (s.t0 < first.t0) first = s
    end = Math.max(end, s.t1)
  }
  const kind = KIND_ORDER.find(k => lane.spans.some(s => s.kind === k)) ?? 'keys'
  return {
    target: lane.target,
    kind: lane.kind,
    entry: first.t0,
    end,
    at: first.at,
    color: spanColor(kind),
    index,
  }
}

const round4 = (v: number) => Math.round(v * 1e4) / 1e4

/**
 * A scene's whole beat in one glance: one short lane per node, placed where it
 * enters within the scene's own 0 → dur. The ladder down the left of the track
 * joins consecutive entries, so an uneven staircase shows up as a kink rather
 * than as numbers you have to compare.
 *
 * Dragging a bar rewrites the node's track `at`, which is what "restagger"
 * means in the document: `at` shifts the whole track and key times are stored
 * relative to it.
 */
export default function StaggerStrip({
  lanes, dur, playhead, width, selected, onSelect, onShift, fps, collapsed, onCollapse,
}: Props) {
  const [drag, setDrag] = useState<Drag | null>(null)
  /** pointer is over the strip, which is what offers the even ladder */
  const [hint, setHint] = useState(false)
  /** pointer is on the even ladder itself, so it can outshout the real one */
  const [aim, setAim] = useState(false)
  /**
   * The live gesture, held in a ref as well as in state. `onShift` is a side
   * effect and must not be called from inside a setState updater, where React
   * makes no promise about when or how often the function runs — which also
   * breaks cancelling the drag.
   */
  const gesture = useRef<Drag | null>(null)
  const cancelled = useRef(false)
  /** row order captured at drag start, so rows do not reshuffle under the pointer */
  const [frozen, setFrozen] = useState<string[] | null>(null)

  const mode: Mode = width >= LABEL_MIN ? 'full' : width >= BARS_MIN ? 'bars' : 'summary'
  const span = Math.max(dur, 0.001)

  const rows = useMemo(() => {
    const out: Row[] = []
    lanes.forEach((l, i) => {
      const r = rowOf(l, i)
      if (r) out.push(r)
    })
    out.sort((a, b) => a.entry - b.entry || a.index - b.index)
    return out
  }, [lanes])

  const staticCount = lanes.length - rows.length

  const ordered = useMemo(() => {
    if (!frozen) return rows
    const rank = new Map(frozen.map((t, i) => [t, i]))
    return [...rows].sort(
      (a, b) => (rank.get(a.target) ?? rows.length) - (rank.get(b.target) ?? rows.length),
    )
  }, [rows, frozen])

  /** gap to the previous entry, keyed by node, always in entry order */
  const gaps = useMemo(() => {
    const m = new Map<string, number>()
    for (let i = 1; i < rows.length; i++) m.set(rows[i].target, rows[i].entry - rows[i - 1].entry)
    return m
  }, [rows])

  const beat = useMemo(() => {
    const vs = [...gaps.values()]
    if (!vs.length) return null
    const lo = Math.min(...vs)
    const hi = Math.max(...vs)
    return { lo, hi, even: hi - lo < 0.008 }
  }, [gaps])

  /**
   * The ladder this scene would have with an even stagger: the first and last
   * entries stay, everything between them is respaced. The two ends fix the
   * gap, so the even shape has no free parameter — which is why it can be
   * drawn ahead of time and simply taken, rather than dialled in.
   */
  const straight = useMemo(() => {
    if (rows.length < 3 || !beat || beat.even) return null
    const first = rows[0].entry
    const step = (rows[rows.length - 1].entry - first) / (rows.length - 1)
    if (step <= 0) return null
    const grid = fps ?? FPS
    // the two ends are held out of the loop rather than filtered afterwards,
    // so no rounding can nudge them. what moves is `at`, snapped to the frame
    // grid the way a drag snaps it, and the row's entry follows it
    const entries = rows.map(r => r.entry)
    const moves: { target: string; at: number }[] = []
    for (let i = 1; i < rows.length - 1; i++) {
      const r = rows[i]
      const want = r.at + (first + step * i - r.entry)
      const at = round4(Math.max(0, Math.round(want * grid) / grid))
      // the document keeps `at` to the millisecond, so a move it could not
      // record is not a move. that is also what retires the offer: once every
      // row is as close to even as the frame grid allows, there is nothing
      // left to hand over and the ladder stops being drawn
      if (Math.abs(at - r.at) < 0.001) continue
      entries[i] = round4(r.entry + (at - r.at))
      moves.push({ target: r.target, at })
    }
    return moves.length ? { gap: step, entries, moves } : null
  }, [rows, beat, fps])

  /**
   * One press is one undo: the parent snapshots on the first `onShift` of a
   * gesture and closes it on `done`, so every row goes out in one run with the
   * flag on the last. Read straight from the memo — never from inside a
   * setState updater, which is free to run twice.
   */
  const straighten = useCallback(() => {
    if (!straight) return
    straight.moves.forEach((m, i) => onShift(m.target, m.at, i === straight.moves.length - 1))
    setAim(false)
  }, [straight, onShift])

  const trackW = Math.max(
    24,
    width - PAD * 2 - (mode === 'full' ? GUTTER : 0),
  )
  const pps = trackW / span

  const applyDrag = useCallback((clientX: number, done: boolean) => {
    const d = gesture.current
    if (!d || cancelled.current) return
    const delta = (clientX - d.startX) / pps
    // the document is frame based, so a time between frames is one the renderer
    // can never show; 4/30 also repeats, hence the round
    const grid = fps ?? FPS
    const at = round4(Math.max(0, Math.round((d.startAt + delta) * grid) / grid))
    onShift(d.target, at, done)
    d.at = at
    setDrag({ ...d })
  }, [pps, onShift, fps])

  useEffect(() => {
    gesture.current = drag
    if (!drag) return
    const start = drag
    const move = (e: PointerEvent) => applyDrag(e.clientX, false)
    const up = (e: PointerEvent) => {
      applyDrag(e.clientX, true)
      gesture.current = null
      setDrag(null)
      setFrozen(null)
    }
    const key = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return
      e.stopPropagation()
      e.preventDefault()
      cancelled.current = true
      // put the track back where it was, then end the gesture
      onShift(start.target, start.startAt, true)
      gesture.current = null
      setDrag(null)
      setFrozen(null)
    }
    cancelled.current = false
    window.addEventListener('pointermove', move)
    window.addEventListener('pointerup', up)
    // capture phase, so escape lands here before the app clears the selection
    window.addEventListener('keydown', key, true)
    return () => {
      window.removeEventListener('pointermove', move)
      window.removeEventListener('pointerup', up)
      window.removeEventListener('keydown', key, true)
    }
  }, [drag, applyDrag, onShift])

  const grab = useCallback((e: React.PointerEvent, r: Row) => {
    e.preventDefault()
    e.stopPropagation()
    onSelect(r.target)
    setFrozen(ordered.map(o => o.target))
    setDrag({ target: r.target, startX: e.clientX, startAt: r.at, at: r.at })
  }, [onSelect, ordered])

  // the narrowest mode has no room for the words, only for the numbers. the
  // word is what degrades: the number is the thing worth reading, so it stays
  // at every width
  const tight = mode === 'summary'
  const lead = mode === 'full' ? 'stagger ' : tight ? 'Δ' : 'Δ '
  const headRight = drag
    ? `${drag.at.toFixed(2)}s`
    : beat
      ? beat.even
        ? `${lead}${beat.lo.toFixed(2)}s`
        : `${lead}${beat.lo.toFixed(2)}–${beat.hi.toFixed(2)}s`
      : null

  const head = (
    <div
      onPointerDown={onCollapse ? e => { e.stopPropagation(); onCollapse(!collapsed) } : undefined}
      title={onCollapse
        ? (collapsed ? 'show the lanes' : 'collapse the strips')
        : undefined}
      className={`flex items-baseline gap-1.5 px-[5px]
                  ${onCollapse ? 'cursor-pointer hover:bg-black/[0.035]' : ''}`}
      style={{ height: HEAD_H }}
    >
      {onCollapse && (
        <span className={`shrink-0 self-center text-faint transition-transform
                          ${collapsed ? '-rotate-90' : ''}`}>
          <svg width="7" height="7" viewBox="0 0 10 10" fill="none" stroke="currentColor"
               strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
            <path d="M2 3.75 5 6.5l3-2.75" />
          </svg>
        </span>
      )}
      <span className="shrink-0 font-mono text-[9px] tabular-nums text-faint"
            title={`${rows.length} node${rows.length === 1 ? '' : 's'} with motion`}>
        {rows.length}
        {!tight && <span className="ml-1">{rows.length === 1 ? 'node' : 'nodes'}</span>}
      </span>
      {mode === 'full' && staticCount > 0 && (
        <span className="truncate font-mono text-[9px] tabular-nums text-faint/70">
          +{staticCount} static
        </span>
      )}
      {headRight && (
        <span
          className="ml-auto shrink-0 font-mono text-[9px] tabular-nums"
          style={{ color: drag ? ACCENT : undefined }}
          title={drag
            ? 'entry while dragging'
            : 'stagger: the gap between one node entering and the next'
              + `  ·  the house style is ${HOUSE_LO.toFixed(2)}–${HOUSE_HI.toFixed(2)}s`}
        >
          {headRight}
        </span>
      )}
    </div>
  )

  if (collapsed) {
    return (
      <div className="border-t border-hair bg-panel" style={{ width }}>{head}</div>
    )
  }

  if (!rows.length) {
    return (
      <div className="border-t border-hair bg-panel" style={{ width }}>
        <div className="flex items-center px-[5px]" style={{ height: HEAD_H }}>
          <span className="truncate font-mono text-[9px] text-faint">
            {lanes.length ? `${lanes.length} static` : 'no motion'}
          </span>
        </div>
      </div>
    )
  }

  // too narrow for rows: one lane, one tick per entry, colours kept
  if (mode === 'summary') {
    return (
      <div className="border-t border-hair bg-panel" style={{ width }}>
        {head}
        <div className="px-[5px] pb-[4px]">
          <div className="relative overflow-hidden rounded-[2px] bg-row/60"
               style={{ height: SUMMARY_H, width: trackW }}>
            {ordered.map(r => (
              <span
                key={r.target}
                title={`${r.target}  enters ${r.entry.toFixed(2)}s`}
                className="absolute top-[2px] bottom-[2px] w-[2px] rounded-[1px]"
                style={{
                  left: clamp(r.entry * pps, 0, trackW - 2),
                  background: r.color,
                  opacity: selected === r.target ? 1 : 0.55,
                }}
              />
            ))}
            {playhead !== null && (
              <span className="absolute inset-y-0 w-px"
                    style={{ left: clamp(playhead * pps, 0, trackW - 1), background: ACCENT }} />
            )}
          </div>
        </div>
      </div>
    )
  }

  const labels = mode === 'full'
  const dot = (t: number) => clamp(t * pps, 0.5, trackW - 0.5)
  const ladder = ordered
    .map((r, i) => `${dot(r.entry)},${i * ROW_H + ROW_H / 2}`)
    .join(' ')

  /**
   * The offer: the even ladder drawn where it would land, captioned with the
   * gap it would produce. Hidden until the pointer is over the strip, so an
   * untouched wall of strips looks exactly as it did.
   */
  const offer = straight && !drag
    ? (() => {
      const mid = Math.floor((straight.entries.length - 1) / 2)
      const x = dot(straight.entries[mid])
      const flip = x + CAP_W > trackW
      const off = straight.gap < HOUSE_LO - 1e-6 || straight.gap > HOUSE_HI + 1e-6
      return {
        pts: straight.entries.map((e, i) => `${dot(e)},${i * ROW_H + ROW_H / 2}`).join(' '),
        x, flip,
        y: mid * ROW_H + ROW_H / 2,
        label: `even ${straight.gap.toFixed(2)}s`,
        tip: `even the stagger to ${straight.gap.toFixed(2)}s`
          + (off ? `  ·  the house style is ${HOUSE_LO.toFixed(2)}–${HOUSE_HI.toFixed(2)}s` : ''),
      }
    })()
    : null

  return (
    <div className="select-none border-t border-hair bg-panel" style={{ width }}>
      {head}
      <div
        className="relative px-[5px]"
        onPointerEnter={() => setHint(true)}
        onPointerLeave={() => { setHint(false); setAim(false) }}
      >
        {/* the ladder joins entries in order; a kink is an uneven stagger */}
        <svg
          className="pointer-events-none absolute"
          style={{ left: PAD + (labels ? GUTTER : 0), top: 0, width: trackW, height: ordered.length * ROW_H }}
          width={trackW}
          height={ordered.length * ROW_H}
          aria-hidden
        >
          <polyline points={ladder} fill="none" strokeWidth="1"
                    stroke={aim ? 'rgba(0,0,0,0.07)' : 'rgba(0,0,0,0.14)'} />
          {/* the even ladder takes the pointer from down here, under the rows,
              so a bar always wins where the two overlap and no one straightens
              a scene while reaching for a drag */}
          {offer && (
            <g
              className="cursor-pointer"
              style={{ pointerEvents: hint ? undefined : 'none' }}
              onPointerEnter={() => setAim(true)}
              onPointerLeave={() => setAim(false)}
              onPointerDown={e => { e.preventDefault(); e.stopPropagation(); straighten() }}
            >
              <title>{offer.tip}</title>
              {/* a fat invisible stroke, because a 1px dashed line is not a target */}
              <polyline points={offer.pts} fill="none" stroke="rgba(0,0,0,0)" strokeWidth="11"
                        style={{ pointerEvents: 'stroke' }} />
              <rect x={offer.flip ? offer.x - 6 - CAP_W : offer.x + 6} y={offer.y - 6}
                    width={CAP_W} height={12} fill="rgba(0,0,0,0)"
                    style={{ pointerEvents: 'all' }} />
            </g>
          )}
        </svg>

        {ordered.map(r => {
          const on = selected === r.target
          const dragging = drag?.target === r.target
          const left = r.entry * pps
          const w = Math.max(3, (r.end - r.entry) * pps)
          const gap = gaps.get(r.target)
          return (
            <div
              key={r.target}
              onPointerDown={() => onSelect(r.target)}
              className={`relative flex items-center ${on ? '' : 'hover:bg-black/[0.035]'}`}
              style={{ height: ROW_H, background: on ? `${ACCENT}1a` : undefined }}
            >
              {on && (
                <span className="absolute inset-y-0 -left-[5px] w-[2px]" style={{ background: ACCENT }} />
              )}
              {labels && (
                <span className="flex shrink-0 items-baseline gap-1 pr-1.5" style={{ width: GUTTER }}>
                  <span className={`min-w-0 flex-1 truncate text-[10px] leading-[13px]
                                    ${on ? 'text-ink' : 'text-dim'}`}
                        title={`${r.target}  (${r.kind})`}>
                    {r.target}
                  </span>
                  <span className="shrink-0 font-mono text-[9px] leading-[13px] tabular-nums text-faint"
                        title={gap === undefined
                          ? 'first entry in the scene'
                          : 'gap to the previous entry'}>
                    {gap === undefined ? r.entry.toFixed(2) : `+${gap.toFixed(2)}`}
                  </span>
                </span>
              )}

              <span className="relative block overflow-hidden" style={{ width: trackW, height: ROW_H }}>
                <span className="absolute left-0 right-0 rounded-[1px] bg-row/50"
                      style={{ top: (ROW_H - 1) / 2, height: 1 }} />
                {/* a full-row wrapper so an 8px bar is still an easy target */}
                <span
                  onPointerDown={e => grab(e, r)}
                  title={`${r.target}  enters ${r.entry.toFixed(2)}s`
                    + `  ·  ${r.entry.toFixed(2)}–${r.end.toFixed(2)}s`
                    + '  ·  drag to restagger'}
                  className="absolute top-0 cursor-ew-resize"
                  style={{ left: clamp(left, 0, Math.max(0, trackW - 3)), width: w, height: ROW_H }}
                >
                  <span
                    className="absolute block rounded-[2px]"
                    style={{
                      top: (ROW_H - BAR_H) / 2, left: 0, width: '100%', height: BAR_H,
                      background: `${r.color}${on || dragging ? '38' : '20'}`,
                      border: `1px solid ${r.color}`,
                      opacity: dragging ? 1 : 0.9,
                    }}
                  />
                  {/* the entry edge, which is the thing being dragged */}
                  <span className="absolute left-0 rounded-[1px]"
                        style={{ top: (ROW_H - BAR_H) / 2 - 1, height: BAR_H + 2, width: 2, background: r.color }} />
                </span>
              </span>
            </div>
          )
        })}

        {/* the straight ladder, offered on top of the bars so it can be taken
            by pointing at it. one press, and the kink is gone */}
        {offer && (
          <svg
            className="absolute z-10"
            style={{
              left: PAD + (labels ? GUTTER : 0),
              top: 0,
              opacity: hint ? 1 : 0,
              pointerEvents: hint ? undefined : 'none',
              transition: 'opacity 120ms ease',
            }}
            width={trackW}
            height={ordered.length * ROW_H}
          >
            <polyline points={offer.pts} fill="none" stroke={ACCENT} strokeWidth="1"
                      strokeDasharray="3 3" opacity={aim ? 1 : 0.6}
                      className="pointer-events-none" />
            <g
              className="cursor-pointer"
              onPointerEnter={() => setAim(true)}
              onPointerLeave={() => setAim(false)}
              onPointerDown={e => { e.preventDefault(); e.stopPropagation(); straighten() }}
            >
              <title>{offer.tip}</title>
              {/* a fat invisible stroke, because a 1px dashed line is not a target */}
              <polyline points={offer.pts} fill="none" stroke="rgba(0,0,0,0)" strokeWidth="11"
                        style={{ pointerEvents: 'stroke' }} />
              <rect x={offer.flip ? offer.x - 6 - CAP_W : offer.x + 6} y={offer.y - 6}
                    width={CAP_W} height={12} fill="rgba(0,0,0,0)" />
              <text
                x={offer.flip ? offer.x - 6 : offer.x + 6}
                y={offer.y + 3}
                textAnchor={offer.flip ? 'end' : 'start'}
                className="pointer-events-none font-mono tabular-nums"
                fontSize="9"
                fill={ACCENT}
                fillOpacity={aim ? 1 : 0.75}
                stroke="#f2f2f2"
                strokeWidth="3"
                paintOrder="stroke"
              >
                {offer.label}
              </text>
            </g>
          </svg>
        )}

        {playhead !== null && (
          <span
            className="pointer-events-none absolute z-20 w-px"
            style={{
              left: PAD + (labels ? GUTTER : 0) + clamp(playhead * pps, 0, trackW - 1),
              top: 0,
              height: ordered.length * ROW_H,
              background: ACCENT,
            }}
          />
        )}
      </div>

      <div className="flex items-center gap-1.5 px-[5px]" style={{ height: FOOT_H }}>
        <span className="font-mono text-[9px] leading-[12px] tabular-nums text-faint/80">0.00</span>
        {!labels && staticCount > 0 && (
          <span className="truncate font-mono text-[9px] leading-[12px] text-faint/70">
            +{staticCount} static
          </span>
        )}
        <span className="ml-auto font-mono text-[9px] leading-[12px] tabular-nums text-faint/80">
          {dur.toFixed(2)}s
        </span>
      </div>
    </div>
  )
}
