interface Props {
  t: number
  dur: number
  playing: boolean
  onToggle(): void
  onSeek(v: number): void
}

const IconPlay = () => (
  <svg width="13" height="13" viewBox="0 0 20 20" aria-hidden>
    <polygon points="6 4 16 10 6 16 6 4" fill="none" stroke="currentColor"
             strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
  </svg>
)

const IconPause = () => (
  <svg width="13" height="13" viewBox="0 0 20 20" aria-hidden>
    <line x1="7" y1="4.5" x2="7" y2="15.5" stroke="currentColor"
          strokeLinecap="round" strokeWidth="2.4" />
    <line x1="13" y1="4.5" x2="13" y2="15.5" stroke="currentColor"
          strokeLinecap="round" strokeWidth="2.4" />
  </svg>
)

export default function Transport({ t, dur, playing, onToggle, onSeek }: Props) {
  const pct = dur ? (t / dur) * 100 : 0

  return (
    <div className="mt-6 flex w-full max-w-[560px] items-center gap-4">
      <button
        onClick={onToggle}
        aria-label={playing ? 'pause' : 'play'}
        className="grid h-8 w-8 shrink-0 place-items-center rounded-full
                   text-ink/60 transition-colors hover:bg-black/[0.05] hover:text-ink"
      >
        {playing ? <IconPause /> : <IconPlay />}
      </button>

      {/* the scrub track: a hairline that fills, with the input on top of it */}
      <label className="relative flex h-8 flex-1 items-center">
        <span className="pointer-events-none absolute inset-x-0 h-px bg-hair" />
        <span className="pointer-events-none absolute h-px bg-flame"
              style={{ width: `${pct}%` }} />
        <span
          className="pointer-events-none absolute h-2.5 w-2.5 -translate-x-1/2
                     rounded-full bg-flame"
          style={{ left: `${pct}%` }}
        />
        <input
          type="range" min={0} max={dur} step={1 / 120} value={t}
          onChange={e => onSeek(parseFloat(e.target.value))}
          aria-label="scrub"
          className="absolute inset-x-0 h-8 w-full cursor-pointer opacity-0"
        />
      </label>

      <span className="w-28 shrink-0 whitespace-nowrap text-right font-mono
                       text-[10px] text-mute tabular-nums">
        {t.toFixed(2)} / {dur.toFixed(2)}s
      </span>
    </div>
  )
}
