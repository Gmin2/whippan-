import { fileURLToPath } from 'node:url'

// a .env beside the service, if there is one. real environment always wins, so
// a container that sets its own variables is unaffected. loaded here rather
// than in the server entry point so scripts and migrations get it too
try {
  process.loadEnvFile(fileURLToPath(new URL('../.env', import.meta.url)))
} catch {
  // no .env is the normal case in production
}

/** everything the service needs, read once from the environment */
export interface Config {
  port: number
  export: {
    /** the compiled native renderer */
    bin: string
    /** it resolves fonts relative to its working directory */
    cwd: string
    outDir: string
    concurrency: number
    timeoutMs: number
    retentionMs: number
  }
  /** where films are stored; a repo checkout locally, a volume in a container */
  docsDir: string
  /** when set, films come from postgres and docsDir is only used by the importer */
  databaseUrl: string | null
  /** allowed browser origins; '*' in development, an explicit list in production */
  corsOrigins: string[]
  env: 'development' | 'production'
}

const repoDocs = fileURLToPath(new URL('../../../docs/', import.meta.url))
const repoRoot = fileURLToPath(new URL('../../../', import.meta.url))

export function loadConfig(): Config {
  const env = process.env.NODE_ENV === 'production' ? 'production' : 'development'
  return {
    port: Number(process.env.PORT ?? 8903),
    docsDir: process.env.DOCS_DIR ?? repoDocs,
    databaseUrl: process.env.DATABASE_URL?.trim() || null,
    corsOrigins: (process.env.CORS_ORIGINS ?? (env === 'production' ? '' : '*'))
      .split(',').map(s => s.trim()).filter(Boolean),
    env,
    export: {
      bin: process.env.EXPORT_BIN ?? `${repoRoot}target/release/export`,
      cwd: process.env.EXPORT_CWD ?? repoRoot,
      outDir: process.env.EXPORT_DIR ?? `${repoRoot}out/exports`,
      // rendering saturates a core; more than a couple in parallel just makes
      // every one of them slower
      concurrency: Number(process.env.EXPORT_CONCURRENCY ?? 2),
      timeoutMs: Number(process.env.EXPORT_TIMEOUT_MS ?? 10 * 60_000),
      retentionMs: Number(process.env.EXPORT_RETENTION_MS ?? 6 * 60 * 60_000),
    },
  }
}
