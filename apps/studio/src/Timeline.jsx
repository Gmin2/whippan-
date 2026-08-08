/* ─────────────────────────────────────────────────────────
 * TIMELINE
 *
 * pinned header column (icon + layer + scene) | scrolling lanes
 * ruler: minor ticks every 0.1s, labeled majors every 1s
 * rows: clip pill per node per scene, keyframe diamonds inline
 * below: orange marker lane, green audio lane
 * playhead: accent line + grab handle, pinned-follow while playing
 * ───────────────────────────────────────────────────────── */
import { useMemo, useRef, useState } from 'react'
import { timing } from './engine.js'
import { Pointer, TextTool, Shapes, Picture, PenNib, ZoomIn, ZoomOut } from './icons.jsx'

const TL = {
  height: 264,
  headerW: 192,
  rowH: 26,
  rulerH: 26,
  pinX: 300,          // playhead parks here, lanes scroll underneath
  pxPerS: 130,        // base zoom, scaled by the zoom control
  accent: '#606de0',
  marker: '#cf7030',
  wave: '#0f8b40',
  clip: '#1c1c1e',
  bg: '#111112',
  line: '#1e1e20',
}

const TYPE_ICON = {
  text: TextTool, rect: Shapes, image: Picture, path: PenNib, cursor: Pointer,
}

export default function Timeline({ doc, t, selection, onScrub, onSelect }) {
  const [zoom, setZoom] = useState(1)
  const pxs = TL.pxPerS * zoom
  const areaRef = useRef(null)
  const { dur, scenes } = useMemo(() => timing(doc.stage), [doc])

  const rows = useMemo(() =>
    scenes.flatMap(scene => scene.nodes.map(node => ({
      scene, node,
      keys: keyTimes(doc, scene, node),
    }))), [doc, scenes])

  const scroll = Math.max(0, t * pxs - TL.pinX)
  const playheadX = Math.min(TL.pinX, t * pxs)

  function scrubTo(ev) {
    const r = areaRef.current.getBoundingClientRect()
    onScrub(clamp((ev.clientX - r.left + scroll) / pxs, 0, dur))
  }

  function dragScrub(ev) {
    scrubTo(ev)
    const move = e => scrubTo(e)
    const up = () => {
      removeEventListener('mousemove', move)
      removeEventListener('mouseup', up)
    }
    addEventListener('mousemove', move)
    addEventListener('mouseup', up)
  }

  return (
    <div style={{
      height: TL.height, background: TL.bg, borderTop: `1px solid ${TL.line}`,
      display: 'flex', position: 'relative',
    }}>
      {/* pinned headers */}
      <div style={{
        width: TL.headerW, flexShrink: 0, borderRight: `1px solid ${TL.line}`,
        display: 'flex', flexDirection: 'column',
      }}>
        <div style={{
          height: TL.rulerH, display: 'flex', alignItems: 'center', gap: 6,
          padding: '0 10px', borderBottom: `1px solid ${TL.line}`,
          color: '#6a6a68',
        }}>
          <span style={{ fontSize: 10, letterSpacing: '.1em' }}>LAYERS</span>
          <span style={{ flex: 1 }} />
          <ZoomOut size={13} style={{ cursor: 'pointer' }}
                   onClick={() => setZoom(z => Math.max(0.4, z / 1.3))} />
          <ZoomIn size={13} style={{ cursor: 'pointer' }}
                  onClick={() => setZoom(z => Math.min(4, z * 1.3))} />
        </div>
        <div className="tl-scroll" style={{ flex: 1, overflowY: 'auto', overflowX: 'hidden' }}
             onScroll={e => { lanesRef.current.scrollTop = e.target.scrollTop }}>
          {rows.map((r, i) => (
            <Header key={r.scene.id + r.node.id} row={r} i={i}
                    selected={isSel(selection, r)} onSelect={onSelect} />
          ))}
        </div>
      </div>

      {/* lanes */}
      <div
        ref={areaRef}
        style={{ flex: 1, position: 'relative', overflow: 'hidden', cursor: 'ew-resize' }}
        onMouseDown={dragScrub}
      >
        <div style={{
          position: 'absolute', inset: 0, width: dur * pxs + 500,
          transform: `translateX(${-scroll}px)`,
        }}>
          <Ruler dur={dur} pxs={pxs} />
          <div ref={el => { lanesRef.current = el ?? lanesRef.current }}
               className="tl-scroll"
               style={{ position: 'absolute', top: TL.rulerH, bottom: 48,
                        left: 0, right: 0, overflowY: 'hidden' }}>
            {rows.map((r, i) => (
              <Lane key={r.scene.id + r.node.id} row={r} i={i} t={t} pxs={pxs}
                    selected={isSel(selection, r)} onSelect={onSelect} />
            ))}
          </div>
          <MarkerLane rows={rows} pxs={pxs} />
          <Waveform dur={dur} pxs={pxs} />
        </div>

        {/* playhead */}
        <div style={{
          position: 'absolute', top: 0, bottom: 0, left: playheadX,
          pointerEvents: 'none',
        }}>
          <div style={{
            position: 'absolute', top: 0, bottom: 0, left: -1, width: 2,
            background: TL.accent, boxShadow: `0 0 8px ${TL.accent}88`,
          }} />
          <div style={{
            position: 'absolute', top: 2, left: -17, padding: '1px 5px',
            background: TL.accent, borderRadius: 5, fontSize: 10,
            fontFamily: 'ui-monospace, monospace', color: '#fff',
          }}>{t.toFixed(2)}</div>
        </div>
      </div>
    </div>
  )
}

