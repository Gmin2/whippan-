import { useMemo, useState } from 'react'
import NumField from './NumField'
import { TONE, checkDuration, checkTravel } from '../taste'
import type { Note } from '../taste'
import ColorRow from './ColorRow'
import EaseCurve from './motion/EaseCurve'
import {
  MEANING, NAMED, bezierArgs, easeKind, easeLabel, sortKeys, springArgs, valueAt,
} from './motion/ease'
import type { Key } from './motion/ease'
import type { Node } from '../engine/types'

export interface TrackPatch {
  at?: number
  loop?: boolean
  /** replace one property's keys; null removes that property */
  keys?: Record<string, { t: number; v: number; ease?: unknown }[] | null>
  enter?: string | null
  reveal?: Record<string, unknown> | null
  state?: string | null
}

interface RawTrack {
  at?: number
  loop?: boolean
  keys?: Record<string, { t: number; v: number; ease?: unknown }[]>
  reveal?: Record<string, unknown>
  enter?: unknown
  state?: string
}

interface Props {
  node: Node | null
  sceneId: string | null
  /** the raw tracks targeting this node, already filtered for you */
  tracks: RawTrack[]
  /** scene-local playhead time, so the panel can show values AT the playhead */
  localTime: number
  sceneDur: number
  onPatch(patch: TrackPatch): void
}

const ENTERS = ['pop', 'rise-fade', 'drop', 'slide-left', 'slide-right', 'spring-in', 'fade']
const UNITS = ['word', 'glyph', 'type', 'scramble']

interface Meta {
  precision: number
  step: number
  suffix?: string
  min?: number
  max?: number
  /** x and y are offsets from the stage position, everything else is absolute */
  offset?: boolean
  seed(node: Node | null): [number, number]
}

const NUM = (v: unknown, fallback: number) =>
  typeof v === 'number' && Number.isFinite(v) ? v : fallback

const PROPS: Record<string, Meta> = {
  x: { precision: 0, step: 1, suffix: ' px', offset: true, seed: () => [-40, 0] },
  y: { precision: 0, step: 1, suffix: ' px', offset: true, seed: () => [40, 0] },
  w: { precision: 0, step: 1, suffix: ' px', min: 0, seed: n => [Math.round(NUM(n?.w, 200) * 0.8), NUM(n?.w, 200)] },
  h: { precision: 0, step: 1, suffix: ' px', min: 0, seed: n => [Math.round(NUM(n?.h, 200) * 0.8), NUM(n?.h, 200)] },
  scale: { precision: 2, step: 0.01, min: 0, seed: () => [0.92, 1] },
  rot: { precision: 1, step: 0.5, suffix: '°', seed: () => [-6, 0] },
  opacity: { precision: 2, step: 0.02, min: 0, max: 1, seed: () => [0, 1] },
  blur: { precision: 1, step: 0.5, min: 0, seed: () => [8, 0] },
  glow_sigma: { precision: 0, step: 1, min: 0, seed: () => [0, 24] },
  glow_opacity: { precision: 2, step: 0.02, min: 0, max: 1, seed: () => [0, 0.8] },
}

const CAM_PROPS: Record<string, Meta> = {
  cam_x: { precision: 0, step: 1, suffix: ' px', seed: () => [0, 40] },
  cam_y: { precision: 0, step: 1, suffix: ' px', seed: () => [0, 40] },
  cam_zoom: { precision: 3, step: 0.005, min: 0.01, seed: () => [1, 1.08] },
}

/** the band the 29 reference films sit inside */
const SLOW = 0.35
const TRAVEL = 40

function Section({ label, children, right }: {
  label: string
  children: React.ReactNode
  right?: React.ReactNode
}) {
  return (
    <div className="border-b border-hair px-3 py-3">
      <div className="mb-2 flex items-center">
        <p className="font-medium">{label}</p>
        {right && <div className="ml-auto flex items-center gap-1">{right}</div>}
      </div>
      {children}
    </div>
  )
}

