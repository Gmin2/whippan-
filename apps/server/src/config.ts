import { fileURLToPath } from 'node:url'

/** everything the service needs, read once from the environment */
export interface Config {
  port: number
  /** where films are stored; a repo checkout locally, a volume in a container */
  docsDir: string
  /** allowed browser origins; '*' in development, an explicit list in production */
  corsOrigins: string[]
  env: 'development' | 'production'
}

const repoDocs = fileURLToPath(new URL('../../../docs/', import.meta.url))

export function loadConfig(): Config {
  const env = process.env.NODE_ENV === 'production' ? 'production' : 'development'
  return {
    port: Number(process.env.PORT ?? 8903),
    docsDir: process.env.DOCS_DIR ?? repoDocs,
    corsOrigins: (process.env.CORS_ORIGINS ?? (env === 'production' ? '' : '*'))
      .split(',').map(s => s.trim()).filter(Boolean),
    env,
  }
}
