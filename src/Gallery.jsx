/* ─────────────────────────────────────────────────────────
 * GALLERY — svg-harness layout, whippan content
 *
 * light field, left rail of dash-marked numbered entries with a
 * fisheye hover and live engine-rendered preview cards, the film
 * centered under a hint + hairline, a white pill dock below
 * (play / replay / scrub / edit / copy link).
 * ───────────────────────────────────────────────────────── */
import { useEffect, useRef, useState } from 'react'
import { loadDoc, timing, render, paintFrame } from './engine.js'
import { Play, Pause, Pointer } from './icons.jsx'

const G = {
  accent: '#f02900',
  ink: '#171717',
  dim: '#9a9a97',
  bg: '#f4f4f3',
  railW: 300,
  tick: 26,
  tickActive: 50,
  fisheye: 90,       // px falloff of the hover lens
}

export default function Gallery({ ck, registry, onEdit }) {
  const [slug, setSlug] = useState(
    location.hash.replace(/^#\/?/, '') || registry[0]?.slug)
  const [doc, setDoc] = useState(null)
  const [t, setT] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [hovered, setHovered] = useState(null)   // { slug, y }
  const [runKey, setRunKey] = useState(0)
  const [copied, setCopied] = useState(false)
  const railRef = useRef(null)
  const raf = useRef(null)

  const entry = registry.find(e => e.slug === slug) ?? registry[0]

  useEffect(() => {
    let alive = true
    setDoc(null)
    setPlaying(false)
    setT(0)
    loadDoc(entry).then(d => { if (alive) { setDoc(d); setPlaying(true) } })
    location.hash = '/' + entry.slug
    return () => { alive = false }
  }, [entry.slug])

  const dur = doc ? timing(doc.stage).dur : 1

  useEffect(() => {
    if (!playing || !doc) return
    let last = performance.now()
    const tick = now => {
      const dt = (now - last) / 1000
      last = now
      setT(prev => (prev + dt) % dur)
      raf.current = requestAnimationFrame(tick)
    }
    raf.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf.current)
  }, [playing, doc, dur, runKey])

  function fisheye(ev) {
    const rows = railRef.current?.querySelectorAll('[data-row]') ?? []
    for (const row of rows) {
      const r = row.getBoundingClientRect()
      const d = Math.abs(ev.clientY - (r.top + r.height / 2))
      const k = Math.max(0, 1 - d / G.fisheye)
      row.style.transform = `scale(${1 + k * 0.14}) translateX(${k * 6}px)`
      row.style.opacity = 0.45 + k * 0.55
    }
  }

  function restRail() {
    const rows = railRef.current?.querySelectorAll('[data-row]') ?? []
    for (const row of rows) {
      row.style.transform = 'none'
      row.style.opacity = 1
    }
    setHovered(null)
  }

  let group = null
  let num = 0

  return (
    <div style={{
      position: 'absolute', inset: 0, background: G.bg, color: G.ink,
      overflow: 'hidden',
      font: '14px/1.45 -apple-system, "SF Pro Text", Inter, sans-serif',
    }}>
      {/* rail */}
      <nav
        ref={railRef}
        onMouseMove={fisheye}
        onMouseLeave={restRail}
        style={{
          position: 'fixed', left: 0, top: 0, bottom: 0, width: G.railW,
          overflowY: 'auto', padding: '72px 0 40vh 30px',
          scrollbarWidth: 'none', zIndex: 5,
          maskImage: 'linear-gradient(to bottom, transparent 2%, black 12%, black 88%, transparent 98%)',
        }}
      >
        <div style={{ fontWeight: 650, marginBottom: 22 }}>
          whippan <span style={{ color: G.accent }}>gallery</span>
        </div>
        {registry.map(e => {
          const g = e.group || 'examples'
          const head = g !== group
          if (head) { group = g; num = 0 }
          num += 1
          const active = e.slug === entry.slug
          return (
            <div key={e.slug}>
              {head && (
                <div style={{ margin: '18px 0 6px', fontSize: 10,
                              letterSpacing: '.16em', color: '#c2c2bf',
                              textTransform: 'uppercase' }}>{g}</div>
              )}
              <div data-row style={{ transformOrigin: 'left center',
                                     transition: 'transform 120ms, opacity 120ms' }}>
                <button
                  onClick={() => setSlug(e.slug)}
                  onMouseEnter={ev => {
                    const r = ev.currentTarget.getBoundingClientRect()
                    setHovered({ slug: e.slug, y: r.top + r.height / 2 })
                  }}
                  onMouseLeave={() => setHovered(null)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '5px 0', border: 0, background: 'none',
                    font: 'inherit', cursor: 'pointer',
                    color: active ? G.ink : G.dim,
                  }}
                >
                  <span style={{
                    width: active ? G.tickActive : G.tick, height: 1,
                    background: active ? G.accent : '#c9c9c6',
                    transition: 'width 250ms cubic-bezier(0.2,0.9,0.25,1)',
                  }} />
                  <span style={{ whiteSpace: 'nowrap' }}>
                    {String(num).padStart(2, '0')} {e.title}
                  </span>
                </button>
              </div>
            </div>
          )
        })}
      </nav>

      {hovered && hovered.slug !== entry.slug && (
        <PreviewCard ck={ck} registry={registry} slug={hovered.slug} y={hovered.y} />
      )}

      {/* stage */}
      <main key={entry.slug + runKey} style={{
        position: 'absolute', inset: 0, display: 'grid',
        placeItems: 'center', paddingLeft: G.railW - 60,
        animation: 'stage-in 550ms cubic-bezier(0.22,1,0.36,1)',
      }}>
        <div style={{ display: 'flex', flexDirection: 'column',
                      alignItems: 'center', gap: 14 }}>
          <div style={{ fontSize: 11, letterSpacing: '.14em',
                        textTransform: 'uppercase', color: '#b0b0ad' }}>
            {entry.title} — {(entry.dur ?? dur).toFixed(1)}s
          </div>
          <div style={{ width: 520, height: 1, background: '#e2e2e0' }} />
          {doc
            ? <Film ck={ck} doc={doc} t={t} />
            : <div style={{ width: 640, height: 360, display: 'grid',
                            placeItems: 'center', color: '#b0b0ad' }}>loading</div>}
        </div>
      </main>

      {/* dock */}
      <div style={{
        position: 'fixed', bottom: 26, left: '50%', zIndex: 10,
        transform: `translateX(calc(-50% + ${G.railW / 2 - 30}px))`,
        display: 'flex', alignItems: 'center', gap: 10,
        background: 'rgba(255,255,255,0.92)', backdropFilter: 'blur(6px)',
        border: '1px solid rgba(0,0,0,0.07)', borderRadius: 999,
        padding: '8px 14px',
        boxShadow: '0 18px 44px -18px rgba(0,0,0,0.4)',
      }}>
        <Dot title={playing ? 'pause' : 'play'} accent
             onClick={() => setPlaying(p => !p)}>
          {playing ? <Pause size={13} /> : <Play size={13} />}
        </Dot>
        <Dot title="replay" onClick={() => { setT(0); setRunKey(k => k + 1); setPlaying(true) }}>
          <ReplayIcon />
        </Dot>
        <input
          type="range" min={0} max={dur} step={1 / 60} value={t}
          onChange={e => { setPlaying(false); setT(parseFloat(e.target.value)) }}
          style={{ width: 240, accentColor: G.accent }}
        />
        <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 11,
                       color: '#8a8a88', width: 46 }}>{t.toFixed(2)}s</span>
        <Dot title="open in editor" onClick={() => onEdit(entry.slug)}>
          <Pointer size={13} />
        </Dot>
        <Dot title={copied ? 'copied' : 'copy link'} onClick={() => {
          navigator.clipboard?.writeText(location.href).catch(() => {})
          setCopied(true)
          setTimeout(() => setCopied(false), 1200)
        }}>
          {copied ? <CheckIcon /> : <LinkIcon />}
        </Dot>
      </div>

      <style>{`@keyframes stage-in {
        from { transform: translateY(16px); opacity: 0 }
        to { transform: none; opacity: 1 } }`}</style>
    </div>
  )
}

