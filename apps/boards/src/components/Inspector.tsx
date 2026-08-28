import { useState } from 'react'
import NumField from './NumField'
import ColorRow from './ColorRow'
import type { Node } from '../engine/types'
import type { NodePatch } from '../doc'
import type { NodeBox } from '../measure'

interface Props {
  node: Node
  box: NodeBox | null
  /** the scene canvas, which is what the align buttons align against */
  canvas: [number, number]
  onPatch(patch: NodePatch): void
}

function Section({ label, children, right }: {
  label: string
  children: React.ReactNode
  right?: React.ReactNode
}) {
  return (
    <div className="border-b border-hair px-3 py-3">
      <div className="mb-2 flex items-center">
        <p className="font-medium">{label}</p>
        {right && <div className="ml-auto flex items-center gap-1">{right}</div>}
      </div>
      {children}
    </div>
  )
}

/** the collapsed "+" rows paper shows for sections that are not applied yet */
function AddRow({ label, onAdd, hint }: {
  label: string
  onAdd?(): void
  hint?: string
}) {
  return (
    <button
      onClick={onAdd}
      disabled={!onAdd}
      title={hint}
      className={`flex h-[42px] w-full items-center border-b border-hair px-3
                  ${onAdd ? 'hover:bg-black/[0.02]' : 'cursor-default'}`}
    >
      <span className={onAdd ? 'text-ink' : 'text-faint'}>{label}</span>
      <span className={`ml-auto ${onAdd ? 'text-dim' : 'text-faint/50'}`}>+</span>
    </button>
  )
}

const Pair = ({ children }: { children: React.ReactNode }) => (
  <div className="grid grid-cols-2 gap-1.5">{children}</div>
)

const Trio = ({ children }: { children: React.ReactNode }) => (
  <div className="grid grid-cols-3 gap-1.5">{children}</div>
)

const ALIGN = [
  { key: 'left', d: 'M2 2v12M5 5h8M5 10h5' },
  { key: 'hcentre', d: 'M8 2v12M4 5h8M6 10h4' },
  { key: 'right', d: 'M14 2v12M3 5h8M6 10h5' },
  { key: 'top', d: 'M2 2h12M5 5v8M10 5v5' },
  { key: 'vcentre', d: 'M2 8h12M5 4v8M10 6v4' },
  { key: 'bottom', d: 'M2 14h12M5 3v8M10 6v5' },
] as const

