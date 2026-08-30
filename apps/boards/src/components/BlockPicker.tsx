import { useEffect, useMemo, useState } from 'react'
import { BLOCKS, SCALE } from '../blocks'
import type { Block } from '../blocks'

interface Props {
  /** the film's hue, shown so you can see what accent a block will take */
  accent: string
  onInsert(key: string, opts: Record<string, unknown>): void
  onClose(): void
}

const ROLES = [
  { key: 'accent', label: 'accent' },
  { key: 'ink', label: 'ink' },
  { key: 'tint', label: 'tint' },
]

/**
 * Placing a block.
 *
 * The list is the vocabulary the 31 films actually use, so the blurb on each
 * one carries the measured rule rather than a description. That is the teaching
 * surface: you learn that a pill's label is 0.47 of its height by reading it on
 * the way to using it, not from a document.
 */
export default function BlockPicker({ accent, onInsert, onClose }: Props) {
  const [pick, setPick] = useState<Block | null>(null)
  const [opts, setOpts] = useState<Record<string, unknown>>({})

  useEffect(() => {
    const key = (e: KeyboardEvent) => { if (e.key === 'Escape') { e.stopPropagation(); onClose() } }
    window.addEventListener('keydown', key, true)
    return () => window.removeEventListener('keydown', key, true)
  }, [onClose])

  // every slot starts at its measured default, so Insert alone gives something
  // already in the house style
  const defaults = useMemo(() => {
    if (!pick) return {}
    const o: Record<string, unknown> = {}
    for (const s of pick.slots) o[s.key] = s.def
    return o
  }, [pick])

  const choose = (b: Block) => { setPick(b); setOpts({}) }
  const val = (k: string) => (k in opts ? opts[k] : defaults[k])
  const set = (k: string, v: unknown) => setOpts(o => ({ ...o, [k]: v }))

  return (
    <div className="fixed inset-0 z-[130] grid place-items-center bg-black/25"
         onPointerDown={onClose}>
      <div onPointerDown={e => e.stopPropagation()}
           className="flex h-[440px] w-[560px] overflow-hidden rounded-[12px] border
                      border-black/10 bg-panel shadow-[0_24px_60px_-16px_rgba(0,0,0,0.5)]">

        <div className="w-[228px] shrink-0 overflow-y-auto border-r border-hair">
          <div className="flex items-center gap-2 border-b border-hair px-3 py-2.5">
            <p className="font-medium">Blocks</p>
            <span className="ml-auto flex items-center gap-1.5 text-[10px] text-faint">
              accent
              <span className="h-3 w-3 rounded-[3px] border border-black/10"
                    style={{ background: accent }} />
            </span>
          </div>
          {BLOCKS.map(b => (
            <button
              key={b.key}
              onClick={() => choose(b)}
              className={`block w-full px-3 py-2 text-left transition-colors
                          ${pick?.key === b.key ? 'bg-black/[0.055]' : 'hover:bg-black/[0.03]'}`}
            >
              <span className="block">{b.name}</span>
              <span className="mt-0.5 block leading-relaxed text-[10px] text-faint">{b.blurb}</span>
            </button>
          ))}
        </div>

        <div className="flex min-w-0 flex-1 flex-col">
          <div className="flex items-center gap-2 border-b border-hair px-3 py-2.5">
            <p className="truncate font-medium">{pick ? pick.name : 'pick a block'}</p>
            <button onClick={onClose}
                    className="ml-auto text-dim transition-colors hover:text-ink">✕</button>
          </div>

          {!pick ? (
            <p className="p-3 leading-relaxed text-dim">
              Every number in these comes from the 31 authored films, not from a
              style guide. A block lands as one group, so a single track animates
              the whole thing.
            </p>
          ) : (
            <>
              <div className="min-h-0 flex-1 space-y-2.5 overflow-y-auto p-3">
                {pick.slots.map(s => (
                  <div key={s.key}>
                    <p className="mb-1 text-[10px] uppercase tracking-[0.14em] text-faint">
                      {s.label}
                    </p>
                    {s.kind === 'text' && (
                      <input
                        value={String(val(s.key) ?? '')}
                        onChange={e => set(s.key, e.target.value)}
                        className="inset-control h-[28px] w-full bg-surface px-2 outline-none"
                      />
                    )}
                    {s.kind === 'lines' && (
                      <textarea
                        rows={4}
                        value={(val(s.key) as string[] | string) instanceof Array
                          ? (val(s.key) as string[]).join('\n')
                          : String(val(s.key) ?? '')}
                        onChange={e => set(s.key, e.target.value)}
                        className="inset-control w-full resize-none bg-surface px-2 py-1.5
                                   leading-relaxed outline-none"
                      />
                    )}
                    {s.kind === 'role' && (
                      <div className="grid grid-cols-3 gap-1.5">
                        {ROLES.map(r => (
                          <button
                            key={r.key}
                            onClick={() => set(s.key, r.key)}
                            className={`h-[26px] rounded-[5px] border text-[11px] transition-colors
                                        ${val(s.key) === r.key
                                          ? 'border-[#5e92f4] bg-[#5e92f4]/12 text-[#2f6ad4]'
                                          : 'border-hair bg-surface text-dim hover:text-ink'}`}
                          >
                            {r.label}
                          </button>
                        ))}
                      </div>
                    )}
                    {s.kind === 'tier' && (
                      <div className="flex items-center gap-2">
                        <input
                          type="range" min={0} max={SCALE.length - 1} step={1}
                          value={Number(val(s.key) ?? 4)}
                          onChange={e => set(s.key, Number(e.target.value))}
                          className="min-w-0 flex-1"
                        />
                        <span className="w-[54px] shrink-0 text-right font-mono text-[11px]
                                         tabular-nums text-dim">
                          {SCALE[Number(val(s.key) ?? 4)]} px
                        </span>
                      </div>
                    )}
                  </div>
                ))}
                <p className="pt-1 leading-relaxed text-[10px] text-faint">
                  sizes are given for a 1920 canvas and scale with the film
                </p>
              </div>

              <div className="flex items-center gap-2 border-t border-hair px-3 py-2.5">
                <p className="text-[10px] text-faint">lands centred on the scene</p>
                <button
                  onClick={() => onInsert(pick.key, { ...defaults, ...opts })}
                  className="ml-auto h-[28px] rounded-[6px] bg-[#5e92f4] px-3 text-white
                             transition-colors hover:bg-[#4d82e8]"
                >
                  Insert
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
