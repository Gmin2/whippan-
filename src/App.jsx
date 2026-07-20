import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'
import { Navigate, Route, Routes, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { gsap } from 'gsap'
import { motion, useMotionTemplate, useSpring } from 'motion/react'
import { boot, loadDoc, docDur, render, paintFrame } from './engine.js'
import { fisheyeList, pressFeedback } from './tools/interaction.js'

// The whippan gallery, a faithful port of the svg-harness playground
// (skiper-ui style): a left rail of dash-marked entries with fisheye hover
// and live preview cards, the film centered under a hint and a hairline,
// a floating pill dock. Every film routes at /<slug>; the isolated view
// stays at /?render=<slug>.

// rail craft, the harness's tuned dial values
const RAIL = {
  rowGap: 0, fontSize: 14.5, tick: 47, tickActive: 70, labelGap: 8,
  fisheye: { spread: 140, scale: 0.17, shift: 15 },
  rest: { dim: 0.5, fadePer: 0.05, blurMax: 0.5 },
}

function useEngine() {
  const [eng, setEng] = useState(null)
  useEffect(() => { boot().then(setEng) }, [])
  return eng
}

// the film itself: engine draw commands through the shared skia painter,
// looping in real time
function Film({ ck, doc, animated = true, className, style }) {
  const ref = useRef(null)
  const surf = useRef(null)
  const [w, h] = doc.stage.size
  const dur = docDur(doc.stage)

  useEffect(() => {
    const surface = ck.MakeCanvasSurface(ref.current)
    const paint = new ck.Paint()
    paint.setAntiAlias(true)
    surf.current = { surface, skc: surface.getCanvas(), paint }
    const stage = JSON.stringify(doc.stage)
    const anim = JSON.stringify(doc.anim)
    let raf
    const t0 = performance.now()
    const draw = now => {
      const s = surf.current
      if (!s) return
      const t = animated ? ((now - t0) / 1000) % dur : dur * 0.4
      paintFrame(ck, s.skc, s.paint, JSON.parse(render(stage, anim, t)), doc.images)
      s.surface.flush()
      if (animated) raf = requestAnimationFrame(draw)
    }
    draw(t0)
    return () => {
      cancelAnimationFrame(raf)
      paint.delete()
      surface.delete()
      surf.current = null
    }
  }, [ck, doc, animated, dur])

  return <canvas ref={ref} width={w} height={h} className={className}
                 style={style} data-film />
}

function RenderRoute({ ck, registry, name }) {
  const [doc, setDoc] = useState(null)
  const entry = registry.find(e => e.slug === name)
  useEffect(() => { if (entry) loadDoc(entry).then(setDoc) }, [name])
  if (!entry) return <p className="p-8 text-red-600">unknown film: {name}</p>
  if (!doc) return null
  return (
    <div className="grid min-h-screen place-items-center bg-neutral-100">
      <div id="art" style={{ width: doc.stage.size[0] }}>
        <Film ck={ck} doc={doc} className="h-auto w-full" />
      </div>
    </div>
  )
}

function Home({ registry }) {
  const [q] = useSearchParams()
  if (q.get('render')) return null // handled in App
  return <Navigate to={`/${registry[0].slug}`} replace />
}

// nucleo micro-bold icons, inlined (shared with the harness)
const IconRefresh = () => (
  <svg width="15" height="15" viewBox="0 0 20 20">
    <path d="m4,10c0,3.314,2.686,6,6,6,1.227,0,2.367-.368,3.317-1" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
    <polygon points="14.25 10 16 12 17.75 10 14.25 10" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" fill="currentColor" />
    <path d="m16,10c0-3.314-2.686-6-6-6-1.227,0-2.367.368-3.317,1" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
    <polygon points="5.75 10 4 8 2.25 10 5.75 10" fill="currentColor" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
  </svg>
)

const IconArrowUpRight = () => (
  <svg width="15" height="15" viewBox="0 0 20 20">
    <line x1="4" y1="16" x2="16" y2="4" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
    <polyline points="16 11 16 4 9 4" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
  </svg>
)

const IconSidebar = () => (
  <svg width="17" height="17" viewBox="0 0 24 24" style={{ transform: 'scaleX(-1)' }}>
    <line x1="15" y1="4" x2="15" y2="20" fill="none" stroke="currentColor" strokeMiterlimit="10" strokeWidth="2" />
    <rect x="4" y="2" width="16" height="20" rx="2" ry="2" transform="translate(24) rotate(90)" fill="none" stroke="currentColor" strokeLinecap="square" strokeMiterlimit="10" strokeWidth="2" />
    <rect x="16" y="6" width="4" height="12" rx="1" fill="currentColor" />
  </svg>
)

const IconWindowCode = () => (
  <svg width="15" height="15" viewBox="0 0 20 20">
    <polyline points="12.5 12 10 14.5 12.5 17" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
    <path d="m17,8.845v-2.845c0-1.657-1.343-3-3-3H6c-1.657,0-3,1.343-3,3v8c0,1.657,1.343,3,3,3h1.55l-.025-.025" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
    <polyline points="15.5 17 18 14.5 15.5 12" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
  </svg>
)

const IconDownload = () => (
  <svg width="15" height="15" viewBox="0 0 20 20">
    <line x1="10" y1="3" x2="10" y2="13" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
    <polyline points="6 9.5 10 13.5 14 9.5" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
    <path d="m3,14v1c0,1.105.895,2,2,2h10c1.105,0,2-.895,2-2v-1" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
  </svg>
)

const IconCopy = () => (
  <svg width="13" height="13" viewBox="0 0 20 20">
    <rect x="7" y="7" width="10" height="10" rx="2" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
    <path d="m13,4v-1c0-1.105-.895-2-2-2h-6c-1.105,0-2,.895-2,2v6c0,1.105.895,2,2,2h1" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" transform="translate(1 2)" />
  </svg>
)

const IconCheck = () => (
  <svg width="13" height="13" viewBox="0 0 20 20">
    <polyline points="4 11 8.5 15 16 5" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.4" />
  </svg>
)

// pill button: press squash + back.out pop, per-action icon flourish
function PillAction({ fx = 'none', onClick, href, active, children }) {
  const ref = useRef(null)
  const iconRef = useRef(null)
  const press = useRef(null)

  useLayoutEffect(() => {
    if (ref.current) press.current = pressFeedback(ref.current)
  }, [])

  const flourish = () => {
    if (!iconRef.current) return
    if (fx === 'spin')
      gsap.fromTo(iconRef.current, { rotate: 0 }, { rotate: 360, duration: 0.6, ease: 'power2.out' })
    if (fx === 'dip')
      gsap.fromTo(iconRef.current, { y: 0 }, { y: 3, duration: 0.14, yoyo: true, repeat: 1, ease: 'power2.out' })
  }

  const inner = (
    <span
      ref={ref}
      className={`grid h-8 w-8 place-items-center rounded-full transition-colors duration-200 hover:bg-neutral-100 ${
        active ? 'bg-sky-50 text-sky-500' : 'text-neutral-500 hover:text-neutral-800'
      }`}
    >
      <span ref={iconRef} className="grid place-items-center transition-transform duration-200 group-hover:-translate-y-px">
        {children}
      </span>
    </span>
  )

  const common = {
    className: 'group relative',
    onPointerDown: () => press.current?.press(),
    onPointerUp: () => press.current?.release(),
    onPointerLeave: () => press.current?.release(),
    onClick: () => {
      flourish()
      onClick?.()
    },
  }

  if (href)
    return (
      <a href={href} target="_blank" rel="noreferrer" {...common}>
        {inner}
      </a>
    )
  return <button {...common}>{inner}</button>
}

const DOCK_SPRING = { stiffness: 300, damping: 30, mass: 0.8 }
const DOCK_LABELS = ['replay', 'save frame .png', 'zen mode', 'isolated render', 'copy link']

const THUMB_W = 208

// preview thumbnails: one engine-rendered mid-film frame per doc, cached
const thumbCache = new Map()
async function thumbFrame(ck, entry) {
  let url = thumbCache.get(entry.slug)
  if (url) return url
  const doc = await loadDoc(entry)
  const [w, h] = doc.stage.size
  const canvas = document.createElement('canvas')
  canvas.width = w
  canvas.height = h
  const surface = (ck.MakeSWCanvasSurface ?? ck.MakeCanvasSurface).call(ck, canvas)
  const paint = new ck.Paint()
  paint.setAntiAlias(true)
  const t = docDur(doc.stage) * 0.4
  paintFrame(ck, surface.getCanvas(), paint,
    JSON.parse(render(JSON.stringify(doc.stage), JSON.stringify(doc.anim), t)),
    doc.images)
  surface.flush()
  url = canvas.toDataURL('image/png')
  paint.delete()
  surface.delete()
  thumbCache.set(entry.slug, url)
  return url
}

function Preview({ ck, registry, name, index, y }) {
  const ref = useRef(null)
  const [src, setSrc] = useState(thumbCache.get(name))
  const entry = registry.find(e => e.slug === name)
  const [w, h] = entry.size ?? [1920, 1080]
  const sc = THUMB_W / w
  const th = Math.round(h * sc)

  useEffect(() => {
    let alive = true
    thumbFrame(ck, entry).then(u => { if (alive) setSrc(u) })
    return () => { alive = false }
  }, [name])

  useLayoutEffect(() => {
    gsap.fromTo(
      ref.current,
      { autoAlpha: 0, scale: 0.92, x: -10 },
      { autoAlpha: 1, scale: 1, x: 0, duration: 0.35, ease: 'back.out(1.7)' },
    )
  }, [name])

  const top = Math.min(Math.max(y, th / 2 + 24), window.innerHeight - th / 2 - 48)
  return (
    <div
      ref={ref}
      className="pointer-events-none fixed z-20 -translate-y-1/2 rounded-xl border border-black/10 bg-white p-2 shadow-lg"
      style={{ left: '21rem', top }}
    >
      <div className="overflow-hidden rounded-lg border border-black/5 bg-[#f4f4f3]"
           style={{ width: THUMB_W, height: Math.min(th, 260) }}>
        {src && <img src={src} width={THUMB_W} height={th} alt="" />}
      </div>
      <div className="flex items-center justify-between px-1 pt-1.5">
        <span className="text-[10px] text-neutral-400">{entry.title}</span>
        <span className="font-mono text-[9px] text-neutral-300">
          {String(index + 1).padStart(2, '0')} / {String(registry.length).padStart(2, '0')}
        </span>
      </div>
    </div>
  )
}

function Playground({ ck, registry }) {
  const { name = '' } = useParams()
  const navigate = useNavigate()
  const [doc, setDoc] = useState(null)
  const [runKey, setRunKey] = useState(0)
  const [hovered, setHovered] = useState(null)
  const [zen, setZen] = useState(false)
  const [stageScale, setStageScale] = useState(1)
  const [stagePan, setStagePan] = useState({ x: 0, y: 0 })
  const stageRef = useRef(null)
  const dragRef = useRef(null)
  const [navOpen, setNavOpen] = useState(true)
  const [copied, setCopied] = useState(false)
  const dockRef = useRef(null)
  const dockIconRefs = useRef([])
  const dockTipRefs = useRef([])
  const dockTipParentRef = useRef(null)
  const navRef = useRef(null)
  const mainRef = useRef(null)

  const names = registry.map(e => e.slug)
  const entry = registry.find(e => e.slug === name)

  useEffect(() => {
    if (entry) document.title = `${name} · whippan gallery`
  }, [name, entry])

  useEffect(() => {
    let alive = true
    setDoc(null)
    if (entry) loadDoc(entry).then(d => { if (alive) setDoc(d) })
    return () => { alive = false }
  }, [name])

  // wheel over the canvas zooms; horizontal (or shift) pans; dblclick resets
  useEffect(() => {
    setStageScale(1)
    setStagePan({ x: 0, y: 0 })
  }, [name])
  useEffect(() => {
    const el = stageRef.current
    if (!el) return
    const onWheel = e => {
      e.preventDefault()
      if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) {
        setStagePan(p => ({ ...p, x: p.x - e.deltaX }))
      } else if (e.shiftKey) {
        setStagePan(p => ({ ...p, x: p.x - e.deltaY }))
      } else {
        setStageScale(z => Math.min(4, Math.max(0.35, z * Math.exp(-e.deltaY * 0.0012))))
      }
    }
    const onDown = e => {
      dragRef.current = { px: e.clientX, py: e.clientY }
      el.setPointerCapture(e.pointerId)
    }
    const onMove = e => {
      const d = dragRef.current
      if (!d) return
      setStagePan(p => ({ x: p.x + e.clientX - d.px, y: p.y + e.clientY - d.py }))
      dragRef.current = { px: e.clientX, py: e.clientY }
    }
    const onUp = () => { dragRef.current = null }
    el.addEventListener('wheel', onWheel, { passive: false })
    el.addEventListener('pointerdown', onDown)
    el.addEventListener('pointermove', onMove)
    el.addEventListener('pointerup', onUp)
    el.addEventListener('pointercancel', onUp)
    return () => {
      el.removeEventListener('wheel', onWheel)
      el.removeEventListener('pointerdown', onDown)
      el.removeEventListener('pointermove', onMove)
      el.removeEventListener('pointerup', onUp)
      el.removeEventListener('pointercancel', onUp)
    }
  })

  // rest state: rows fade + blur with distance from the active one
  const restFade = useCallback(() => {
    if (!navRef.current) return
    const ai = names.indexOf(name)
    const rows = gsap.utils.toArray('[data-row]', navRef.current)
    gsap.killTweensOf(rows)
    rows.forEach((row, i) => {
      const dist = Math.abs(i - ai)
      gsap.to(row, {
        opacity: i === ai ? 1 : Math.max(RAIL.rest.dim, 1 - dist * RAIL.rest.fadePer),
        filter: `blur(${Math.min(Math.max(dist - 3, 0) * 0.4, RAIL.rest.blurMax)}px)`,
        x: 0,
        scale: 1,
        duration: 0.45,
        ease: 'power2.out',
      })
    })
  }, [name])

  // dock entrance
  useLayoutEffect(() => {
    if (!dockRef.current) return
    gsap.fromTo(
      dockRef.current,
      { y: 18, autoAlpha: 0 },
      { y: 0, autoAlpha: 1, duration: 0.6, ease: 'power3.out', delay: 0.15 },
    )
  }, [])

  // dock tooltip: one strip revealed through a spring-animated clip-path
  // window. Adapted from Skiper UI's skiper43 by @gurvinder-singh02 —
  // https://gxuri.me — used with attribution.
  const tipX = useSpring(0, { stiffness: 350, damping: 30 })
  const clipL = useSpring(0, DOCK_SPRING)
  const clipR = useSpring(100, DOCK_SPRING)
  const tipOpacity = useSpring(0, DOCK_SPRING)
  const tipClip = useMotionTemplate`inset(0 ${clipR}% 0 ${clipL}% round 8px)`

  const dockEnter = useCallback(
    index => {
      const iconR = dockIconRefs.current[index]?.getBoundingClientRect()
      const parentR = dockTipParentRef.current?.getBoundingClientRect()
      const segs = dockTipRefs.current
      if (!iconR || !parentR || !segs[index]) return
      let before = 0
      for (let i = 0; i < index; i++) before += segs[i]?.getBoundingClientRect().width || 0
      const cur = segs[index].getBoundingClientRect().width
      const total = segs.reduce((sum, el) => sum + (el?.getBoundingClientRect().width || 0), 0)
      const after = total - before - cur
      tipX.set(iconR.left + iconR.width / 2 - (parentR.left + before + cur / 2))
      clipL.set(total ? (before / total) * 100 : 0)
      clipR.set(total ? (after / total) * 100 : 0)
      tipOpacity.set(1)
    },
    [tipX, clipL, clipR, tipOpacity],
  )
  const dockLeave = useCallback(() => tipOpacity.set(0), [tipOpacity])

  // vertical fisheye on the rail
  const lensRef = useRef(null)
  useLayoutEffect(() => {
    if (!navRef.current) return
    const rows = gsap.utils.toArray('[data-row]', navRef.current)
    gsap.set(rows, { transformOrigin: 'left center' })
    lensRef.current = fisheyeList(rows, {
      spread: RAIL.fisheye.spread,
      scale: RAIL.fisheye.scale,
      shift: RAIL.fisheye.shift,
      dim: RAIL.rest.dim,
    })
  }, [])

  useLayoutEffect(() => {
    if (!navRef.current) return
    restFade()
    gsap.fromTo('[data-activeline]', { width: RAIL.tick }, { width: RAIL.tickActive, duration: 0.5, ease: 'power3.out' })
    const ai = names.indexOf(name)
    const rows = gsap.utils.toArray('[data-row]', navRef.current)
    rows[ai]?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  }, [name, restFade])

  // sidebar collapse
  useLayoutEffect(() => {
    if (!navRef.current) return
    gsap.to(navRef.current, {
      x: navOpen ? 0 : -340,
      autoAlpha: navOpen ? 1 : 0,
      duration: 0.55,
      ease: 'power3.inOut',
    })
  }, [navOpen])

  // stage entrance on switch/replay
  useLayoutEffect(() => {
    if (!mainRef.current) return
    gsap.fromTo(mainRef.current, { y: 16, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.55, ease: 'power3.out' })
  }, [name, runKey])

  if (!entry) return <Navigate to="/" replace />

  const copyLink = () => {
    navigator.clipboard?.writeText(`${window.location.origin}/${name}`).catch(() => {})
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1200)
  }

  const savePng = () => {
    const c = document.querySelector('[data-film]')
    if (!c) return
    c.toBlob(blob => {
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = `${name}-frame.png`
      a.click()
      URL.revokeObjectURL(a.href)
    })
  }

  // fit the film into the stage
  const [fw, fh] = entry.size ?? [1920, 1080]
  const maxW = Math.min(fw, window.innerWidth * (zen ? 0.8 : 0.52))
  const maxH = window.innerHeight * (zen ? 0.9 : 0.7)
  const stageW = Math.round(Math.min(maxW, (maxH * fw) / fh))

  const group = entry.group || 'examples'

  return (
    <div className="min-h-screen overflow-hidden bg-[#f4f4f3] text-neutral-800">
      {/* sidebar toggle */}
      {!zen && (
        <button
          onClick={() => setNavOpen(o => !o)}
          title="toggle sidebar"
          className="fixed left-5 top-5 z-30 grid h-11 w-11 place-items-center rounded-2xl border border-black/5 bg-white text-neutral-500 shadow-md hover:text-neutral-700"
        >
          <IconSidebar />
        </button>
      )}

      {/* sidebar rail */}
      {!zen && (
        <nav ref={navRef} className="fixed left-0 top-0 z-10 h-full w-80">
          <div
            className="h-full overflow-y-auto pl-6 [scrollbar-width:none]"
            style={{
              maskImage: 'linear-gradient(to bottom, transparent 2%, black 14%, black 86%, transparent 98%)',
            }}
            onMouseMove={e => lensRef.current?.update(e.clientY)}
            onMouseLeave={restFade}
          >
            <div className="flex flex-col pb-[40vh] pt-[88px]">
              {names.map((n, i) => (
                <div key={n} data-row>
                  <button
                    onClick={() => navigate(`/${n}`)}
                    onMouseEnter={e => {
                      const r = e.currentTarget.getBoundingClientRect()
                      setHovered({ name: n, y: r.top + r.height / 2 })
                    }}
                    onMouseLeave={() => setHovered(null)}
                    className={`flex items-center text-left transition-colors ${
                      n === name ? 'text-sky-500' : 'text-neutral-400 hover:text-neutral-600'
                    }`}
                    style={{ paddingBlock: RAIL.rowGap, fontSize: RAIL.fontSize, gap: RAIL.labelGap }}
                  >
                    {n === name ? (
                      <span key="line" data-activeline className="h-px shrink-0 bg-sky-400" style={{ width: RAIL.tickActive }} />
                    ) : (
                      <span key="ticks" className="h-px shrink-0 bg-neutral-300" style={{ width: RAIL.tick }} />
                    )}
                    <span className="whitespace-nowrap">
                      {String(i + 1).padStart(2, '0')} {registry[i].title}
                    </span>
                  </button>
                </div>
              ))}
            </div>
          </div>
          {hovered && hovered.name !== name && (
            <Preview ck={ck} registry={registry} name={hovered.name}
                     index={names.indexOf(hovered.name)} y={hovered.y} />
          )}
        </nav>
      )}

      {/* bottom dock — skiper43-style icons menu with clip-path tooltip strip */}
      <div className="fixed bottom-6 left-1/2 z-20 -translate-x-1/2">
        <div ref={dockRef} onMouseLeave={dockLeave} className="relative">
          <div ref={dockTipParentRef} className="pointer-events-none absolute -top-11 left-0">
            <motion.div
              className="flex bg-[#4d5c96] text-white"
              style={{ opacity: tipOpacity, x: tipX, clipPath: tipClip }}
            >
              {DOCK_LABELS.map((l, i) => (
                <div
                  key={l}
                  ref={el => { if (el) dockTipRefs.current[i] = el }}
                  className="inline-flex h-8 items-center justify-center whitespace-nowrap px-3 text-[12px] font-medium leading-none tracking-tight"
                >
                  {l}
                </div>
              ))}
            </motion.div>
          </div>

          <div className="flex items-center gap-0.5 rounded-full border border-black/5 bg-white/90 py-1.5 pl-1.5 pr-2 shadow-[0_18px_44px_-18px_rgba(0,0,0,0.4)] backdrop-blur-sm">
            <span ref={el => { if (el) dockIconRefs.current[0] = el }} onMouseEnter={() => dockEnter(0)}>
              <PillAction fx="spin" onClick={() => setRunKey(k => k + 1)}>
                <IconRefresh />
              </PillAction>
            </span>
            <span ref={el => { if (el) dockIconRefs.current[1] = el }} onMouseEnter={() => dockEnter(1)}>
              <PillAction fx="dip" onClick={savePng}>
                <IconDownload />
              </PillAction>
            </span>
            <span ref={el => { if (el) dockIconRefs.current[2] = el }} onMouseEnter={() => dockEnter(2)}>
              <PillAction active={zen} onClick={() => setZen(z => !z)}>
                <IconWindowCode />
              </PillAction>
            </span>
            <span ref={el => { if (el) dockIconRefs.current[3] = el }} onMouseEnter={() => dockEnter(3)}>
              <PillAction href={`/?render=${name}`}>
                <IconArrowUpRight />
              </PillAction>
            </span>
            <span className="mx-1.5 h-5 w-px bg-neutral-200" />
            <button
              ref={el => { if (el) dockIconRefs.current[4] = el }}
              onClick={copyLink}
              onMouseEnter={() => dockEnter(4)}
              className="group flex items-center gap-2 rounded-full px-2.5 py-1.5 transition-colors duration-200 hover:bg-neutral-100"
            >
              <span className="font-mono text-[11px] tracking-tight text-neutral-400 transition-colors duration-200 group-hover:text-neutral-600">
                /{name}
              </span>
              <span className={`transition-colors duration-200 ${copied ? 'text-emerald-500' : 'text-neutral-400 group-hover:text-neutral-600'}`}>
                {copied ? <IconCheck /> : <IconCopy />}
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* film kind, bottom-left */}
      {!zen && (
        <p className="fixed bottom-7 left-6 z-10 text-[10px] leading-relaxed tracking-[0.18em] text-neutral-400">
          {group === 'reproductions' ? 'REPRODUCTION' : 'PRIMITIVE'} FILM
        </p>
      )}

      {/* credit */}
      <a
        href="https://x.com/Gur__vi"
        target="_blank"
        rel="noreferrer"
        className="fixed bottom-7 right-6 z-30 font-mono text-[10px] tracking-tight text-neutral-400 transition-colors hover:text-neutral-600"
      >
        layout inspired by @Gur__vi
      </a>

      {/* centered stage */}
      <main className="grid min-h-screen place-items-center">
        <div ref={mainRef} key={`${name}-${runKey}`} className="flex flex-col items-center">
          <div
            ref={stageRef}
            onDoubleClick={() => {
              setStageScale(1)
              setStagePan({ x: 0, y: 0 })
            }}
            className="cursor-grab active:cursor-grabbing"
            style={{
              width: stageW,
              transform: `translate(${stagePan.x}px, ${stagePan.y}px) scale(${stageScale})`,
              transformOrigin: 'center center',
              touchAction: 'none',
            }}
          >
            {doc
              ? <Film key={runKey} ck={ck} doc={doc}
                      className="h-auto w-full rounded-lg shadow-[0_1px_2px_rgba(0,0,0,0.06),0_12px_40px_rgba(0,0,0,0.1)]" />
              : <div style={{ aspectRatio: `${fw} / ${fh}` }}
                     className="w-full rounded-lg bg-black/5" />}
          </div>
        </div>
      </main>
    </div>
  )
}

export default function App() {
  const eng = useEngine()
  const [q] = useSearchParams()
  if (!eng)
    return (
      <div className="grid min-h-screen place-items-center bg-[#f4f4f3] text-neutral-400">
        whippan gallery — engine loading
      </div>
    )
  const { CK, registry } = eng
  const renderName = q.get('render')
  if (renderName) return <RenderRoute ck={CK} registry={registry} name={renderName} />
  return (
    <Routes>
      <Route path="/" element={<Home registry={registry} />} />
      <Route path="/:name" element={<Playground ck={CK} registry={registry} />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
