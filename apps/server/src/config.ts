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
  /** azure blob when there is a connection string, a directory otherwise */
  storage: { connection: string | null; dir: string }
  /** accounts are off until a session secret is set */
  auth: {
    secret: string
    baseURL: string
    trustedOrigins: string[]
    google?: { clientId: string; clientSecret: string }
    github?: { clientId: string; clientSecret: string }
  } | null
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
    storage: {
      connection: process.env.STORAGE_CONNECTION?.trim() || null,
      dir: process.env.STORAGE_DIR ?? `${repoRoot}out/blob`,
    },
    auth: authConfig(env),
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


/**
 * Accounts turn on when there is a secret to sign sessions with, and not
 * before. A half-configured auth is worse than none: it would let people sign
 * up into sessions that stop verifying the moment the process restarts.
 */
function authConfig(env: string): Config['auth'] {
  // A development escape hatch, opt-in and never silent. With it set the API
  // mounts no auth at all, /api/me 404s, and the editor takes that to mean
  // "this deployment has no accounts" and skips its sign-in gate entirely —
  // a path that already existed for filesystem mode. Every request then falls
  // through to the default workspace.
  //
  // It throws rather than warns in production, because an auth bypass that
  // degrades quietly is exactly the kind that reaches a deployment.
  if (process.env.WHIPPAN_DEV_NO_AUTH === '1') {
    if (env === 'production') {
      throw new Error('WHIPPAN_DEV_NO_AUTH cannot be set in production')
    }
    return null
  }

  const secret = process.env.BETTER_AUTH_SECRET?.trim()
  if (!secret) return null
  if (env === 'production' && secret.length < 32) {
    throw new Error('BETTER_AUTH_SECRET must be at least 32 characters in production')
  }
  const pair = (a?: string, b?: string) =>
    a?.trim() && b?.trim() ? { clientId: a.trim(), clientSecret: b.trim() } : undefined
  return {
    secret,
    baseURL: process.env.BETTER_AUTH_URL?.trim()
      || `http://localhost:${process.env.PORT ?? 8903}`,
    // the editor's origins, which are allowed to hold a session cookie
    trustedOrigins: (process.env.AUTH_TRUSTED_ORIGINS ?? '')
      .split(',').map(s => s.trim()).filter(Boolean),
    google: pair(process.env.GOOGLE_CLIENT_ID, process.env.GOOGLE_CLIENT_SECRET),
    github: pair(process.env.GITHUB_CLIENT_ID, process.env.GITHUB_CLIENT_SECRET),
  }
}
