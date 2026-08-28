import { useEffect } from 'react'
import { EFFECTS, GROUPS } from '../effects'
import type { NodePatch } from '../doc'
import type { Node } from '../engine/types'

interface Props {
  node: Node | null
  onApply(patch: NodePatch): void
  onClose(): void
}

/**
 * The renderer's effects, applied to the selected node.
 *
 * Paper's shader gallery creates standalone generative layers; this cannot,
 * because the engine has no shader stage. Rather than fake that, this surfaces
 * what the engine genuinely does — and gives goo and streak their first UI.
 */
export default function EffectPicker({ node, onApply, onClose }: Props) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div className="fixed inset-0 z-[120] grid place-items-center bg-black/25"
         onPointerDown={onClose}>
      <div
        onPointerDown={e => e.stopPropagation()}
        className="flex max-h-[74vh] w-[520px] flex-col overflow-hidden rounded-[12px]
                   border border-black/10 bg-panel
                   shadow-[0_24px_60px_-16px_rgba(0,0,0,0.5)]"
      >
        <div className="flex items-center gap-2 border-b border-hair px-3 py-2.5">
          <p className="font-medium">Effects</p>
          <span className="text-dim">
            {node ? `on ${node.id}` : 'select a node first'}
          </span>
          <button onClick={onClose} className="ml-auto text-dim hover:text-ink">✕</button>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto">
          {GROUPS.map(g => {
            const items = EFFECTS.filter(e => e.group === g.key)
            if (!items.length) return null
            return (
              <div key={g.key}>
                <p className="px-3 pb-1 pt-3 text-[10px] uppercase tracking-[0.14em] text-faint">
                  {g.label}
                </p>
                {items.map(fx => {
                  // some effects are only meaningful on some node types; say so
                  // rather than letting them silently do nothing
                  const ok = !node ? false
                    : !fx.appliesTo || fx.appliesTo.includes(node.type)
                  return (
                    <div key={fx.key} className="border-b border-hair px-3 py-2.5">
                      <div className="flex items-baseline gap-2">
                        <p className={ok ? 'font-medium' : 'font-medium text-faint'}>
                          {fx.name}
                        </p>
                        {!ok && node && (
                          <span className="text-[10px] text-faint">
                            {fx.appliesTo?.join(', ')} only
                          </span>
                        )}
                      </div>
                      <p className="mt-0.5 leading-relaxed text-dim">{fx.blurb}</p>
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {fx.presets.map(p => (
                          <button
                            key={p.name}
                            disabled={!ok}
                            onClick={() => { onApply(p.patch); onClose() }}
                            className={`inset-control h-[26px] px-2.5 transition-colors
                                        ${ok ? 'hover:bg-black/[0.03]'
                                             : 'cursor-default text-faint/60'}`}
                          >
                            {p.name}
                          </button>
                        ))}
                      </div>
                    </div>
                  )
                })}
              </div>
            )
          })}
        </div>

        <p className="border-t border-hair px-3 py-2 leading-relaxed text-[10px] text-faint">
          these are the renderer's own effects, not shaders. streak only shows
          while a node is in motion, and goo only fuses nodes that share a group.
        </p>
      </div>
    </div>
  )
}