export default function Inspector({ node, box, canvas, onPatch }: Props) {
  const isText = node.type === 'text'
  const [cw, ch] = canvas
  const [fillTab, setFillTab] = useState<'solid' | 'gradient' | 'image'>(
    node.gradient ? 'gradient' : node.src ? 'image' : 'solid')

  // the painted box is the truth for alignment: a text node has no w/h
  const w = node.w ?? box?.w ?? 0
  const h = node.h ?? box?.h ?? 0
  const opacity = node.keys?.opacity?.[0]?.v ?? 1

  const align = (key: string) => {
    if (key === 'left') onPatch({ x: Math.round(w / 2) })
    if (key === 'hcentre') onPatch({ x: Math.round(cw / 2) })
    if (key === 'right') onPatch({ x: Math.round(cw - w / 2) })
    if (key === 'top') onPatch({ y: Math.round(h / 2) })
    if (key === 'vcentre') onPatch({ y: Math.round(ch / 2) })
    if (key === 'bottom') onPatch({ y: Math.round(ch - h / 2) })
  }

  return (
    <>
      <Section
        label="Layout"
        right={ALIGN.map(a => (
          <button key={a.key} onClick={() => align(a.key)} title={a.key}
                  className="grid h-5 w-5 place-items-center text-dim
                             transition-colors hover:text-ink">
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none"
                 stroke="currentColor" strokeWidth="1.4" strokeLinecap="round">
              <path d={a.d} />
            </svg>
          </button>
        ))}
      >
        <Trio>
          <NumField label="X" value={node.x ?? 0} onChange={v => onPatch({ x: Math.round(v) })} />
          <NumField label="Y" value={node.y ?? 0} onChange={v => onPatch({ y: Math.round(v) })} />
          <NumField label="∠" value={node.rot ?? 0} step={1} suffix="°"
                    onChange={v => onPatch({ rot: v })} />
        </Trio>
        {!isText && (
          <div className="mt-1.5">
            <Pair>
              <NumField label="W" value={node.w ?? 0} min={1}
                        onChange={v => onPatch({ w: Math.round(v) })} />
              <NumField label="H" value={node.h ?? 0} min={1}
                        onChange={v => onPatch({ h: Math.round(v) })} />
            </Pair>
          </div>
        )}
        <p className="mt-1.5 text-[10px] text-faint">
          x,y is the node centre{isText && '; text sizes itself from the type'}
        </p>
      </Section>

      {!isText && (
        <Section label="Radius">
          <div className="flex items-center gap-2">
            <input
              type="range" min={0} max={Math.round(Math.min(w, h) / 2) || 200}
              value={node.radius ?? 0}
              onChange={e => onPatch({ radius: Number(e.target.value) })}
              className="h-1 flex-1 accent-[#2d52f0]"
            />
            <div className="w-[74px]">
              <NumField value={node.radius ?? 0} min={0}
                        onChange={v => onPatch({ radius: Math.round(v) })} />
            </div>
          </div>
        </Section>
      )}

      <Section label="Blending">
        <Pair>
          <NumField label="%" value={Math.round(opacity * 100)} min={0} max={100}
                    onChange={v => onPatch({ opacity: v / 100 })} />
          <div className="inset-control flex h-[26px] items-center px-2 text-faint">
            Normal
          </div>
        </Pair>
        <p className="mt-1.5 text-[10px] text-faint">
          the renderer has one blend mode
        </p>
      </Section>

      <Section label="Fill">
        <div className="mb-1.5 flex rounded-[6px] bg-black/[0.05] p-[2px]">
          {(['solid', 'gradient', 'image'] as const).map(k => (
            <button
              key={k}
              disabled={k === 'image' && node.type !== 'image'}
              onClick={() => {
                setFillTab(k)
                if (k === 'solid') onPatch({ gradient: null })
                if (k === 'gradient' && !node.gradient) {
                  onPatch({
                    gradient: {
                      angle: 90,
                      stops: [
                        { at: 0, color: node.fill ?? '#2d52f0' },
                        { at: 1, color: '#000000' },
                      ],
                    },
                  })
                }
              }}
              className={`h-[24px] flex-1 rounded-[4px] capitalize transition-colors
                          ${fillTab === k
                            ? 'bg-surface font-medium shadow-[0_1px_2px_rgba(0,0,0,0.07)]'
                            : 'text-dim enabled:hover:text-ink disabled:text-faint/60'}`}
            >
              {k}
            </button>
          ))}
        </div>

        {fillTab === 'gradient' && node.gradient ? (
          <div className="flex flex-col gap-1.5">
            <NumField label="Angle" value={node.gradient.angle ?? 0} step={1} suffix="°"
                      onChange={v => onPatch({
                        gradient: { ...node.gradient!, angle: v },
                      })} />
            {node.gradient.stops.map((st, i) => (
              <ColorRow
                key={i}
                hex={st.color}
                alpha={1}
                onChange={hex => onPatch({
                  gradient: {
                    ...node.gradient!,
                    stops: node.gradient!.stops.map((o, k) =>
                      k === i ? { ...o, color: hex } : o),
                  },
                })}
              />
            ))}
          </div>
        ) : fillTab === 'image' ? (
          <div className="inset-control flex h-[26px] items-center gap-2 px-2">
            <span className="truncate font-mono text-[10px]">{node.src ?? 'no source'}</span>
          </div>
        ) : (
          <ColorRow
            hex={(isText ? node.color : node.fill) ?? '#000000'}
            alpha={1}
            onChange={hex => onPatch(isText ? { color: hex } : { fill: hex })}
          />
        )}
      </Section>

      {isText && (
        <Section label="Text">
          <textarea
            key={node.id}
            defaultValue={node.text ?? ''}
            rows={2}
            onBlur={e => onPatch({ text: e.target.value })}
            className="inset-control mb-1.5 w-full resize-none px-2 py-1.5 leading-relaxed
                       outline-none focus:border-[#2d52f0] focus:ring-2 focus:ring-[#2d52f0]/25"
          />
          <select
            value={node.font?.family ?? 'inter'}
            onChange={e => onPatch({ fontFamily: e.target.value })}
            className="inset-control mb-1.5 h-[26px] w-full px-1.5 outline-none"
          >
            <option value="inter">Inter</option>
            <option value="mono">JetBrains Mono</option>
          </select>
          <Pair>
            <select
              value={node.font?.weight ?? 400}
              onChange={e => onPatch({ fontWeight: Number(e.target.value) })}
              className="inset-control h-[26px] w-full px-1.5 outline-none"
            >
              {[100, 200, 300, 400, 500, 600, 700, 800, 900].map(w2 => (
                <option key={w2} value={w2}>{w2}</option>
              ))}
            </select>
            <NumField label="Size" value={node.font?.size ?? 48} min={4}
                      onChange={v => onPatch({ fontSize: Math.round(v) })} />
          </Pair>
          <p className="mt-1.5 text-[10px] text-faint">
            one text node is one line; inter is variable 100-900
          </p>
        </Section>
      )}

      {/* shadow is the engine's glow: a blurred echo behind the body */}
      {node.glow ? (
        <Section
          label="Shadow"
          right={
            <button onClick={() => onPatch({ glow: null })}
                    className="text-dim hover:text-ink">−</button>
          }
        >
          <div className="mb-1.5">
            <ColorRow hex={node.glow.color ?? node.fill ?? '#000000'} alpha={node.glow.opacity ?? 1}
                      onChange={(hex, a) => onPatch({
                        glow: { ...node.glow!, color: hex, opacity: a },
                      })} />
          </div>
          <Trio>
            <NumField label="X" value={node.glow.dx ?? 0}
                      onChange={v => onPatch({ glow: { ...node.glow!, dx: v } })} />
            <NumField label="Y" value={node.glow.dy ?? 0}
                      onChange={v => onPatch({ glow: { ...node.glow!, dy: v } })} />
            <NumField label="B" value={node.glow.sigma ?? 20} min={0}
                      onChange={v => onPatch({ glow: { ...node.glow!, sigma: v } })} />
          </Trio>
        </Section>
      ) : (
        <AddRow label="Shadow"
                onAdd={() => onPatch({ glow: { sigma: 24, opacity: 0.8, dx: 0, dy: 0 } })} />
      )}

      {node.blur != null ? (
        <Section
          label="Filters"
          right={
            <button onClick={() => onPatch({ blur: null })}
                    className="text-dim hover:text-ink">−</button>
          }
        >
          <NumField label="Blur" value={node.blur} min={0}
                    onChange={v => onPatch({ blur: v })} />
        </Section>
      ) : (
        <AddRow label="Filters" onAdd={() => onPatch({ blur: 8 })} />
      )}

      <AddRow label="Outline" hint="the renderer strokes paths only" />
      <AddRow label="Border" hint="the renderer strokes paths only" />
      <AddRow label="Inner shadow" hint="not in the renderer" />
      <AddRow label="Export" hint="export runs from the cli for now" />

      {box && (
        <div className="px-3 py-3">
          <p className="mb-2 font-medium">On screen</p>
          <Pair>
            <div className="inset-control flex h-[26px] items-center gap-2 px-2">
              <span className="text-faint">W</span>
              <span className="ml-auto tabular-nums">{Math.round(box.w)}</span>
            </div>
            <div className="inset-control flex h-[26px] items-center gap-2 px-2">
              <span className="text-faint">H</span>
              <span className="ml-auto tabular-nums">{Math.round(box.h)}</span>
            </div>
          </Pair>
          <p className="mt-1.5 text-[10px] leading-relaxed text-faint">
            what the engine paints at this frame, after motion. the fields above
            are the resting values in the document.
          </p>
        </div>
      )}
    </>
  )
}
