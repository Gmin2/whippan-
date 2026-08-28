import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { docDur, loadDoc } from '../engine'
import { createSound } from '../engine/sound'
import type { Sound } from '../engine/sound'
import type { Doc, Entry } from '../engine/types'
import Film from '../components/Film'
import Transport from '../components/Transport'
import DocPanel from '../components/DocPanel'
import { useFit } from '../useFit'

interface Props {
  ck: CanvasKit
  registry: Entry[]
}

const GROUP_LABEL: Record<string, string> = {
  films: 'our film',
  reproductions: 'reproduction',
  primitives: 'primitive',
}

export default function FilmPage({ ck, registry }: Props) {
  const { slug = '' } = useParams()
  const navigate = useNavigate()
  const entry = registry.find(e => e.slug === slug)
  const i = registry.findIndex(e => e.slug === slug)

  const [doc, setDoc] = useState<Doc | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [t, setT] = useState(0)
  const [playing, setPlaying] = useState(true)
  const [showDoc, setShowDoc] = useState(false)
  const sound = useRef<Sound | null>(null)
  const raf = useRef(0)

  useEffect(() => {
    if (entry) document.title = `${entry.title} · whippan`
  }, [entry])

  useEffect(() => {
    if (!entry) return
    let alive = true
    setDoc(null)
    setError(null)
    setT(0)
    setPlaying(true)
    loadDoc(entry).then(
      d => {
        if (!alive) return
        sound.current?.dispose()
        sound.current = createSound(d)
        setDoc(d)
      },
      err => { if (alive) setError(String(err)) },
    )
    return () => { alive = false; sound.current?.dispose() }
  }, [entry])

  const dur = doc ? docDur(doc.stage) : (entry?.dur ?? 1)

  // one clock drives the canvas and the score together
  useEffect(() => {
    if (!playing || !doc) return
    sound.current?.play(t)
    let last = performance.now()
    const tick = (now: number) => {
      const dt = (now - last) / 1000
      last = now
      setT(prev => {
        const next = prev + dt
        if (next >= dur) {
          sound.current?.loop(0)
          return next % dur
        }
        return next
      })
      raf.current = requestAnimationFrame(tick)
    }
    raf.current = requestAnimationFrame(tick)
    return () => {
      cancelAnimationFrame(raf.current)
      sound.current?.pause()
    }
  }, [playing, doc, dur])

  const seek = useCallback((v: number) => {
    const c = Math.min(dur, Math.max(0, v))
    sound.current?.seek(c)
    setT(c)
  }, [dur])

  const step = useCallback((frames: number) => {
    const fps = doc?.stage.fps ?? 30
    setPlaying(false)
    seek(t + frames / fps)
  }, [doc, seek, t])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement) return
      if (e.key === ' ') { e.preventDefault(); setPlaying(p => !p) }
      if (e.key === 'ArrowRight') { e.preventDefault(); step(e.shiftKey ? 10 : 1) }
      if (e.key === 'ArrowLeft') { e.preventDefault(); step(e.shiftKey ? -10 : -1) }
      if (e.key === 'Escape') navigate('/')
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [navigate, step])

  const [fw, fh] = entry?.size ?? [1920, 1080]
  const fit = useFit(fw, fh)

  if (!entry) return <Navigateaway />

  const prev = registry[(i - 1 + registry.length) % registry.length]
  const next = registry[(i + 1) % registry.length]

  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex items-center gap-5 px-8 py-5">
        <Link to="/" className="text-[15px] font-semibold tracking-[-0.02em]
                                transition-colors hover:text-flame">
          whippan
        </Link>
        <span className="h-3.5 w-px bg-hair" />
        <span className="label">{GROUP_LABEL[entry.group] ?? entry.group}</span>
        <h1 className="text-[13.5px]">{entry.title}</h1>

        <div className="ml-auto flex items-center gap-5">
          <span className="font-mono text-[10px] text-mute tabular-nums">
            {fw}×{fh} · {doc?.stage.fps ?? 30}fps · {dur.toFixed(2)}s
          </span>
          <button
            onClick={() => setShowDoc(s => !s)}
            className={`label transition-colors hover:text-ink ${showDoc ? 'text-flame' : ''}`}
          >
            {showDoc ? 'hide json' : 'the json'}
          </button>
        </div>
      </header>

      <span className="mx-8 block h-px bg-hair" />

      <main className="flex min-h-0 flex-1 items-stretch justify-center gap-8 px-8 py-10">
        <div ref={fit.ref}
             className="flex min-h-0 min-w-0 flex-1 flex-col items-center justify-center">
          <div
            className="overflow-hidden rounded-xl bg-letterbox
                       shadow-[0_2px_4px_rgba(0,0,0,0.05),0_24px_60px_-28px_rgba(0,0,0,0.5)]"
            style={{ width: fit.w, height: fit.h }}
          >
            {doc ? (
              <Film ck={ck} doc={doc} t={t} className="h-full w-full" />
            ) : (
              <div className="grid h-full place-items-center">
                <span className="label">{error ?? 'loading film'}</span>
              </div>
            )}
          </div>

          <Transport
            t={t} dur={dur} playing={playing}
            onToggle={() => setPlaying(p => !p)}
            onSeek={v => { setPlaying(false); seek(v) }}
          />
        </div>

        {showDoc && doc && <DocPanel doc={doc} t={t} />}
      </main>

      <footer className="flex items-center justify-between px-8 py-6">
        <Link to={`/${prev.slug}`} className="label transition-colors hover:text-ink">
          ← {prev.title}
        </Link>
        <span className="font-mono text-[10px] text-mute tabular-nums">
          {String(i + 1).padStart(2, '0')} / {registry.length}
        </span>
        <Link to={`/${next.slug}`} className="label transition-colors hover:text-ink">
          {next.title} →
        </Link>
      </footer>
    </div>
  )
}

function Navigateaway() {
  const navigate = useNavigate()
  useEffect(() => { navigate('/', { replace: true }) }, [navigate])
  return null
}
