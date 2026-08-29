import NumField from './NumField'
import ColorRow from './ColorRow'
import { DIRS, EASES, KINDS, findKind, kindOf, withKind } from '../transitions'
import type { Artboard } from '../doc'
import type { Transition } from '../engine/types'

interface Props {
  /** the scene this transition brings you INTO */
  into: Artboard
  from: Artboard | null
  onPatch(t: Transition | null): void
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
        {right && <div className="ml-auto">{right}</div>}
      </div>
      {children}
    </div>
  )
}

/**
 * The seam between two scenes. This is the one thing a storyboard can edit that
 * a design tool cannot, because motion lives *between* screens rather than
 * inside one.
 */
export default function SeamInspector({ into, from, onPatch }: Props) {
  const t = into.transition
  const kind = kindOf(t)
  const meta = findKind(kind)
  const dur = t?.dur ?? 0.4

  const set = (patch: Partial<Transition>) =>
    onPatch({ ...(t ?? { kind }), ...patch })

  return (
    <>
      <div className="flex items-baseline gap-2 border-b border-hair px-3 py-2.5">
        <p className="font-medium">Transition</p>
        <span className="ml-auto truncate font-mono text-[10px] text-faint">
          {from?.id ?? '—'} → {into.id}
        </span>
      </div>

      <Section label="Kind">
        <div className="grid grid-cols-3 gap-1.5">
          {KINDS.map(k => (
            <button
              key={k.key}
              onClick={() => onPatch(
                // a plain cut with no morph is the document default, so it is
                // stored as the absence of a transition
                k.key === 'cut' && !t?.morph ? null : withKind(k.key, t))}
              className={`h-[26px] rounded-[5px] border text-[11px] transition-colors
                          ${kind === k.key
                            ? 'border-[#5e92f4] bg-[#5e92f4]/12 font-medium text-[#2f6ad4]'
                            : 'border-hair bg-surface hover:bg-black/[0.03]'}`}
            >
              {k.name}
            </button>
          ))}
        </div>
        {meta && (
          <p className="mt-2 leading-relaxed text-dim">{meta.blurb}</p>
        )}
      </Section>

      {kind !== 'cut' && (
        <Section label="Timing">
          <div className="grid grid-cols-2 gap-1.5">
            <NumField label="Dur" value={dur} precision={2} step={0.05} min={0.05}
                      onChange={v => set({ dur: v })} />
            <select
              value={typeof t?.ease === 'string' ? t.ease : ''}
              onChange={e => set({ ease: e.target.value || undefined })}
              className="inset-control h-[26px] w-full px-1.5 outline-none"
            >
              <option value="">linear</option>
              {EASES.map(e => <option key={e} value={e}>{e}</option>)}
            </select>
          </div>
          {dur > 0.35 && (
            <p className="mt-1.5 leading-relaxed text-[10px] text-faint">
              scene-level moves may run long, but in-scene motion over 350ms
              reads slow. the references sit at 140–280ms.
            </p>
          )}
        </Section>
      )}

      {meta?.needsDir && (
        <Section label="Direction">
          <div className="grid grid-cols-4 gap-1.5">
            {DIRS.map(d => (
              <button
                key={d}
                onClick={() => set({ dir: d })}
                className={`h-[26px] rounded-[5px] border text-[11px] transition-colors
                            ${t?.dir === d
                              ? 'border-[#5e92f4] bg-[#5e92f4]/12 text-[#2f6ad4]'
                              : 'border-hair bg-surface hover:bg-black/[0.03]'}`}
              >
                {d}
              </button>
            ))}
          </div>
        </Section>
      )}

      {meta?.needsColor && (
        <Section label="Dip colour">
          <ColorRow hex={t?.dir?.startsWith('#') ? t.dir : '#000000'} alpha={1}
                    onChange={hex => set({ dir: hex })} />
        </Section>
      )}

      <Section
        label="Magic move"
        right={
          <button
            onClick={() => set({ morph: !t?.morph })}
            className={`h-[22px] rounded-[5px] border px-2 text-[11px] transition-colors
                        ${t?.morph
                          ? 'border-[#5e92f4] bg-[#5e92f4]/12 text-[#2f6ad4]'
                          : 'border-hair bg-surface text-dim hover:bg-black/[0.03]'}`}
          >
            {t?.morph ? 'on' : 'off'}
          </button>
        }
      >
        <p className="leading-relaxed text-dim">
          nodes sharing an id across the cut glide as full-opacity clones
          instead of fading. unmatched nodes fade in place.
        </p>
        {t?.morph && (
          <div className="mt-2 grid grid-cols-2 gap-1.5">
            <NumField label="Dur" value={t.morph_dur ?? dur * 2.5} precision={2}
                      step={0.05} min={0.05}
                      onChange={v => set({ morph_dur: v })} />
            <select
              value={typeof t.morph_ease === 'string' ? t.morph_ease : ''}
              onChange={e => set({ morph_ease: e.target.value || undefined })}
              className="inset-control h-[26px] w-full px-1.5 outline-none"
            >
              <option value="">linear</option>
              {EASES.map(e => <option key={e} value={e}>{e}</option>)}
            </select>
          </div>
        )}
        <div className="mt-2">
          {into.carried.length ? (
            <>
              <p className="text-[10px] uppercase tracking-[0.14em] text-faint">
                carries {into.carried.length}
              </p>
              <div className="mt-1 flex flex-wrap gap-1">
                {into.carried.slice(0, 12).map(id => (
                  <span key={id}
                        className="rounded-[4px] bg-black/[0.05] px-1.5 py-0.5
                                   font-mono text-[10px] text-dim">
                    {id}
                  </span>
                ))}
              </div>
            </>
          ) : (
            <p className="text-[10px] text-faint">
              these two scenes share no node ids, so magic move has nothing to
              pair. give a node the same id in both to make it carry.
            </p>
          )}
        </div>
      </Section>

      <div className="px-3 py-3">
        <p className="leading-relaxed text-[10px] text-faint">
          cuts punctuate, morphs narrate. several of the reference films have
          two hard cuts or none — inside a chapter everything is dissolve,
          morph or physics.
        </p>
      </div>
    </>
  )
}
