import type { Pool } from 'pg'
import type { Asset, DocStore, FilmDoc, FilmEntry } from './types.js'

/** everything before accounts exist belongs to this workspace, and keeps belonging to it */
export const DEFAULT_WORKSPACE = '00000000-0000-0000-0000-000000000001'

/**
 * Films in Postgres, as documents.
 *
 * `stage` and `anim` are already JSON, so they are stored as jsonb rather than
 * shredded into tables. The format grows constantly and a relational schema
 * would mean a migration every time a node gains a field.
 *
 * The registry is DERIVED here rather than read from a hand-maintained
 * index.json. Duration and canvas size are computed in SQL from the stage
 * document itself, so the listing can never disagree with the film, and asking
 * for the registry does not drag several megabytes of documents across the
 * wire to work out how long each one is.
 */
export class PgStore implements DocStore {
  constructor(
    private readonly pool: Pool,
    private readonly workspace: string = DEFAULT_WORKSPACE,
  ) {}

  get description(): string {
    return 'postgres'
  }

  async list(): Promise<FilmEntry[]> {
    const { rows } = await this.pool.query<{
      slug: string; title: string; grp: string; dur: string | null
      w: number | null; h: number | null
    }>(
      `select f.slug, f.title, f.grp,
              (select coalesce(sum(coalesce((s->>'dur')::numeric, 3)), 0)
                 from jsonb_array_elements(f.stage->'scenes') s) as dur,
              (f.stage->'size'->>0)::int as w,
              (f.stage->'size'->>1)::int as h
         from films f
        where f.workspace_id = $1
        order by f.grp, f.slug`,
      [this.workspace],
    )
    return rows.map(r => ({
      slug: r.slug,
      title: r.title,
      group: r.grp,
      dur: Math.round(Number(r.dur ?? 0) * 100) / 100,
      size: [r.w ?? 1920, r.h ?? 1080] as [number, number],
    }))
  }

  async has(slug: string): Promise<boolean> {
    const { rowCount } = await this.pool.query(
      'select 1 from films where workspace_id = $1 and slug = $2',
      [this.workspace, slug],
    )
    return (rowCount ?? 0) > 0
  }

  async get(slug: string): Promise<FilmDoc | null> {
    const { rows } = await this.pool.query<{ stage: unknown; anim: unknown }>(
      'select stage, anim from films where workspace_id = $1 and slug = $2',
      [this.workspace, slug],
    )
    return rows[0] ? { stage: rows[0].stage, anim: rows[0].anim } : null
  }

  async put(slug: string, doc: FilmDoc): Promise<void> {
    // a save must not invent a title for a film that already has one, so the
    // insert supplies a fallback and the update leaves the existing one alone
    const title = titleOf(doc.stage) ?? slug
    await this.pool.query(
      `insert into films (workspace_id, slug, title, stage, anim)
            values ($1, $2, $3, $4, $5)
       on conflict (workspace_id, slug) do update
              set stage = excluded.stage,
                  anim = excluded.anim,
                  updated_at = now()`,
      [this.workspace, slug, title, JSON.stringify(doc.stage), JSON.stringify(doc.anim)],
    )
  }

  async assets(): Promise<Asset[]> {
    const { rows } = await this.pool.query<{ src: string; bytes: string }>(
      'select src, bytes from assets where workspace_id = $1 order by src',
      [this.workspace],
    )
    return rows.map(r => ({ src: r.src, bytes: Number(r.bytes) }))
  }
}

/** documents carry no title field; the film menu falls back to the slug */
function titleOf(stage: unknown): string | null {
  const t = (stage as { title?: unknown })?.title
  return typeof t === 'string' && t.trim() ? t : null
}
