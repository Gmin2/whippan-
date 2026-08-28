import { useState } from 'react'
import ColorPicker from './ColorPicker'

interface Props {
  hex: string
  alpha: number
  onChange(hex: string, alpha: number): void
}

/** a hex swatch that opens the picker beside the panel */
export default function ColorRow({ hex, alpha, onChange }: Props) {
  const [open, setOpen] = useState(false)
  const flat = hex.replace('#', '').toUpperCase()
  return (
    <div className="relative">
      <button
        onClick={() => setOpen(o => !o)}
        className={`inset-control flex h-[26px] w-full items-center gap-2 px-2
                    transition-colors hover:bg-black/[0.02]
                    ${open ? 'border-[#2d52f0] ring-2 ring-[#2d52f0]/25' : ''}`}
      >
        <span className="h-3.5 w-3.5 shrink-0 rounded-[3px] border border-black/15"
              style={{ background: hex, opacity: alpha }} />
        <span className="tabular-nums">{flat}</span>
        <span className="ml-auto text-dim tabular-nums">{Math.round(alpha * 100)} %</span>
      </button>
      {open && (
        <div className="absolute right-[calc(100%+16px)] top-0 z-50">
          <ColorPicker hex={flat} alpha={alpha} onClose={() => setOpen(false)}
                       onChange={(h, a) => onChange('#' + h, a)} />
        </div>
      )}
    </div>
  )
}
