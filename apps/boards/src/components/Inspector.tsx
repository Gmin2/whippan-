import NumField from './NumField'
import ColorRow from './ColorRow'
import type { Node } from '../engine/types'
import type { NodePatch } from '../doc'
import type { NodeBox } from '../measure'

interface Props {
  node: Node
  /** what the node actually measures on screen right now, which is not the
   *  same as its resting geometry once motion is running */
  box: NodeBox | null
  onPatch(patch: NodePatch): void
}

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="border-b border-hair px-3 py-3">
      <p className="mb-2 font-medium">{label}</p>
      {children}
    </div>
  )
}

const Pair = ({ children }: { children: React.ReactNode }) => (
  <div className="grid grid-cols-2 gap-1.5">{children}</div>
)

export default function Inspector({ node, box, onPatch }: Props) {
  const isText = node.type === 'text'
  const measured = box && (
    Math.abs((box.w ?? 0) - (node.w ?? 0)) > 1 ||
    Math.abs((box.h ?? 0) - (node.h ?? 0)) > 1)

  return (
    <>
      <Section label={node.type}>
        <input
          key={node.id}
          defaultValue={node.id}
          readOnly
          className="inset-control h-[26px] w-full px-2 font-mono text-[11px] text-dim outline-none"
        />
      </Section>

      <Section label="Position">
        <Pair>
          <NumField label="X" value={node.x ?? 0}
                    onChange={v => onPatch({ x: Math.round(v) })} />
          <NumField label="Y" value={node.y ?? 0}
                    onChange={v => onPatch({ y: Math.round(v) })} />
        </Pair>
        <p className="mt-1.5 text-[10px] text-faint">x,y is the node centre</p>
      </Section>

      {!isText && (
        <Section label="Size">
          <Pair>
            <NumField label="W" value={node.w ?? 0}
                      onChange={v => onPatch({ w: Math.max(1, Math.round(v)) })} />
            <NumField label="H" value={node.h ?? 0}
                      onChange={v => onPatch({ h: Math.max(1, Math.round(v)) })} />
          </Pair>
          <div className="mt-1.5">
            <Pair>
              <NumField label="R" value={node.radius ?? 0} min={0}
                        onChange={v => onPatch({ radius: Math.round(v) })} />
              <NumField label="°" value={node.rot ?? 0} step={1}
                        onChange={v => onPatch({ rot: v })} />
            </Pair>
          </div>
        </Section>
      )}

      {isText && (
        <Section label="Text">
          <textarea
            key={node.id}
            defaultValue={node.text ?? ''}
            rows={2}
            onBlur={e => onPatch({ text: e.target.value })}
            className="inset-control w-full resize-none px-2 py-1.5 leading-relaxed
                       outline-none focus:border-[#2d52f0] focus:ring-2
                       focus:ring-[#2d52f0]/25"
          />
          <div className="mt-1.5">
            <Pair>
              <NumField label="Size" value={node.font?.size ?? 48} min={4}
                        onChange={v => onPatch({ fontSize: Math.round(v) })} />
              <NumField label="°" value={node.rot ?? 0} step={1}
                        onChange={v => onPatch({ rot: v })} />
            </Pair>
          </div>
        </Section>
      )}

      <Section label="Fill">
        <ColorRow
          hex={(isText ? node.color : node.fill) ?? '#000000'}
          alpha={1}
          onChange={h => onPatch(isText ? { color: h } : { fill: h })}
        />
      </Section>

      {measured && box && (
        <Section label="On screen">
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
          <p className="mt-1.5 leading-relaxed text-[10px] text-faint">
            what the engine actually paints at this frame, after motion. the
            fields above are the resting values in the document.
          </p>
        </Section>
      )}
    </>
  )
}
