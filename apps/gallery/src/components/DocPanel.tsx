import { useMemo, useState } from 'react'
import type { Doc, Scene } from '../engine/types'

interface Props {
  doc: Doc
  t: number
}

/** the scene the playhead is inside, plus where that scene starts */
function sceneAt(doc: Doc, t: number): { scene: Scene; index: number; start: number } {
  let start = 0
  const scenes = doc.stage.scenes
  for (let i = 0; i < scenes.length; i++) {
    const d = scenes[i].dur ?? 3
    if (t < start + d || i === scenes.length - 1) return { scene: scenes[i], index: i, start }
    start += d
  }
  return { scene: scenes[0], index: 0, start: 0 }
}

// The document beside the film it produced. Scrubbing moves the highlight,
// which is the whole argument: the frame on the left is this json at this
// second, not a video file.
export default function DocPanel({ doc, t }: Props) {
  const [tab, setTab] = useState<'stage' | 'anim'>('stage')
  const { scene, index, start } = useMemo(() => sceneAt(doc, t), [doc, t])

  // the overlay tracks that touch a node in the scene on screen
  const tracks = useMemo(() => {
    const ids = new Set(scene.nodes.map(n => n.id))
    return (doc.anim.tracks as { target?: string }[])
      .filter(tr => tr.target && (ids.has(tr.target) || tr.target === scene.id))
  }, [doc, scene])

  const body = tab === 'stage' ? scene : { tracks }

  return (
    <aside className="hidden w-[360px] shrink-0 flex-col self-stretch xl:flex">
      <div className="mb-4 flex items-center gap-4">
        {(['stage', 'anim'] as const).map(k => (
          <button
            key={k}
            onClick={() => setTab(k)}
            className={`label transition-colors hover:text-ink
                        ${tab === k ? 'text-flame' : ''}`}
          >
            {k}.json
          </button>
        ))}
        <span className="h-px flex-1 bg-hair" />
        <span className="font-mono text-[10px] text-mute tabular-nums">
          {(t - start).toFixed(2)}s into scene
        </span>
      </div>

      <ol className="mb-4 flex flex-col gap-px">
        {doc.stage.scenes.map((s, si) => (
          <li key={s.id}
              className={`flex items-baseline gap-2.5 py-1 text-[11.5px] leading-snug
                          ${si === index ? 'text-ink' : 'text-mute'}`}>
            <span className={`mt-[5px] h-px w-4 shrink-0
                              ${si === index ? 'bg-flame' : 'bg-hair'}`} />
            <span className="font-mono text-[10px] tabular-nums">{s.id}</span>
            <span className="min-w-0 flex-1 truncate">{s.note ?? `${s.nodes.length} nodes`}</span>
            <span className="font-mono text-[10px] tabular-nums">{(s.dur ?? 3).toFixed(1)}s</span>
          </li>
        ))}
      </ol>

      <pre className="flex-1 overflow-auto rounded-lg bg-ink/[0.035] p-4
                      font-mono text-[10.5px] leading-[1.65] text-ink/75">
        {JSON.stringify(body, null, 1)}
      </pre>
    </aside>
  )
}