const Pair = ({ children }: { children: React.ReactNode }) => (
  <div className="grid grid-cols-2 gap-1.5">{children}</div>
)

function Field({ label, value, note }: { label: string; value: string; note?: Note | null }) {
  const tone = note ? TONE[note.level] : null
  return (
    <div
      title={note?.text}
      className="inset-control flex h-[26px] items-center gap-2 px-2"
      style={tone && note!.level === 'warn'
        ? { borderColor: tone.border, background: tone.tint }
        : undefined}
    >
      <span className="text-faint">{label}</span>
      <span className="ml-auto tabular-nums"
            style={tone && note!.level === 'warn' ? { color: tone.text } : undefined}>
        {value}
      </span>
    </div>
  )
}

/** the reason a band was broken, shown where the number is rather than in a footnote */
function Band({ note }: { note: Note | null }) {
  if (!note) return null
  return (
    <p className="mt-1 text-[10px] leading-relaxed"
       style={{ color: TONE[note.level].text }}>
      {note.text}
    </p>
  )
}

/** the consequence in front, the name it is actually called underneath */
function EaseName({ kind }: { kind: string }) {
  const m = MEANING[kind]
  if (!m) return <>{kind}</>
  return (
    <span className="block leading-[1.15]">
      <span className="block truncate">{m.verb}</span>
      <span className="block truncate font-mono text-[9px] text-faint">{kind}</span>
    </span>
  )
}

function Chip({ on, onClick, children, title, tall }: {
  on: boolean
  onClick(): void
  children: React.ReactNode
  title?: string
  /** two lines of label instead of one */
  tall?: boolean
}) {
  return (
    <button
      onClick={onClick}
      title={title}
      className={`${tall ? 'py-1' : 'h-[24px] truncate'} min-w-0 rounded-[5px] border px-1.5
                  text-[11px] transition-colors
                  ${on
                    ? 'border-[#5e92f4] bg-[#5e92f4]/12 font-medium text-[#2f6ad4]'
                    : 'border-hair bg-surface text-dim hover:text-ink'}`}
    >
      {children}
    </button>
  )
}

function Segmented({ options, value, onPick }: {
  options: string[]
  value: string | null
  onPick(v: string): void
}) {
  return (
    <div className="flex rounded-[6px] bg-black/[0.05] p-[2px]">
      {options.map(o => (
        <button
          key={o}
          onClick={() => onPick(o)}
          className={`h-[22px] min-w-0 flex-1 truncate rounded-[4px] text-[10px] transition-colors
                      ${value === o
                        ? 'bg-surface font-medium shadow-[0_1px_2px_rgba(0,0,0,0.07)]'
                        : 'text-dim hover:text-ink'}`}
        >
          {o}
        </button>
      ))}
    </div>
  )
}

function Toggle({ label, on, onClick }: { label: string; on: boolean; onClick(): void }) {
  return (
    <button
      onClick={onClick}
      className="inset-control flex h-[26px] items-center gap-2 px-2 transition-colors
                 hover:bg-black/[0.02]"
    >
      <span className="text-faint">{label}</span>
      <span className={`ml-auto ${on ? 'font-medium text-[#2f6ad4]' : 'text-dim'}`}>
        {on ? 'on' : 'off'}
      </span>
    </button>
  )
}

const secs = (t: number) => `${t.toFixed(2)}s`
const ms = (t: number) => `${Math.round(t * 1000)}ms`

