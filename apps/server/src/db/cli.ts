import { db, closeDb } from './pool.js'
import { migrate } from './migrate.js'
import { loadConfig } from '../config.js'

/** apply any migrations this database has not seen: `npm run migrate` */
const config = loadConfig()
if (!config.databaseUrl) {
  console.error('DATABASE_URL is not set')
  process.exit(1)
}
const pool = db(config.databaseUrl)
try {
  const ran = await migrate(pool)
  console.log(ran.length ? `applied: ${ran.join(', ')}` : 'up to date')
} catch (e) {
  // not e.message: a failed connection surfaces as an AggregateError whose own
  // message is empty, which printed nothing at all and looked like a hang
  console.error(e)
  process.exitCode = 1
} finally {
  await closeDb()
}
