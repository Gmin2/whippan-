import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { cachedPoster, loadDoc, queuePoster } from '../engine'
import type { Doc, Entry } from '../engine/types'
import Film from './Film'

interface Props {
  ck: CanvasKit
  entry: Entry
  /** position in the full registry, so the wall and the film rail agree */
  index: number
}

// A film on the wall. The still is cut by the engine once it scrolls into
// range; pointing at the card loads the doc and hands the same frame over to
// a live canvas, so hovering is the film actually running, not a preview mp4.
export default function FilmCard({ ck, entry, index }: Props) {
  const ref = useRef<HTMLAnchorElement>(null)
  const [poster, setPoster] = useState<string | undefined>(() => cachedPoster(entry.slug))
  const [doc, setDoc] = useState<Doc | null>(null)
  const [live, setLive] = useState(false)

  useEffect(() => {
    if (poster || !ref.current) return
    let alive = true
    const io = new IntersectionObserver(([e]) => {
      if (!e.isIntersecting) return
      io.disconnect()
      queuePoster(ck, entry).then(url => { if (alive && url) setPoster(url) })
    }, { rootMargin: '300px' })
    io.observe(ref.current)
    return () => { alive = false; io.disconnect() }
  }, [ck, entry, poster])

  const enter = () => {
    setLive(true)
    if (!doc) loadDoc(entry).then(setDoc, () => {})
  }

  const showFilm = live && doc

  return (
    <Link
      ref={ref}
      to={`/${entry.slug}`}
      onMouseEnter={enter}
      onMouseLeave={() => setLive(false)}
      className="group block"
    >
      <div
        className="relative overflow-hidden rounded-[10px] bg-letterbox ring-1
                   ring-black/[0.07] transition-[transform,box-shadow] duration-300
                   ease-out group-hover:-translate-y-[3px]
                   group-hover:shadow-[0_18px_40px_-20px_rgba(0,0,0,0.45)]"
        style={{ aspectRatio: '16 / 10' }}
      >
        <div className="absolute inset-0 grid place-items-center">
          {showFilm ? (
            <Film ck={ck} doc={doc} className="max-h-full max-w-full" />
          ) : poster ? (
            <img src={poster} alt="" className="max-h-full max-w-full" />
          ) : (
            <span className="label opacity-40">cutting frame</span>
          )}
        </div>

        {/* the film's own clock, running only while the card is live */}
        <span className="absolute inset-x-0 bottom-0 h-px bg-black/[0.06]">
          {showFilm && (
            <span
              className="block h-px bg-flame"
              style={{ animation: `sweep ${entry.dur}s linear infinite` }}
            />
          )}
        </span>
      </div>

      <div className="mt-2.5 flex items-baseline gap-2.5">
        <span className="font-mono text-[10px] text-mute tabular-nums">
          {String(index + 1).padStart(2, '0')}
        </span>
        <span className="text-[13.5px] leading-none text-ink transition-colors
                         group-hover:text-flame">
          {entry.title}
        </span>
        <span className="ml-auto font-mono text-[10px] text-mute tabular-nums">
          {entry.dur}s
        </span>
      </div>
    </Link>
  )
}
