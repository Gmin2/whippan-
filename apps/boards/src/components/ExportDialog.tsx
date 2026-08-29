import { useCallback, useEffect, useRef, useState } from 'react'
import { cancelExport, exportFileUrl, pollExport, startExport } from '../engine'
import type { ExportJob } from '../engine'
import type { Anim, Stage } from '../engine/types'

interface Props {
  slug: string
  title: string
  stage: Stage
  anim: Anim
  /** total film length, for the estimate */
  dur: number
  onClose(): void
}

const SCALES = [
  { key: 1 as const, label: '1×', note: 'document size' },
  { key: 2 as const, label: '2×', note: 'supersampled, 4K from 1080p' },
]

const kb = (n?: number) =>
  n == null ? '—'
    : n > 1_000_000 ? `${(n / 1e6).toFixed(1)} MB`
    : `${Math.max(1, Math.round(n / 1000))} KB`

const secs = (ms: number) => `${(ms / 1000).toFixed(1)}s`

/**
 * Rendering the film. This is a job, not a request: a 28-second film is
 * hundreds of frames and takes seconds even at 150-500fps, so the dialog
 * queues it and follows the renderer's own frame count.
 *
 * The document travels in the request rather than the slug alone, so what you
 * are looking at is what gets rendered — unsaved edits included.
 */