const lanesRef = { current: null }

function isSel(sel, r) {
  return sel && sel.nodeId === r.node.id && sel.sceneId === r.scene.id
}

function keyTimes(doc, scene, node) {
  const marks = []
  for (const tr of doc.anim.tracks ?? []) {
    if (tr.target !== node.id) continue
    const base = scene.start + (tr.at ?? 0)
    if (tr.reveal || tr.enter) marks.push({ t: base, kind: 'reveal' })
    for (const keys of Object.values(tr.keys ?? {}))
      for (const k of keys) marks.push({ t: base + k.t, kind: 'key' })
  }
  const seen = new Set()
  return marks.filter(m => {
    const id = m.kind + Math.round(m.t * 60)
    return seen.has(id) ? false : (seen.add(id), true)
  })
}

function Header({ row, i, selected, onSelect }) {
  const Icon = TYPE_ICON[row.node.type] ?? Shapes
  return (
    <div
      onMouseDown={() => onSelect({ sceneId: row.scene.id, nodeId: row.node.id })}
      style={{
        height: TL.rowH, display: 'flex', alignItems: 'center', gap: 8,
        padding: '0 10px', cursor: 'pointer',
        background: selected ? '#1d1d22' : i % 2 ? '#131314' : 'transparent',
        borderLeft: selected ? `2px solid ${TL.accent}` : '2px solid transparent',
        color: selected ? '#e8e8e6' : '#8f8f8d',
      }}
    >
      <Icon size={13} style={{ flexShrink: 0, opacity: 0.8 }} />
      <span style={{
        fontSize: 11, whiteSpace: 'nowrap', overflow: 'hidden',
        textOverflow: 'ellipsis', flex: 1,
      }}>{row.node.id}</span>
      <span style={{
        fontSize: 9, color: '#5a5a58',
        fontFamily: 'ui-monospace, monospace',
      }}>{row.scene.id}</span>
    </div>
  )
}

