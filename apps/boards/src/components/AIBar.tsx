import { useEffect, useMemo, useRef, useState } from 'react'
import { ImageSparkle, PenSparkle, Sparkle } from '../icons'
import type { AiKind, Capability, MotionProposal } from '../ai'
import type { Fit } from '../fit'

interface Props {
  kind: AiKind
  caps: Capability[]
  /** what the prompt will act on, named so you can see it before you send */
  subject: string
  busy: boolean
  error: string | null
  /** the motion proposal waiting on a decision, if there is one */
  proposal: MotionProposal | null
  /** a composed screen waiting on a decision, with its fit budget already run */
  screen: {
    note: string
    nodes: { id: string; type: string }[]
    fit: Fit[]
    /** how the composed screen scored against the corpus, if it was scored */
    checks?: { key: string; score: number; detail: string }[]
  } | null
  onAcceptScreen(): void
  onDiscardScreen(): void
  onRun(prompt: string, model: string, extra: Record<string, unknown>): void
  onAccept(): void
  onDiscard(): void
  onClose(): void
}

const ASPECTS = ['1:1', '16:9', '4:3', '9:16'] as const

const TITLE: Record<AiKind, string> = {
  film: 'Create film',
  screen: 'Create screen',
  motion: 'Create motion',
  image: 'Create image',
  vector: 'Create SVG',
}

const PLACEHOLDER: Record<AiKind, string> = {
  film: 'a 20s launch film for a json motion format',
  screen: 'the editor mid-keystroke, with a run button',
  motion: 'make these land harder, 60ms apart',
  image: 'a dark product shot, soft rim light',
  vector: 'Moon icon in outline style',
}

const ICON: Record<AiKind, React.ReactNode> = {
  film: <Sparkle size={13} />,
  screen: <Sparkle size={13} />,
  motion: <Sparkle size={13} />,
  image: <ImageSparkle size={14} />,
  vector: <PenSparkle size={14} />,
}

/**
 * The prompt bar, docked at the bottom of the canvas.
 *
 * Paper puts one of these under the artwork with a model picker on the left and
 * the action on the right, and the shape is right: the prompt is about what you
 * have selected, so it belongs over the canvas rather than in a side panel.
 *
 * Motion never applies straight to the document. It comes back as a proposal
 * you read and accept, because a model that quietly rewrites your timing is a
 * model you stop trusting.
 */