export default function MotionInspector({
  node, sceneId, tracks, localTime, sceneDur, onPatch,
}: Props) {
  const [selProp, setSelProp] = useState<string | null>(null)
  const [selKey, setSelKey] = useState(1)
  const [adding, setAdding] = useState(false)

  const isScene = !node && !!sceneId
  const table = isScene ? CAM_PROPS : PROPS

  // one track per node per property, and a later track replaces an earlier
  // one, so the panel edits the collapsed view of every track on this target
  const track = useMemo(() => {
    const keys: Record<string, Key[]> = {}
    let at = 0
    let loop = false
    let enter: string | null = null
    let reveal: Record<string, unknown> | null = null
    let state: string | null = null
    const ats = new Set<number>()
    for (const tr of tracks) {
      for (const [prop, ks] of Object.entries(tr.keys ?? {})) {
        if (ks && ks.length) keys[prop] = ks
      }
      ats.add(tr.at ?? 0)
      at = tr.at ?? 0
      if (tr.loop != null) loop = !!tr.loop
      if (tr.enter != null) enter = String(tr.enter)
      if (tr.reveal) reveal = tr.reveal
      if (tr.state != null) state = tr.state
    }
    return { keys, at, loop, enter, reveal, state, split: ats.size > 1 }
  }, [tracks])

  const props = Object.keys(track.keys).filter(p => table[p] || PROPS[p] || CAM_PROPS[p])
  const unknown = Object.keys(track.keys).filter(p => !table[p] && !PROPS[p] && !CAM_PROPS[p])
  const prop = selProp && track.keys[selProp] ? selProp : props[0] ?? null
  const meta = (p: string): Meta => table[p] ?? PROPS[p] ?? CAM_PROPS[p] ?? PROPS.opacity

  const keys = prop ? sortKeys(track.keys[prop]) : []
  const ki = Math.min(Math.max(selKey, 1), Math.max(1, keys.length - 1))
  const key = keys[ki]

  const rel = localTime - track.at
  const fmt = (p: string, v: number) => v.toFixed(meta(p).precision) + (meta(p).suffix ?? '')

  // the whole track's footprint, keys plus whatever the presets imply
  const bounds = useMemo(() => {
    const ts: number[] = []
    for (const ks of Object.values(track.keys)) {
      for (const k of ks) ts.push(k.t)
    }
    if (track.enter) ts.push(0, 0.4)
    if (track.reveal) {
      const dur = NUM(track.reveal.dur, 0.27)
      const stagger = NUM(track.reveal.stagger, 0.05)
      ts.push(0, dur + stagger * 4)
    }
    if (track.state) ts.push(0, 0.12)
    if (!ts.length) return null
    return { in: track.at + Math.min(...ts), out: track.at + Math.max(...ts) }
  }, [track])

  /**
   * How long the move actually takes, and whether that is inside the band.
   *
   * The band is about ONE move, so it is only applied to something shaped like
   * one. Two exemptions, both real cases in the reference films:
   *
   *  - a looped track is a hold, not a move; a two second pulse is the point
   *  - a track with many keys is a path or a follow, not an A to B. the caret
   *    tracking a typewriter runs 3.9s across a dozen keys and is correct
   *
   * Warning on those would be noise, and a check that cries wolf is worse than
   * the paragraph it replaced.
   */
  const span = bounds ? bounds.out - bounds.in : null
  const steps = useMemo(
    () => Math.max(0, ...Object.values(track.keys).map(ks => ks.length)),
    [track.keys])
  const simple = !track.loop && steps <= 3
  const durNote = span == null || !simple ? null : checkDuration(span)

  /** how far an x or y key asks a node to travel, the other band worth catching */
  const travelNote = useMemo(() => {
    let far = 0
    for (const p of ['x', 'y']) {
      for (const k of track.keys[p] ?? []) far = Math.max(far, Math.abs(NUM(k.v, 0)))
    }
    return checkTravel(far)
  }, [track.keys])

  const writeKeys = (p: string, ks: Key[] | null) => onPatch({ keys: { [p]: ks } })

  const patchKey = (i: number, next: Key) => {
    if (!prop) return
    writeKeys(prop, sortKeys(keys.map((k, n) => (n === i ? next : k))))
  }

  const setEase = (ease: unknown) => {
    if (!key) return
    const next: Key = { t: key.t, v: key.v }
    if (ease != null) next.ease = ease
    patchKey(ki, next)
  }

  const addProp = (p: string) => {
    const [a, b] = meta(p).seed(node)
    writeKeys(p, [{ t: 0, v: a }, { t: 0.24, v: b, ease: 'outCubic' }])
    setSelProp(p)
    setSelKey(1)
    setAdding(false)
  }

  const setReveal = (patch: Record<string, unknown>) =>
    onPatch({ reveal: { unit: 'word', ...(track.reveal ?? {}), ...patch } })

  const advisories = useMemo(() => {
    const out: string[] = []
    for (const [p, ks] of Object.entries(track.keys)) {
      if (ks.length < 2) continue
      const ts = ks.map(k => k.t)
      const span = Math.max(...ts) - Math.min(...ts)
      if (span > SLOW) out.push(`${p} runs ${ms(span)}, over the 350ms slow line`)
      if (p === 'x' || p === 'y' || p === 'cam_x' || p === 'cam_y') {
        const vs = ks.map(k => k.v)
        const travel = Math.max(...vs) - Math.min(...vs)
        if (travel > TRAVEL) out.push(`${p} travels ${Math.round(travel)}px, past the ~40px band`)
      }
    }
    if (bounds && sceneDur > 0 && bounds.out > sceneDur + 0.001) {
      out.push(`ends ${ms(bounds.out - sceneDur)} after the scene does`)
    }
    return out
  }, [track, bounds, sceneDur])

  if (!node && !sceneId) {
    return (
      <div className="px-3 py-6">
        <p className="text-dim">Nothing selected</p>
        <p className="mt-1 text-[10px] leading-relaxed text-faint">
          pick a node on the canvas to see the motion on it, or a scene for the camera.
        </p>
      </div>
    )
  }

  const empty = !props.length && !track.enter && !track.reveal && !track.state

  return (
    <>
      <div className="flex items-center gap-2 border-b border-hair px-3 py-2">
        <span className="truncate font-mono text-[11px]">{node?.id ?? sceneId}</span>
        <span className="ml-auto shrink-0 text-faint">
          {isScene ? 'camera' : node?.type}
        </span>
      </div>

      {empty && (
        <div className="border-b border-hair bg-[#5e92f4]/[0.06] px-3 py-2">
          <p className="text-[11px] text-dim">No motion on this {isScene ? 'scene' : 'node'} yet</p>
          <div className="mt-1.5 grid grid-cols-2 gap-1.5">
            {isScene ? (
              <Chip on={false} onClick={() => addProp('cam_zoom')}>Push in</Chip>
            ) : (
              <Chip on={false} onClick={() => onPatch({ enter: 'rise-fade' })}>Rise + fade</Chip>
            )}
            <Chip on={false} onClick={() => addProp(isScene ? 'cam_x' : 'opacity')}>
              {isScene ? 'Pan' : 'Fade in'}
            </Chip>
          </div>
        </div>
      )}

      <Section label="Timing">
        <Pair>
          <NumField
            label="At" value={track.at} precision={2} step={0.02} min={0}
            max={sceneDur || undefined} suffix="s"
            onChange={v => onPatch({ at: Math.round(v * 100) / 100 })}
          />
          <Toggle label="Loop" on={track.loop} onClick={() => onPatch({ loop: !track.loop })} />
        </Pair>
        <div className="mt-1.5">
          <Pair>
            <Field label="In" value={bounds ? secs(bounds.in) : '—'} />
            <Field label="Out" value={bounds ? secs(bounds.out) : '—'} />
          </Pair>
        </div>
        {/* the band that matters most, checked where the number is rather than
            explained in a footnote nobody reads */}
        <div className="mt-1.5">
          <Field
            label="Takes"
            value={span == null ? '—' : `${Math.round(span * 1000)} ms`}
            note={durNote}
          />
        </div>
        <Band note={durNote} />
        <p className="mt-1.5 text-[10px] leading-relaxed text-faint">
          at is scene-local and shifts the whole track; key times are relative to it
          {track.split && ' · these tracks disagree on at, editing folds them onto one'}
        </p>
      </Section>

      <Section
        label="Enter"
        right={track.enter && (
          <button onClick={() => onPatch({ enter: null })}
                  className="text-dim hover:text-ink">−</button>
        )}
      >
        <div className="grid grid-cols-3 gap-1.5">
          {ENTERS.map(e => (
            <Chip key={e} on={track.enter === e}
                  onClick={() => onPatch({ enter: track.enter === e ? null : e })}>
              {e}
            </Chip>
          ))}
        </div>
        <div className="mt-1.5">
          <input
            key={track.state ?? ''}
            defaultValue={track.state ?? ''}
            placeholder="state"
            onBlur={e => {
              const v = e.target.value.trim()
              if (v !== (track.state ?? '')) onPatch({ state: v || null })
            }}
            onKeyDown={e => { if (e.key === 'Enter') (e.target as HTMLInputElement).blur() }}
            className="inset-control h-[26px] w-full px-2 font-mono text-[11px] outline-none
                       placeholder:font-sans placeholder:text-faint
                       focus:border-[#2d52f0] focus:ring-2 focus:ring-[#2d52f0]/25"
          />
        </div>
      </Section>

      {node?.type === 'text' && (
        <Section
          label="Reveal"
          right={track.reveal && (
            <button onClick={() => onPatch({ reveal: null })}
                    className="text-dim hover:text-ink">−</button>
          )}
        >
          <Segmented
            options={UNITS}
            value={track.reveal ? String(track.reveal.unit ?? 'word') : null}
            onPick={u => setReveal({ unit: u })}
          />
          {track.reveal && (() => {
            const r = track.reveal
            const unit = String(r.unit ?? 'word')
            return (
              <div className="mt-1.5 flex flex-col gap-1.5">
                {(unit === 'word' || unit === 'glyph') && (
                  <>
                    <Pair>
                      <NumField label="Stag" value={NUM(r.stagger, 0.05)} precision={3}
                                step={0.005} min={0}
                                onChange={v => setReveal({ stagger: v })} />
                      <NumField label="Dur" value={NUM(r.dur, 0.27)} precision={2}
                                step={0.01} min={0}
                                onChange={v => setReveal({ dur: v })} />
                    </Pair>
                    <NumField label="Rise" value={NUM(r.rise, 40)} step={1} suffix=" px"
                              onChange={v => setReveal({ rise: Math.round(v) })} />
                  </>
                )}
                {unit === 'type' && (
                  <>
                    <Pair>
                      <NumField label="Cad" value={NUM(r.cadence, 0.04)} precision={3}
                                step={0.005} min={0}
                                onChange={v => setReveal({ cadence: v })} />
                      <NumField label="End" value={NUM(r.cadence_end, NUM(r.cadence, 0.04))}
                                precision={3} step={0.005} min={0}
                                onChange={v => setReveal({ cadence_end: v })} />
                    </Pair>
                    <Segmented
                      options={['bar', 'block', 'none']}
                      value={String(r.caret ?? 'bar')}
                      onPick={c => setReveal({ caret: c })}
                    />
                    <Toggle label="Caret blink" on={r.caret_blink !== false}
                            onClick={() => setReveal({ caret_blink: r.caret_blink === false })} />
                  </>
                )}
                {unit === 'scramble' && (
                  <Pair>
                    <NumField label="Cad" value={NUM(r.cadence, 0.04)} precision={3}
                              step={0.005} min={0}
                              onChange={v => setReveal({ cadence: v })} />
                    <NumField label="Churn" value={NUM(r.churn, 3)} precision={0} step={1} min={1}
                              onChange={v => setReveal({ churn: Math.round(v) })} />
                  </Pair>
                )}
                <ColorRow
                  hex={typeof r.accent === 'string' ? r.accent : '#e8671f'}
                  alpha={1}
                  onChange={hex => setReveal({ accent: hex })}
                />
                <input
                  key={String(r.keep ?? '')}
                  defaultValue={Array.isArray(r.keep) ? r.keep.join(', ') : ''}
                  placeholder="accent these words"
                  onBlur={e => {
                    const list = e.target.value.split(',').map(s => s.trim()).filter(Boolean)
                    setReveal({ keep: list.length ? list : undefined })
                  }}
                  onKeyDown={e => { if (e.key === 'Enter') (e.target as HTMLInputElement).blur() }}
                  className="inset-control h-[26px] w-full px-2 text-[11px] outline-none
                             placeholder:text-faint
                             focus:border-[#2d52f0] focus:ring-2 focus:ring-[#2d52f0]/25"
                />
              </div>
            )
          })()}
          {!track.reveal && (
            <p className="mt-1.5 text-[10px] text-faint">
              a reveal splits the line and staggers the pieces in
            </p>
          )}
        </Section>
      )}

      <Section
        label="Properties"
        right={
          <button onClick={() => setAdding(a => !a)}
                  className="text-dim hover:text-ink">{adding ? '×' : '+'}</button>
        }
      >
        <Band note={travelNote} />
        {adding && (
          <div className="mb-2 grid grid-cols-2 gap-1.5 rounded-[6px] bg-black/[0.03] p-1.5">
            {Object.keys(table).filter(p => !track.keys[p]).map(p => (
              <Chip key={p} on={false} onClick={() => addProp(p)}>
                <span className="font-mono text-[10px]">{p}</span>
              </Chip>
            ))}
            {Object.keys(table).every(p => track.keys[p]) && (
              <p className="col-span-2 text-[10px] text-faint">every property is keyed</p>
            )}
          </div>
        )}

        {props.length ? (
          <div className="flex flex-col gap-px">
            {props.map(p => {
              const ks = sortKeys(track.keys[p])
              const ts = ks.map(k => k.t)
              const span = Math.max(...ts) - Math.min(...ts)
              const live = rel >= Math.min(...ts) && rel <= Math.max(...ts)
              return (
                <div key={p}
                     className={`flex items-start rounded-[5px] transition-colors
                                 ${p === prop ? 'bg-row' : 'hover:bg-black/[0.03]'}`}>
                  <button
                    onClick={() => { setSelProp(p); setSelKey(1) }}
                    className="min-w-0 flex-1 px-1.5 py-1 text-left"
                  >
                    <div className="flex items-baseline gap-2">
                      <span className="truncate font-mono text-[11px]">{p}</span>
                      <span className={`ml-auto shrink-0 font-mono tabular-nums
                                        ${live ? 'text-[#2f6ad4]' : ''}`}>
                        {fmt(p, valueAt(ks, rel))}
                      </span>
                    </div>
                    <div className="mt-0.5 flex items-baseline gap-2 text-[10px] text-faint">
                      <span>{ks.length} keys</span>
                      <span className="truncate tabular-nums">
                        {/* first → last, not min → max: for an animator the
                            direction is the point. a rise-in reads 34 → 0. */}
                        {fmt(p, ks[0].v)} → {fmt(p, ks[ks.length - 1].v)}
                      </span>
                      <span className="ml-auto shrink-0 tabular-nums">{ms(span)}</span>
                    </div>
                  </button>
                  <button
                    onClick={() => writeKeys(p, null)}
                    title={`remove ${p}`}
                    className="px-1.5 py-1 text-faint hover:text-ink"
                  >
                    −
                  </button>
                </div>
              )
            })}
          </div>
        ) : (
          <p className="text-[10px] text-faint">no keyed properties · + adds one</p>
        )}

        {unknown.length > 0 && (
          <p className="mt-1.5 text-[10px] text-faint">
            also keyed, not editable here: {unknown.join(', ')}
          </p>
        )}
        <p className="mt-1.5 text-[10px] leading-relaxed text-faint">
          {isScene
            ? 'camera keys move the frame, not the nodes'
            : 'x and y are offsets from the stage position; the rest are absolute'}
        </p>
      </Section>

      <Section
        label="Easing"
        right={prop && <span className="font-mono text-[10px] text-faint">{prop}</span>}
      >
        {prop && key ? (
          <>
            <div className="mb-1.5 flex items-center gap-1">
              <span className="text-faint">Key</span>
              <button
                onClick={() => setSelKey(Math.max(1, ki - 1))}
                disabled={ki <= 1}
                className="px-1 text-dim hover:text-ink disabled:text-faint/40"
              >‹</button>
              <span className="tabular-nums">{ki + 1}/{keys.length}</span>
              <button
                onClick={() => setSelKey(Math.min(keys.length - 1, ki + 1))}
                disabled={ki >= keys.length - 1}
                className="px-1 text-dim hover:text-ink disabled:text-faint/40"
              >›</button>
              <span className="ml-auto truncate font-mono text-[10px] text-dim">
                {easeLabel(key.ease)}
              </span>
            </div>

            <EaseCurve
              ease={key.ease}
              progress={(() => {
                const a = keys[ki - 1]
                const w = key.t - a.t
                if (w <= 0) return null
                const p = (rel - a.t) / w
                return p < -0.02 || p > 1.02 ? null : p
              })()}
            />

            <div className="mt-1.5 grid grid-cols-3 gap-1.5">
              {NAMED.map(e => (
                <Chip key={e} tall on={easeKind(key.ease) === e} title={MEANING[e]?.hint}
                      onClick={() => setEase(e === 'linear' ? null : e === 'spring'
                        ? { spring: springArgs(key.ease) } : e)}>
                  <EaseName kind={e} />
                </Chip>
              ))}
              <Chip tall on={easeKind(key.ease) === 'bezier'} title={MEANING.bezier.hint}
                    onClick={() => setEase(bezierArgs(key.ease) as unknown)}>
                <EaseName kind="bezier" />
              </Chip>
            </div>

            {easeKind(key.ease) === 'bezier' && (
              <div className="mt-1.5 grid grid-cols-4 gap-1">
                {bezierArgs(key.ease).map((n, i) => (
                  <NumField
                    key={i} value={n} precision={2} step={0.01}
                    onChange={v => {
                      const next = bezierArgs(key.ease).slice() as number[]
                      next[i] = Math.round(v * 100) / 100
                      setEase(next)
                    }}
                  />
                ))}
              </div>
            )}

            {easeKind(key.ease) === 'spring' && (
              <div className="mt-1.5">
                <Pair>
                  <NumField label="Damp" value={springArgs(key.ease)[0]} precision={1}
                            step={0.5} min={0.5}
                            onChange={v => setEase({ spring: [v, springArgs(key.ease)[1]] })} />
                  <NumField label="Cyc" value={springArgs(key.ease)[1]} precision={2}
                            step={0.05} min={0}
                            onChange={v => setEase({ spring: [springArgs(key.ease)[0], v] })} />
                </Pair>
              </div>
            )}

            <div className="mt-1.5">
              <Pair>
                <NumField label="t" value={key.t} precision={2} step={0.01} min={0} suffix="s"
                          onChange={v => patchKey(ki, { ...key, t: Math.round(v * 100) / 100 })} />
                <NumField label="v" value={key.v} precision={meta(prop).precision}
                          step={meta(prop).step} min={meta(prop).min} max={meta(prop).max}
                          onChange={v => patchKey(ki, { ...key, v })} />
              </Pair>
            </div>
            <p className="mt-1.5 text-[10px] leading-relaxed text-faint">
              an ease belongs to the key it lands on · no ease is linear
            </p>
          </>
        ) : (
          <p className="text-[10px] text-faint">
            {prop ? 'one key holds a constant, add a second to ease between them'
                  : 'select a property to shape its curve'}
          </p>
        )}
      </Section>

      <div className="px-3 py-3">
        {advisories.map(a => (
          <p key={a} className="mb-1 flex gap-1.5 text-[10px] leading-relaxed text-dim">
            <span className="mt-[3px] h-1 w-1 shrink-0 rounded-full bg-[#e8671f]" />
            {a}
          </p>
        ))}
        <p className="text-[10px] leading-relaxed text-faint">
          the bands above are measured off 29 launch films. they flag as you type
          rather than asking you to remember them: entrances ease out 200–280ms
          after ~80ms, exits ease in ~150ms, siblings 40–80ms apart.
        </p>
      </div>
    </>
  )
}