function Lane({ row, i, t, pxs, selected, onSelect }) {
  const { scene, node, keys } = row
  const active = t >= scene.start && t < scene.start + scene.dur
  return (
    <div style={{
      height: TL.rowH, position: 'relative',
      background: i % 2 ? '#131314' : 'transparent',
    }}>
      <div
        onMouseDown={ev => {
          ev.stopPropagation()
          onSelect({ sceneId: scene.id, nodeId: node.id })
        }}
        style={{
          position: 'absolute', top: 4, height: TL.rowH - 8,
          left: scene.start * pxs, width: scene.dur * pxs - 3,
          borderRadius: 6, cursor: 'pointer',
          background: active ? TL.accent : TL.clip,
          outline: selected ? '1px solid #ffffffcc' : 'none',
          transition: 'background 90ms linear',
        }}
      >
        {keys.map((m, j) => (
          <div key={j} style={{
            position: 'absolute',
            left: (m.t - scene.start) * pxs - (m.kind === 'key' ? 3 : 4),
            top: '50%',
            ...(m.kind === 'key'
              ? { width: 6, height: 6, transform: 'translateY(-50%) rotate(45deg)',
                  background: active ? '#fff' : '#8f8f8d' }
              : { width: 0, height: 0, transform: 'translateY(-50%)',
                  borderLeft: `8px solid ${active ? '#fff' : '#8f8f8d'}`,
                  borderTop: '4px solid transparent',
                  borderBottom: '4px solid transparent' }),
          }} />
        ))}
      </div>
    </div>
  )
}

function Ruler({ dur, pxs }) {
  const majors = []
  for (let s = 0; s <= Math.ceil(dur); s++) majors.push(s)
  const minorEvery = pxs >= 90 ? 0.1 : 0.5
  const minors = []
  for (let s = 0; s <= dur; s += minorEvery) minors.push(s)
  return (
    <div style={{
      height: TL.rulerH, position: 'relative',
      borderBottom: `1px solid ${TL.line}`,
    }}>
      {minors.map(s => (
        <div key={'m' + s} style={{
          position: 'absolute', left: s * pxs, bottom: 0, width: 1, height: 5,
          background: '#2c2c2e',
        }} />
      ))}
      {majors.map(s => (
        <div key={s} style={{ position: 'absolute', left: s * pxs, bottom: 0 }}>
          <div style={{ width: 1, height: 9, background: '#4a4a4c' }} />
          <span style={{
            position: 'absolute', left: 4, bottom: 7, fontSize: 10,
            color: '#6a6a68', fontFamily: 'ui-monospace, monospace',
          }}>{s}s</span>
        </div>
      ))}
    </div>
  )
}

function MarkerLane({ rows, pxs }) {
  const marks = useMemo(() => {
    const all = rows.flatMap(r => r.keys.map(m => m.t))
    return [...new Set(all.map(m => Math.round(m * 30) / 30))]
  }, [rows])
  return (
    <div style={{ position: 'absolute', bottom: 26, left: 0, right: 0, height: 16 }}>
      <div style={{
        position: 'absolute', inset: '5px 0', background: TL.marker,
        opacity: 0.85, borderRadius: 4,
      }} />
      {marks.map((m, i) => (
        <div key={i} style={{
          position: 'absolute', left: m * pxs - 3, top: 5, width: 6, height: 6,
          background: '#fff', transform: 'rotate(45deg)',
        }} />
      ))}
    </div>
  )
}

function Waveform({ dur, pxs }) {
  const bars = useMemo(() => {
    const out = []
    for (let i = 0; i < dur * 20; i++)
      out.push(3 + Math.abs(Math.sin(i * 1.7) * 0.6 + Math.sin(i * 0.43) * 0.4) * 13)
    return out
  }, [dur])
  const w = (dur * pxs) / bars.length
  return (
    <div style={{
      position: 'absolute', bottom: 2, left: 0, height: 20,
      display: 'flex', alignItems: 'center', gap: 0,
    }}>
      {bars.map((h, i) => (
        <div key={i} style={{
          width: Math.max(1, w - 1), marginRight: 1, height: h,
          background: TL.wave, borderRadius: 1,
        }} />
      ))}
    </div>
  )
}

function clamp(v, a, b) {
  return Math.max(a, Math.min(b, v))
}
