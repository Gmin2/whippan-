import ColorRow from './ColorRow'
import Inspector from './Inspector'
import NumField from './NumField'
import type { Artboard, NodePatch, ScenePatch } from '../doc'
import type { Node } from '../engine/types'
import type { NodeBox } from '../measure'

interface Props {
  ground: string
  groundAlpha: number
  onGround(hex: string, alpha: number): void
  zoom: number
  selection: Artboard | null
  node: Node | null
  nodeBox: NodeBox | null
  canvas: [number, number]
  onPatch(id: string, patch: ScenePatch): void
  onPatchNode(patch: NodePatch): void
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

/** the white value field, in its read-only form */
function Field({ children }: { children: React.ReactNode }) {
  return <div className="inset-control flex h-[26px] items-center gap-2 px-2">{children}</div>
}

export default function RightPanel({
  ground, groundAlpha, onGround, zoom, selection, node, nodeBox, canvas,
  onPatch, onPatchNode,
}: Props) {
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

      <div className="min-h-0 flex-1 overflow-y-auto">
        {node ? (
          <Inspector node={node} box={nodeBox} canvas={canvas} onPatch={onPatchNode} />
        ) : selection ? (
          <>
            <Section label="Scene">
              <div className="grid grid-cols-2 gap-1.5">
                <input
                  defaultValue={selection.id}
                  key={selection.id}
                  onBlur={e => {
                    const v = e.target.value.trim()
                    if (v && v !== selection.id) onPatch(selection.id, { id: v })
                  }}
                  onKeyDown={e => { if (e.key === 'Enter') (e.target as HTMLInputElement).blur() }}
                  className="inset-control h-[26px] min-w-0 px-2 font-mono text-[11px] outline-none
                             focus:border-[#2d52f0] focus:ring-2 focus:ring-[#2d52f0]/25"
                />
                <Field><span className="text-faint">No</span>
                  <span className="ml-auto tabular-nums">{selection.label}</span></Field>
              </div>
            </Section>

            <Section label="Timing">
              <div className="grid grid-cols-2 gap-1.5">
                <Field><span className="text-faint">In</span>
                  <span className="ml-auto tabular-nums">{selection.start.toFixed(2)}s</span></Field>
                <NumField
                  label="Dur" value={selection.dur} precision={2} step={0.05} min={0.05}
                  onChange={v => onPatch(selection.id, { dur: v })}
                />
              </div>
            </Section>

            <Section label="Background">
              <div className="relative">
                <ColorRow
                  hex={selection.bg ?? '#ffffff'}
                  alpha={1}
                  onChange={h => onPatch(selection.id, { bg: h })}
                />
              </div>
            </Section>

            <Section label="Note">
              <textarea
                key={selection.id}
                defaultValue={selection.note}
                onBlur={e => onPatch(selection.id, { note: e.target.value })}
                rows={4}
                className="inset-control w-full resize-none px-2 py-1.5 leading-relaxed
                           outline-none focus:border-[#2d52f0] focus:ring-2 focus:ring-[#2d52f0]/25"
              />
            </Section>

            <Section label="Frame">
              <div className="grid grid-cols-2 gap-1.5">
                <Field><span className="text-faint">W</span>
                  <span className="ml-auto tabular-nums">{selection.w}</span></Field>
                <Field><span className="text-faint">H</span>
                  <span className="ml-auto tabular-nums">{selection.h}</span></Field>
              </div>
              <p className="mt-1.5 text-[10px] text-faint">
                canvas size is set on the document, not per scene
              </p>
            </Section>
          </>
        ) : (
          <Section label="Page">
            <div className="relative">
              <ColorRow hex={ground} alpha={groundAlpha} onChange={onGround} />
            </div>
          </Section>
        )}
      </div>
    </aside>
  )
}