export default function ExportDialog({
  slug, title, stage, anim, dur, onClose,
}: Props) {
  const [fps, setFps] = useState(stage.fps ?? 30)
  const [supersample, setSupersample] = useState<1 | 2>(1)
  const [job, setJob] = useState<ExportJob | null>(null)
  const [error, setError] = useState<string | null>(null)
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const [w, h] = stage.size

  const busy = job?.status === 'queued' || job?.status === 'running'

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape' && !busy) onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose, busy])

  // stop polling when the dialog goes away, so a closed dialog cannot keep a
  // request loop alive
  useEffect(() => () => { if (timer.current) clearTimeout(timer.current) }, [])

  const follow = useCallback((id: string) => {
    const tick = async () => {
      try {
        const next = await pollExport(id)
        setJob(next)
        if (next.status === 'queued' || next.status === 'running') {
          timer.current = setTimeout(tick, 400)
        }
      } catch (e) {
        setError(String(e))
      }
    }
    timer.current = setTimeout(tick, 300)
  }, [])

  const run = async () => {
    setError(null)
    try {
      const started = await startExport(slug, stage, anim, { fps, supersample })
      setJob(started)
      follow(started.id)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  const stop = async () => {
    if (!job) return
    await cancelExport(job.id)
    if (timer.current) clearTimeout(timer.current)
    setJob({ ...job, status: 'cancelled' })
  }

  const frames = Math.round(dur * fps)
  const [now, setNow] = useState(Date.now())
  useEffect(() => {
    if (!busy) return
    const t = setInterval(() => setNow(Date.now()), 200)
    return () => clearInterval(t)
  }, [busy])
  const elapsed = job?.startedAt ? now - job.startedAt : 0

  return (
    <div className="fixed inset-0 z-[130] grid place-items-center bg-black/25"
         onPointerDown={() => { if (!busy) onClose() }}>
      <div
        onPointerDown={e => e.stopPropagation()}
        className="w-[420px] overflow-hidden rounded-[12px] border border-black/10
                   bg-panel shadow-[0_24px_60px_-16px_rgba(0,0,0,0.5)]"
      >
        <div className="flex items-center gap-2 border-b border-hair px-3 py-2.5">
          <p className="font-medium">Export</p>
          <span className="truncate text-dim">{title}</span>
          <button onClick={onClose} disabled={busy}
                  className="ml-auto text-dim transition-colors hover:text-ink
                             disabled:opacity-40">✕</button>
        </div>

        <div className="border-b border-hair px-3 py-3">
          <p className="mb-2 text-[10px] uppercase tracking-[0.14em] text-faint">
            resolution
          </p>
          <div className="grid grid-cols-2 gap-1.5">
            {SCALES.map(s => (
              <button
                key={s.key}
                disabled={busy}
                onClick={() => setSupersample(s.key)}
                className={`rounded-[6px] border px-2 py-1.5 text-left transition-colors
                            disabled:opacity-50
                            ${supersample === s.key
                              ? 'border-[#5e92f4] bg-[#5e92f4]/12'
                              : 'border-hair bg-surface hover:bg-black/[0.03]'}`}
              >
                <span className="font-mono tabular-nums">
                  {w * s.key} × {h * s.key}
                </span>
                <span className="mt-0.5 block text-[10px] text-faint">{s.note}</span>
              </button>
            ))}
          </div>

          <div className="mt-2.5 flex items-center gap-2">
            <span className="text-[10px] uppercase tracking-[0.14em] text-faint">fps</span>
            {[24, 30, 60].map(v => (
              <button
                key={v}
                disabled={busy}
                onClick={() => setFps(v)}
                className={`h-[24px] rounded-[5px] border px-2 font-mono text-[11px]
                            tabular-nums transition-colors disabled:opacity-50
                            ${fps === v
                              ? 'border-[#5e92f4] bg-[#5e92f4]/12 text-[#2f6ad4]'
                              : 'border-hair bg-surface hover:bg-black/[0.03]'}`}
              >
                {v}
              </button>
            ))}
            <span className="ml-auto font-mono text-[10px] text-faint tabular-nums">
              {dur.toFixed(2)}s · {frames} frames
            </span>
          </div>
        </div>

        {/* progress, once a job exists */}
        {job && (
          <div className="border-b border-hair px-3 py-3">
            <div className="mb-1.5 flex items-baseline gap-2">
              <span className={job.status === 'failed' ? 'text-[#c0392b]' : ''}>
                {job.status === 'queued' ? 'queued'
                  : job.status === 'running' ? 'rendering'
                  : job.status === 'done' ? 'done'
                  : job.status}
              </span>
              <span className="ml-auto font-mono text-[10px] text-faint tabular-nums">
                {job.frames != null && job.totalFrames
                  ? `${job.frames} / ${job.totalFrames} frames`
                  : ''}
                {job.bytes != null ? `  ${kb(job.bytes)}` : ''}
              </span>
            </div>
            <div className="h-[6px] overflow-hidden rounded-full bg-black/[0.07]">
              <div
                className={`h-full rounded-full transition-[width] duration-200
                            ${job.status === 'failed' ? 'bg-[#c0392b]' : 'bg-[#5e92f4]'}`}
                style={{
                  width: job.status === 'failed' ? '100%'
                    : `${Math.round((job.progress ?? 0) * 100)}%`,
                }}
              />
            </div>
            {job.error && (
              <p className="mt-2 leading-relaxed text-[10px] text-[#c0392b]">{job.error}</p>
            )}
            {job.status === 'failed' && job.log && (
              <pre className="mt-2 max-h-[110px] overflow-auto rounded-[5px] bg-black/[0.04]
                              p-2 font-mono text-[10px] leading-relaxed text-dim">
                {job.log.split('\n').slice(-8).join('\n')}
              </pre>
            )}
          </div>
        )}

        {error && (
          <div className="border-b border-hair px-3 py-2.5">
            <p className="leading-relaxed text-[11px] text-[#c0392b]">{error}</p>
          </div>
        )}

        <div className="flex items-center gap-2 px-3 py-2.5">
          <p className="text-[10px] leading-relaxed text-faint">
            renders the film as it stands, including unsaved edits
          </p>
          <div className="ml-auto flex gap-1.5">
            {busy && (
              <button onClick={stop}
                      className="inset-control h-[28px] px-3 transition-colors
                                 hover:bg-black/[0.03]">
                Cancel
              </button>
            )}
            {job?.status === 'done' ? (
              <a
                href={exportFileUrl(job.id)}
                download={`${slug}.mp4`}
                className="grid h-[28px] place-items-center rounded-[6px] bg-[#5e92f4]
                           px-3 text-white transition-colors hover:bg-[#4d82e8]"
              >
                Download {kb(job.bytes)}
              </a>
            ) : (
              <button
                onClick={run}
                disabled={busy}
                className="h-[28px] rounded-[6px] bg-[#5e92f4] px-3 text-white
                           transition-colors hover:bg-[#4d82e8] disabled:opacity-50"
              >
                {busy ? `Rendering… ${secs(elapsed)}` : job ? 'Render again' : 'Render'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
