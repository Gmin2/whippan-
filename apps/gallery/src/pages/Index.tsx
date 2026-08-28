import FilmCard from '../components/FilmCard'
import type { Entry, Group } from '../engine/types'

interface Props {
  ck: CanvasKit
  registry: Entry[]
}

// The three groups read differently and should look it: our own work first,
// then the reproductions that prove the engine, then the primitives that
// show a single capability at a time.
const SECTIONS: { group: Group; title: string; note: string }[] = [
  {
    group: 'films',
    title: 'our films',
    note: 'authored end to end in whippan, stage and overlay written by hand and by agent',
  },
  {
    group: 'reproductions',
    title: 'reproductions',
    note: 'real launch videos rebuilt from json and diffed against the original frame by frame',
  },
  {
    group: 'primitives',
    title: 'primitives',
    note: 'one engine capability each, one beat long',
  },
]

function SectionHead({ title, note, count }: { title: string; note: string; count: number }) {
  return (
    <div className="mb-7 flex items-baseline gap-4">
      <h2 className="label text-ink">{title}</h2>
      <span className="h-px flex-1 bg-hair" />
      <p className="hidden max-w-md text-right text-[11.5px] leading-snug text-mute md:block">
        {note}
      </p>
      <span className="font-mono text-[10px] text-mute tabular-nums">
        {String(count).padStart(2, '0')}
      </span>
    </div>
  )
}

export default function Index({ ck, registry }: Props) {
  const at = (slug: string) => registry.findIndex(e => e.slug === slug)

  return (
    <div className="min-h-screen">
      <header className="mx-auto max-w-[1320px] px-8 pb-12 pt-20">
        <div className="flex flex-wrap items-end justify-between gap-8">
          <div>
            <h1 className="text-[42px] font-semibold leading-none tracking-[-0.03em]">
              whippan
            </h1>
            <p className="mt-4 max-w-[38ch] text-[15px] leading-relaxed text-ink/70">
              json in, launch film out. every frame below is drawn live in this
              tab by the engine, out of a document you can read.
            </p>
          </div>

          <dl className="flex gap-9">
            {[
              ['films', String(registry.length)],
              ['rebuilt', String(registry.filter(e => e.group === 'reproductions').length)],
              ['runtime', `${Math.round(registry.reduce((a, e) => a + e.dur, 0) / 60)}m`],
            ].map(([k, v]) => (
              <div key={k}>
                <dt className="label">{k}</dt>
                <dd className="mt-1.5 font-mono text-[22px] tabular-nums">{v}</dd>
              </div>
            ))}
          </dl>
        </div>
      </header>

      <div className="mx-auto max-w-[1320px] px-8">
        <span className="block h-px bg-hair" />
      </div>

      <main className="mx-auto max-w-[1320px] px-8 pb-28 pt-14">
        {SECTIONS.map(s => {
          const films = registry.filter(e => e.group === s.group)
          if (!films.length) return null
          return (
            <section key={s.group} className="mb-20 last:mb-0">
              <SectionHead title={s.title} note={s.note} count={films.length} />
              <div className="grid grid-cols-1 gap-x-6 gap-y-9 sm:grid-cols-2 lg:grid-cols-3">
                {films.map(e => (
                  <FilmCard key={e.slug} ck={ck} entry={e} index={at(e.slug)} />
                ))}
              </div>
            </section>
          )
        })}
      </main>
    </div>
  )
}