function Film({ ck, doc, t }) {
  const ref = useRef(null)
  const surf = useRef(null)
  const [w, h] = doc.stage.size
  const fit = Math.min((innerWidth - G.railW - 160) / w, innerHeight * 0.62 / h, 1)

  useEffect(() => {
    const surface = ck.MakeCanvasSurface(ref.current)
    const paint = new ck.Paint()
    paint.setAntiAlias(true)
    surf.current = { surface, skc: surface.getCanvas(), paint }
    return () => { paint.delete(); surface.delete(); surf.current = null }
  }, [ck, doc])

  useEffect(() => {
    const s = surf.current
    if (!s) return
    paintFrame(ck, s.skc, s.paint,
      JSON.parse(render(JSON.stringify(doc.stage), JSON.stringify(doc.anim), t)),
      doc.images)
    s.surface.flush()
  })

  return (
    <canvas ref={ref} width={w} height={h}
            style={{ width: Math.round(w * fit), borderRadius: 10,
                     background: '#000',
                     boxShadow: '0 1px 2px rgba(0,0,0,0.06), 0 12px 40px rgba(0,0,0,0.1)' }} />
  )
}

// small live preview beside the rail: first mid-film frame of that doc
function PreviewCard({ ck, registry, slug, y }) {
  const ref = useRef(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    let alive = true
    const entry = registry.find(e => e.slug === slug)
    loadDoc(entry).then(doc => {
      if (!alive || !ref.current) return
      const [w, h] = doc.stage.size
      ref.current.width = w
      ref.current.height = h
      const surface = ck.MakeCanvasSurface(ref.current)
      const paint = new ck.Paint()
      paint.setAntiAlias(true)
      const mid = timing(doc.stage).dur * 0.4
      paintFrame(ck, surface.getCanvas(), paint,
        JSON.parse(render(JSON.stringify(doc.stage), JSON.stringify(doc.anim), mid)),
        doc.images)
      surface.flush()
      paint.delete()
      surface.delete()
      setReady(true)
    })
    return () => { alive = false }
  }, [slug])

  return (
    <div style={{
      position: 'fixed', left: G.railW + 8, top: y - 60, zIndex: 8,
      width: 210, borderRadius: 10, overflow: 'hidden',
      background: '#fff', border: '1px solid rgba(0,0,0,0.07)',
      boxShadow: '0 24px 50px -20px rgba(0,0,0,0.35)',
      opacity: ready ? 1 : 0, transition: 'opacity 160ms',
      pointerEvents: 'none',
    }}>
      <canvas ref={ref} style={{ width: '100%', display: 'block' }} />
    </div>
  )
}

