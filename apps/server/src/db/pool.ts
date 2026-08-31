import { Pool } from 'pg'

/**
 * One pool for the process.
 *
 * Container Apps scales to zero, so a cold instance opens connections and a
 * scaled-down one drops them. The pool is kept small deliberately: a burstable
 * Postgres has a low connection ceiling and several idle app replicas each
 * holding ten connections will exhaust it long before traffic does.
 */
let pool: Pool | null = null

export function db(url: string): Pool {
  if (pool) return pool
  pool = new Pool({
    connectionString: url,
    max: Number(process.env.PG_MAX ?? 5),
    idleTimeoutMillis: 30_000,
    connectionTimeoutMillis: 10_000,
    // azure postgres requires tls; a local container does not offer it
    ssl: /\bsslmode=require\b/.test(url) ? { rejectUnauthorized: false } : undefined,
  })
  pool.on('error', e => console.error('postgres pool error:', e.message))
  return pool
}

export async function closeDb(): Promise<void> {
  await pool?.end()
  pool = null
}
