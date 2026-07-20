// the timeline narrates the canvas: a playhead pinned at a fixed screen x
// with the ruler and clips scrolling underneath it (radio-main's signature),
// layer pills that light accent-blue exactly while their scene is on canvas,
// an orange keyframe lane with diamond markers, and a green audio lane.
import { useMemo, useRef } from 'react'
import { timing } from './engine.js'

const ACCENT = '#606de0'
const PX_PER_S = 130
const PIN_X = 260
const ROW_H = 26

export default function Timeline({ doc, t, selection, onScrub, onSelect }) {
  const { dur, scenes } = useMemo(() => timing(doc.stage), [doc])
  const areaRef = useRef(null)

  // camera-follow: once the playhead would pass the pin, scroll content
  const scroll = Math.max(0, t * PX_PER_S - PIN_X)
  const playheadX = Math.min(PIN_X, t * PX_PER_S)

  const rows = useMemo(() => {
    const out = []
    for (const sc of scenes)
      for (const n of sc.nodes)
        out.push({ scene: sc, node: n })
    return out
  }, [scenes])

  const keyMarks = useMemo(() => {
    const marks = []
    const starts = Object.fromEntries(scenes.map(s => [s.id, s.start]))
    for (const tr of doc.anim.tracks ?? []) {
      const sc = scenes.find(s => s.nodes.some(n => n.id === tr.target)
        || s.id === tr.target)
      if (!sc) continue
      const base = starts[sc.id] + (tr.at ?? 0)
      for (const keys of Object.values(tr.keys ?? {}))
        for (const k of keys) marks.push(base + k.t)
      if (tr.reveal) marks.push(base)
    }
    return [...new Set(marks.map(m => Math.round(m * 60) / 60))]
  }, [doc, scenes])

  const wave = useMemo(() => {
    // deterministic pseudo-waveform; a real one would sample the bed
    const bars = []
    for (let i = 0; i < dur * 20; i++) {
      const v = Math.abs(Math.sin(i * 1.7) * 0.6 + Math.sin(i * 0.43) * 0.4)
      bars.push(4 + v * 12)
    }
    return bars
  }, [dur])

  function scrubTo(ev) {
    const r = areaRef.current.getBoundingClientRect()
    const x = ev.clientX - r.left + scroll
    onScrub(Math.max(0, Math.min(dur, x / PX_PER_S)))
  }

  const contentW = dur * PX_PER_S + 400

  return (
    <div style={{
      height: 250, background: '#111111', borderTop: '1px solid #222',
      display: 'flex', flexDirection: 'column', position: 'relative',
      overflow: 'hidden',
    }}>
      <div
        ref={areaRef}
        style={{ flex: 1, position: 'relative', overflow: 'hidden', cursor: 'ew-resize' }}
        onMouseDown={ev => {
          scrubTo(ev)
          const move = e => scrubTo(e)
          const up = () => {
            removeEventListener('mousemove', move)
            removeEventListener('mouseup', up)
          }
          addEventListener('mousemove', move)
          addEventListener('mouseup', up)
        }}
      >
        <div style={{
          position: 'absolute', inset: 0, width: contentW,
          transform: `translateX(${-scroll}px)`,
        }}>
          <Ruler dur={dur} />
          <div style={{ position: 'absolute', top: 24, left: 0, right: 0 }}>
            {rows.slice(0, 6).map(({ scene, node }, i) => (
              <Clip key={scene.id + node.id} scene={scene} node={node} row={i}
                    t={t} selection={selection} onSelect={onSelect} />
            ))}
            <div style={{ position: 'absolute', top: 6 * ROW_H + 4, left: 0 }}>
              <KeyLane marks={keyMarks} />
            </div>
            <div style={{ position: 'absolute', top: 6 * ROW_H + 26, left: 0,
                          display: 'flex', alignItems: 'center', gap: 1, height: 20 }}>
              {wave.map((h, i) => (
                <div key={i} style={{ width: 2, height: h, background: '#0f8b40',
                                      borderRadius: 1 }} />
              ))}
            </div>
          </div>
        </div>
        <div style={{
          position: 'absolute', top: 0, bottom: 0, left: playheadX,
          width: 2, background: ACCENT, boxShadow: `0 0 8px ${ACCENT}88`,
          pointerEvents: 'none',
        }} />
      </div>
    </div>
  )
}

function Ruler({ dur }) {
  const ticks = []
  for (let s = 0; s <= Math.ceil(dur); s++) ticks.push(s)
  return (
    <div style={{ height: 24, position: 'relative', borderBottom: '1px solid #1e1e1e' }}>
      {ticks.map(s => (
        <span key={s} style={{
          position: 'absolute', left: s * PX_PER_S + 4, top: 4,
          fontSize: 10, color: '#6a6a68',
          fontFamily: 'ui-monospace, monospace',
        }}>{s.toFixed(2)}</span>
      ))}
    </div>
  )
}

function Clip({ scene, node, row, t, selection, onSelect }) {
  const active = t >= scene.start && t < scene.start + scene.dur
  const selected = selection && selection.nodeId === node.id
    && selection.sceneId === scene.id
  return (
    <div
      onMouseDown={ev => { ev.stopPropagation(); onSelect({ sceneId: scene.id, nodeId: node.id }) }}
      style={{
        position: 'absolute', top: row * ROW_H + 3,
        left: scene.start * PX_PER_S, width: scene.dur * PX_PER_S - 4,
        height: ROW_H - 6, borderRadius: 7, cursor: 'pointer',
        background: active ? ACCENT : '#1a1a1a',
        outline: selected ? '1px solid #fff' : 'none',
        color: active ? '#fff' : '#777775',
        display: 'flex', alignItems: 'center', padding: '0 10px',
        fontSize: 11, whiteSpace: 'nowrap', overflow: 'hidden',
        transition: 'background 80ms linear',
      }}
    >{node.id}</div>
  )
}

function KeyLane({ marks }) {
  return (
    <div style={{ position: 'relative', height: 16, minWidth: 10 }}>
      <div style={{ position: 'absolute', inset: '5px 0', background: '#cf7030',
                    borderRadius: 4, opacity: 0.85 }} />
      {marks.map((m, i) => (
        <div key={i} style={{
          position: 'absolute', left: m * PX_PER_S - 3, top: 5,
          width: 6, height: 6, background: '#fff',
          transform: 'rotate(45deg)',
        }} />
      ))}
    </div>
  )
}
