import { readFile } from 'node:fs/promises'
import { join } from 'node:path'
import { db, closeDb } from './pool.js'
import { migrate } from './migrate.js'
import { loadConfig } from '../config.js'
import { DEFAULT_WORKSPACE } from '../store/pg.js'

/**
 * Move the film library off the filesystem, once.
 *
 * Reads the registry the editor has always read and writes each film into
 * Postgres. Idempotent: running it twice updates rather than duplicates, so it
 * is safe to re-run after editing a doc on disk.
 *
 *   npm run seed              -> the default workspace
 *   npm run seed -- alice      -> that workspace's slug, for local development
 *                                 with accounts on, where the default one has
 *                                 no members and is therefore invisible
 */
interface Entry { slug: string; title?: string; group?: string }

const isGroup = (g: unknown): g is string =>
  g === 'films' || g === 'reproductions' || g === 'primitives'

async function main() {
  const config = loadConfig()
  if (!config.databaseUrl) throw new Error('DATABASE_URL is not set')
  const pool = db(config.databaseUrl)

  const ran = await migrate(pool)
  if (ran.length) console.log('applied:', ran.join(', '))

  const target = process.argv[2]
  let workspace = DEFAULT_WORKSPACE
  if (target) {
    const { rows } = await pool.query<{ id: string }>(
      'select id from organization where slug = $1', [target])
    if (!rows[0]) throw new Error(`no workspace with slug "${target}"`)
    workspace = rows[0].id
  }

  const index = JSON.parse(
    await readFile(join(config.docsDir, 'examples', 'index.json'), 'utf8')) as Entry[]

  let ok = 0
  const missing: string[] = []
  for (const entry of index) {
    // the library is split across two roots; a film lives in whichever has it
    const doc = await load(config.docsDir, entry.slug)
    if (!doc) { missing.push(entry.slug); continue }
    await pool.query(
      `insert into films (workspace_id, slug, title, grp, stage, anim)
            values ($1, $2, $3, $4, $5, $6)
       on conflict (workspace_id, slug) do update
              set title = excluded.title,
                  grp = excluded.grp,
                  stage = excluded.stage,
                  anim = excluded.anim,
                  updated_at = now()`,
      [
        workspace, entry.slug, entry.title ?? entry.slug,
        isGroup(entry.group) ? entry.group : 'films',
        JSON.stringify(doc.stage), JSON.stringify(doc.anim),
      ],
    )
    ok++
  }

  console.log(`imported ${ok} films into ${target ?? 'the default workspace'}`)
  if (missing.length) console.log(`no files for: ${missing.join(', ')}`)
  await closeDb()
}

async function load(base: string, slug: string) {
  for (const root of [base, join(base, 'examples')]) {
    try {
      const [stage, anim] = await Promise.all([
        readFile(join(root, `${slug}.stage.json`), 'utf8'),
        readFile(join(root, `${slug}.anim.json`), 'utf8'),
      ])
      return { stage: JSON.parse(stage), anim: JSON.parse(anim) }
    } catch { /* try the other root */ }
  }
  return null
}

main().catch(e => { console.error(e.message); process.exit(1) })
