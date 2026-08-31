import { readdir, readFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { join } from 'node:path'
import type { Pool } from 'pg'

/**
 * Migrations, applied in filename order and recorded so they run once.
 *
 * Deliberately not a migration framework: the whole feature is "run the .sql
 * files nobody has run yet, in a transaction, and write down which". A tool
 * that does this plus branching and rollbacks would be more to learn than the
 * problem is worth at this size.
 */
const DIR = fileURLToPath(new URL('../../migrations/', import.meta.url))

export async function migrate(pool: Pool): Promise<string[]> {
  await pool.query(`
    create table if not exists migrations (
      name       text primary key,
      applied_at timestamptz not null default now()
    )`)

  const done = new Set(
    (await pool.query<{ name: string }>('select name from migrations')).rows.map(r => r.name))
  const files = (await readdir(DIR)).filter(f => f.endsWith('.sql')).sort()
  const ran: string[] = []

  for (const file of files) {
    if (done.has(file)) continue
    const sql = await readFile(join(DIR, file), 'utf8')
    const client = await pool.connect()
    try {
      // a half-applied migration is worse than none, so each file is one
      // transaction and a failure leaves the database exactly as it was
      await client.query('begin')
      await client.query(sql)
      await client.query('insert into migrations (name) values ($1)', [file])
      await client.query('commit')
      ran.push(file)
    } catch (e) {
      await client.query('rollback')
      throw new Error(`migration ${file} failed: ${e instanceof Error ? e.message : e}`)
    } finally {
      client.release()
    }
  }
  return ran
}
