import { useState } from 'react'
import ColorPicker from './ColorPicker'
import type { Artboard } from '../doc'

interface Props {
  ground: string
  groundAlpha: number
  onGround(hex: string, alpha: number): void
  zoom: number
  selection: Artboard | null
}

const PEERS = [
  { initial: 'b', bg: '#f4622a' },
  { initial: 'b', bg: '#ef5136' },
  { initial: 'A', bg: '#d6407f' },
]

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="border-b border-hair px-3 py-3">
      <p className="mb-2 font-medium">{label}</p>
      {children}
    </div>
  )
}

/** the white value field used for every property row */
function Field({ children }: { children: React.ReactNode }) {
  return <div className="inset-control flex h-[26px] items-center gap-2 px-2">{children}</div>
}

export default function RightPanel({
  ground, groundAlpha, onGround, zoom, selection,
}: Props) {
  const [picking, setPicking] = useState(false)
  const hex = ground.replace('#', '').toUpperCase()

  return (
    <aside className="relative flex h-full w-inspector shrink-0 flex-col border-l
                      border-hair bg-panel">
      <div className="flex h-[41px] shrink-0 items-center px-3">
        <div className="flex">
          {PEERS.map((p, i) => (
            <span
              key={i}
              className="grid h-[22px] w-[22px] place-items-center rounded-full
                         text-[11px] font-medium text-white ring-2 ring-panel"
              style={{ background: p.bg, marginLeft: i ? -6 : 0 }}
            >
              {p.initial}
            </span>
          ))}
        </div>
        <span className="ml-auto text-dim tabular-nums">{Math.round(zoom * 100)}%</span>
      </div>

      <div className="px-3 pb-3">
        <button className="inset-control flex h-[30px] w-full items-center justify-center gap-2
                           transition-colors hover:bg-black/[0.02]">
          <span>Copy link</span>
          <span className="text-faint">⌘L</span>
        </button>
      </div>

      {selection ? (
        <>
          <Section label="Scene">
            <div className="grid grid-cols-2 gap-1.5">
              <Field><span className="text-faint">ID</span>
                <span className="truncate font-mono text-[11px]">{selection.id}</span></Field>
              <Field><span className="text-faint">No</span>
                <span className="tabular-nums">{selection.label}</span></Field>
            </div>
          </Section>
          <Section label="Frame">
            <div className="grid grid-cols-2 gap-1.5">
              <Field><span className="text-faint">W</span>
                <span className="tabular-nums">{selection.w}</span></Field>
              <Field><span className="text-faint">H</span>
                <span className="tabular-nums">{selection.h}</span></Field>
            </div>
          </Section>
          <Section label="Timing">
            <div className="grid grid-cols-2 gap-1.5">
              <Field><span className="text-faint">In</span>
                <span className="tabular-nums">{selection.start.toFixed(2)}s</span></Field>
              <Field><span className="text-faint">Dur</span>
                <span className="tabular-nums">{selection.dur.toFixed(2)}s</span></Field>
            </div>
          </Section>
          <Section label="Note">
            <p className="leading-relaxed text-dim">{selection.note}</p>
          </Section>
        </>
      ) : (
        <Section label="Page">
          <button
            onClick={() => setPicking(p => !p)}
            className="inset-control flex h-[26px] w-full items-center gap-2 px-2
                       transition-colors hover:bg-black/[0.02]"
          >
            <span className="h-3.5 w-3.5 shrink-0 rounded-[3px] border border-black/15"
                  style={{ background: ground, opacity: groundAlpha }} />
            <span className="tabular-nums">{hex}</span>
            <span className="ml-auto text-dim tabular-nums">
              {Math.round(groundAlpha * 100)} %
            </span>
          </button>
        </Section>
      )}

      {picking && (
        <div className="absolute right-[calc(100%+8px)] top-[92px] z-50">
          <ColorPicker
            hex={hex}
            alpha={groundAlpha}
            onChange={(h, a) => onGround('#' + h, a)}
            onClose={() => setPicking(false)}
          />
        </div>
      )}
    </aside>
  )
}