export default function AIBar({
  kind, caps, subject, busy, error, proposal, screen, onRun, onAccept, onDiscard,
  onAcceptScreen, onDiscardScreen, onClose,
}: Props) {
  const cap = useMemo(() => caps.find(c => c.kind === kind), [caps, kind])
  const [prompt, setPrompt] = useState('')
  const [model, setModel] = useState('')
  const [aspect, setAspect] = useState<string>('16:9')
  const [picking, setPicking] = useState(false)
  const box = useRef<HTMLTextAreaElement>(null)

  useEffect(() => { box.current?.focus() }, [kind])
  useEffect(() => { setModel(cap?.models[0]?.id ?? '') }, [cap])

  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !busy) { e.stopPropagation(); onClose() }
    }
    window.addEventListener('keydown', key, true)
    return () => window.removeEventListener('keydown', key, true)
  }, [onClose, busy])

  const model_ = cap?.models.find(m => m.id === model) ?? cap?.models[0]
  const ready = !!cap?.ready
  const canRun = ready && !busy && prompt.trim().length > 0

  const run = () => {
    if (!canRun) return
    onRun(prompt.trim(), model, kind === 'image' ? { aspect } : {})
  }

  return (
    <div className="pointer-events-none absolute inset-x-0 bottom-4 z-[110] flex justify-center px-4">
      <div className="pointer-events-auto w-[560px] max-w-full overflow-hidden rounded-[11px]
                      border border-black/10 bg-panel
                      shadow-[0_18px_50px_-14px_rgba(0,0,0,0.45)]">

        <div className="flex items-center gap-2 border-b border-hair px-3 py-2">
          <span className="text-dim">{ICON[kind]}</span>
          <p className="font-medium">{TITLE[kind]}</p>
          <span className="truncate text-dim">{subject}</span>
          <button onClick={onClose} disabled={busy}
                  className="ml-auto text-dim transition-colors hover:text-ink
                             disabled:opacity-40">✕</button>
        </div>

        {/* a proposal replaces the prompt while it is waiting to be judged */}
        {screen ? (
          <div className="px-3 py-2.5">
            <p className="mb-2">{screen.note}</p>
            <div className="max-h-[150px] overflow-auto rounded-[6px] bg-black/[0.04] p-2">
              {screen.nodes.filter(n => n.type === 'group').map(n => (
                <p key={n.id} className="font-mono text-[10px] leading-relaxed text-dim">
                  {n.id}
                </p>
              ))}
            </div>
            {/* the fit budget, run before you are asked to judge it */}
            {screen.fit.length > 0 && (
              <div className="mt-2 space-y-0.5">
                {screen.fit.slice(0, 5).map((f, i) => (
                  <p key={i} className="leading-relaxed text-[10px]"
                     style={{ color: f.level === 'warn' ? '#8a5d12' : 'rgba(0,0,0,0.45)' }}>
                    {f.node ? `${f.node}: ` : ''}{f.text}
                  </p>
                ))}
              </div>
            )}
            {/* what it measured against the corpus, worst first, so the
                number you are judging is visible rather than implied */}
            {screen.checks && screen.checks.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {[...screen.checks].sort((a, b) => a.score - b.score).map(c => (
                  <span key={c.key} title={c.detail}
                        className="rounded-[4px] px-1.5 py-0.5 font-mono text-[9px]"
                        style={{
                          background: c.score < 0.6 ? 'rgba(138,93,18,0.12)' : 'rgba(0,0,0,0.05)',
                          color: c.score < 0.6 ? '#8a5d12' : 'rgba(0,0,0,0.45)',
                        }}>
                    {c.key} {c.score.toFixed(2)}
                  </span>
                ))}
              </div>
            )}
            <div className="mt-2.5 flex items-center gap-2">
              <p className="text-[10px] text-faint">
                {screen.nodes.filter(n => n.type === 'group').length} blocks
                {screen.checks?.some(c => c.score < 0.6)
                  ? ` · ${screen.checks.filter(c => c.score < 0.6).length} checks below the corpus`
                  : screen.fit.some(f => f.level === 'warn')
                    ? ' · the budget flagged something'
                    : ' · inside the fit budget'}
              </p>
              <div className="ml-auto flex gap-1.5">
                <button onClick={onDiscardScreen}
                        className="inset-control h-[28px] px-3 transition-colors
                                   hover:bg-black/[0.03]">Discard</button>
                <button onClick={onAcceptScreen}
                        className="h-[28px] rounded-[6px] bg-[#5e92f4] px-3 text-white
                                   transition-colors hover:bg-[#4d82e8]">Place</button>
              </div>
            </div>
          </div>
        ) : proposal ? (
          <div className="px-3 py-2.5">
            <p className="mb-2">{proposal.note}</p>
            <pre className="max-h-[190px] overflow-auto rounded-[6px] bg-black/[0.04] p-2
                            font-mono text-[10px] leading-relaxed text-dim">
              {JSON.stringify(proposal.tracks, null, 1)}
            </pre>
            <div className="mt-2.5 flex items-center gap-2">
              <p className="text-[10px] text-faint">
                {proposal.tracks.length} track{proposal.tracks.length === 1 ? '' : 's'};
                {' '}replaces the motion on {subject}
              </p>
              <div className="ml-auto flex gap-1.5">
                <button onClick={onDiscard}
                        className="inset-control h-[28px] px-3 transition-colors
                                   hover:bg-black/[0.03]">Discard</button>
                <button onClick={onAccept}
                        className="h-[28px] rounded-[6px] bg-[#5e92f4] px-3 text-white
                                   transition-colors hover:bg-[#4d82e8]">Apply</button>
              </div>
            </div>
          </div>
        ) : (
          <>
            <textarea
              ref={box}
              rows={2}
              value={prompt}
              disabled={!ready || busy}
              placeholder={ready ? PLACEHOLDER[kind] : ''}
              onChange={e => setPrompt(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); run() }
              }}
              className="block max-h-[120px] w-full resize-none bg-transparent px-3 py-2.5
                         leading-relaxed outline-none placeholder:text-faint
                         disabled:opacity-50"
            />

            <div className="flex items-center gap-1.5 px-3 pb-2.5">
              {/* model picker, the way paper labels the model on the left */}
              <div className="relative">
                <button
                  disabled={!ready}
                  onClick={() => setPicking(v => !v)}
                  className="inset-control flex h-[26px] items-center gap-1.5 px-2
                             transition-colors hover:bg-black/[0.03] disabled:opacity-50"
                >
                  <span className="text-[#5e92f4]"><Sparkle size={11} /></span>
                  <span>{model_?.label ?? 'model'}</span>
                  <span className="text-faint">⌄</span>
                </button>
                {picking && (
                  <div className="absolute bottom-[30px] left-0 z-10 w-[236px] rounded-[8px]
                                  border border-black/10 bg-panel p-1
                                  shadow-[0_12px_34px_-10px_rgba(0,0,0,0.4)]">
                    {cap?.models.map(m => (
                      <button
                        key={m.id}
                        onClick={() => { setModel(m.id); setPicking(false) }}
                        className={`block w-full rounded-[5px] px-2 py-1.5 text-left
                                    transition-colors hover:bg-black/[0.04]
                                    ${m.id === model ? 'bg-black/[0.05]' : ''}`}
                      >
                        <span className="block">{m.label}</span>
                        {m.note && <span className="block text-[10px] text-faint">{m.note}</span>}
                      </button>
                    ))}
                    <p className="px-2 pb-1 pt-1.5 text-[10px] text-faint">
                      via {cap?.provider}
                    </p>
                  </div>
                )}
              </div>

              {kind === 'image' && (
                <div className="flex gap-1">
                  {ASPECTS.map(a => (
                    <button
                      key={a}
                      disabled={!ready}
                      onClick={() => setAspect(a)}
                      className={`h-[26px] rounded-[5px] border px-2 font-mono text-[10px]
                                  tabular-nums transition-colors disabled:opacity-50
                                  ${aspect === a
                                    ? 'border-[#5e92f4] bg-[#5e92f4]/12 text-[#2f6ad4]'
                                    : 'border-hair bg-surface hover:bg-black/[0.03]'}`}
                    >
                      {a}
                    </button>
                  ))}
                </div>
              )}

              <div className="ml-auto flex items-center gap-2">
                {!ready && (
                  <span className="text-[10px] text-faint">{cap?.reason ?? 'not configured'}</span>
                )}
                <button
                  onClick={run}
                  disabled={!canRun}
                  className="flex h-[28px] items-center gap-1.5 rounded-[6px] bg-[#5e92f4]
                             px-3 text-white transition-colors hover:bg-[#4d82e8]
                             disabled:opacity-40"
                >
                  <Sparkle size={11} />
                  {busy ? 'Working…' : TITLE[kind]}
                </button>
              </div>
            </div>
          </>
        )}

        {error && (
          <p className="border-t border-hair px-3 py-2 leading-relaxed text-[11px] text-[#c0392b]">
            {error}
          </p>
        )}
      </div>
    </div>
  )
}
