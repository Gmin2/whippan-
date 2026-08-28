import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { ChevronDown } from '../icons'
import type { Entry } from '../engine/types'

interface Props {
  registry: Entry[]
  current: string
  onPick(slug: string): void
}

const GROUPS: { key: string; label: string }[] = [
  { key: 'films', label: 'our films' },
  { key: 'reproductions', label: 'reproductions' },
  { key: 'primitives', label: 'primitives' },
]

/** the file name is the document switcher: 37 films live in one registry */
export default function FilmMenu({ registry, current, onPick }: Props) {
  const btn = useRef<HTMLButtonElement>(null)
  const [open, setOpen] = useState(false)
  const [at, setAt] = useState({ x: 0, y: 0 })
  const entry = registry.find(e => e.slug === current)

  useEffect(() => {
    if (!open || !btn.current) return
    const r = btn.current.getBoundingClientRect()
    setAt({ x: r.left, y: r.bottom + 4 })
    const away = (e: MouseEvent) => {
      if (!btn.current?.contains(e.target as HTMLElement)) setOpen(false)
    }
    const id = setTimeout(() => document.addEventListener('pointerdown', away), 0)
    return () => { clearTimeout(id); document.removeEventListener('pointerdown', away) }
  }, [open])

  return (
    <>
      <button ref={btn} onClick={() => setOpen(o => !o)}
              className="flex min-w-0 flex-1 items-center gap-1.5 text-left">
        <span className="truncate font-medium">{entry?.title ?? current}</span>
        <ChevronDown size={9} className="shrink-0 text-faint" />
      </button>
      {open && createPortal(
        <div
          className="fixed z-[100] max-h-[70vh] w-[260px] overflow-y-auto rounded-[10px]
                     border border-black/10 bg-panel py-1
                     shadow-[0_16px_50px_-12px_rgba(0,0,0,0.45)]"
          style={{ left: at.x, top: at.y }}
          onPointerDown={e => e.stopPropagation()}
        >
          {GROUPS.map(g => {
            const films = registry.filter(e => e.group === g.key)
            if (!films.length) return null
            return (
              <div key={g.key}>
                <p className="px-3 pb-1 pt-2 text-[10px] uppercase tracking-[0.14em] text-faint">
                  {g.label}
                </p>
                {films.map(f => (
                  <button
                    key={f.slug}
                    onClick={() => { onPick(f.slug); setOpen(false) }}
                    className={`flex h-[26px] w-full items-center gap-2 px-3 text-left
                                ${f.slug === current ? 'bg-row' : 'hover:bg-black/[0.035]'}`}
                  >
                    <span className="truncate">{f.title}</span>
                    <span className="ml-auto shrink-0 font-mono text-[10px] text-faint">
                      {f.dur}s
                    </span>
                  </button>
                ))}
              </div>
            )
          })}
        </div>,
        document.body,
      )}
    </>
  )
}
