import type { Artboard, Board } from '../doc'

interface Props {
  board: Board
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

/** the white value field paper uses for every property row */
function Field({ children }: { children: React.ReactNode }) {
  return (
    <div className="inset-control flex h-[26px] items-center gap-2 px-2">{children}</div>
  )
}

export default function RightPanel({ board, zoom, selection }: Props) {
  return (
    <aside className="flex h-full w-inspector shrink-0 flex-col border-l border-hair bg-panel">
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
          <Section label="Artboard">
            <div className="grid grid-cols-2 gap-1.5">
              <Field><span className="text-faint">W</span><span className="tabular-nums">{selection.w}</span></Field>
              <Field><span className="text-faint">H</span><span className="tabular-nums">{selection.h}</span></Field>
            </div>
          </Section>
          <Section label="Timing">
            <div className="grid grid-cols-2 gap-1.5">
              <Field><span className="text-faint">Dur</span><span className="tabular-nums">{selection.dur.toFixed(2)}s</span></Field>
              <Field><span className="text-faint">ID</span><span className="truncate font-mono text-[11px]">{selection.id}</span></Field>
            </div>
          </Section>
          <Section label="Note">
            <p className="leading-relaxed text-dim">{selection.note}</p>
          </Section>
        </>
      ) : (
        <Section label="Page">
          <Field>
            <span className="h-3.5 w-3.5 rounded-[3px] border border-black/10"
                  style={{ background: board.ground }} />
            <span className="uppercase">{board.ground.replace('#', '')}</span>
            <span className="ml-auto text-dim tabular-nums">100 %</span>
          </Field>
        </Section>
      )}

      {!selection && (
        <p className="px-3 py-4 leading-relaxed text-faint">
          Select an artboard on the canvas or in the layer list.
        </p>
      )}
    </aside>
  )
}