function Dot({ children, title, accent, onClick }) {
  return (
    <button title={title} onClick={onClick} style={{
      width: 30, height: 30, borderRadius: 999, border: 0,
      display: 'grid', placeItems: 'center', cursor: 'pointer',
      background: accent ? G.accent : 'transparent',
      color: accent ? '#fff' : '#5a5a58',
    }}>{children}</button>
  )
}

const ReplayIcon = () => (
  <svg width="14" height="14" viewBox="0 0 20 20">
    <path d="m4,10c0,3.314,2.686,6,6,6,1.227,0,2.367-.368,3.317-1" fill="none"
          stroke="currentColor" strokeLinecap="round" strokeWidth="2" />
    <path d="m16,10c0-3.314-2.686-6-6-6-1.227,0-2.367.368-3.317,1" fill="none"
          stroke="currentColor" strokeLinecap="round" strokeWidth="2" />
    <polygon points="14.25 10 16 12 17.75 10" fill="currentColor" />
    <polygon points="5.75 10 4 8 2.25 10" fill="currentColor" />
  </svg>
)

const LinkIcon = () => (
  <svg width="13" height="13" viewBox="0 0 20 20">
    <path d="m8 12l4-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    <path d="m9 6l1.5-1.5a3.2 3.2 0 014.5 4.5L13.5 10.5" fill="none"
          stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    <path d="m11 14l-1.5 1.5a3.2 3.2 0 01-4.5-4.5L6.5 9.5" fill="none"
          stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
  </svg>
)

const CheckIcon = () => (
  <svg width="13" height="13" viewBox="0 0 20 20">
    <polyline points="4 11 8.5 15 16 5" fill="none" stroke="currentColor"
              strokeWidth="2.4" strokeLinecap="round" />
  </svg>
)
