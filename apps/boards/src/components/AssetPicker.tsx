import { useEffect, useState } from 'react'
import { listAssets } from '../engine'
import type { Asset } from '../engine/types'

interface Props {
  onPick(asset: Asset): void
  onClose(): void
}

const kb = (n: number) => (n > 1_000_000 ? `${(n / 1e6).toFixed(1)} MB` : `${Math.round(n / 1000)} KB`)

/**
 * The images a document can reference. Paper's counterpart generates one with a
 * model; ours picks from the assets the films already ship, which is what an
 * editor over a repo actually needs.
 */
export default function AssetPicker({ onPick, onClose }: Props) {
  const [assets, setAssets] = useState<Asset[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [q, setQ] = useState('')

  useEffect(() => {
    listAssets().then(setAssets, e => setError(String(e)))
  }, [])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const shown = (assets ?? []).filter(a =>
    a.src.toLowerCase().includes(q.trim().toLowerCase()))

  return (
    <div className="fixed inset-0 z-[120] grid place-items-center bg-black/25"
         onPointerDown={onClose}>
      <div
        onPointerDown={e => e.stopPropagation()}
        className="flex max-h-[70vh] w-[560px] flex-col overflow-hidden rounded-[12px]
                   border border-black/10 bg-panel
                   shadow-[0_24px_60px_-16px_rgba(0,0,0,0.5)]"
      >
        <div className="flex items-center gap-2 border-b border-hair px-3 py-2.5">
          <p className="font-medium">Insert image</p>
          <input
            autoFocus
            value={q}
            onChange={e => setQ(e.target.value)}
            placeholder="filter"
            className="inset-control ml-auto h-[26px] w-[180px] px-2 outline-none
                       focus:border-[#5e92f4] focus:ring-2 focus:ring-[#5e92f4]/25"
          />
          <button onClick={onClose} className="text-dim hover:text-ink">✕</button>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto p-3">
          {error && <p className="text-[#c0392b]">{error}</p>}
          {!assets && !error && <p className="text-dim">loading assets…</p>}
          {assets && !shown.length && <p className="text-dim">nothing matches</p>}
          <div className="grid grid-cols-3 gap-2.5">
            {shown.map(a => {
              const seq = a.src.endsWith('/')
              return (
                <button
                  key={a.src}
                  onClick={() => { onPick(a); onClose() }}
                  className="group overflow-hidden rounded-[8px] border border-black/10
                             bg-surface text-left transition-shadow
                             hover:shadow-[0_6px_18px_-8px_rgba(0,0,0,0.45)]"
                >
                  <div className="grid h-[92px] place-items-center overflow-hidden bg-letterbox">
                    {seq
                      ? <span className="label">frame sequence</span>
                      : <img src={a.src} alt="" className="max-h-full max-w-full" />}
                  </div>
                  <div className="px-2 py-1.5">
                    <p className="truncate text-[11px]">{a.src.split('/').filter(Boolean).pop()}</p>
                    <p className="text-[10px] text-faint">{seq ? 'seq' : kb(a.bytes)}</p>
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
