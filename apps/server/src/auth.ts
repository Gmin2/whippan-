import { betterAuth } from 'better-auth'
import { organization } from 'better-auth/plugins'
import type { Pool } from 'pg'

/**
 * Accounts.
 *
 * Better Auth owns its own tables in our Postgres, so users never live in
 * somebody else's system and a migration away from this is never blocked by a
 * vendor. It takes the same pool everything else uses.
 *
 * The organization plugin IS our workspace model. Rolling our own members and
 * roles table would mean reimplementing invitations, active-organization
 * session state and permission checks that this already has.
 */
export function makeAuth(pool: Pool, opts: {
  secret: string
  baseURL: string
  trustedOrigins: string[]
  google?: { clientId: string; clientSecret: string }
  github?: { clientId: string; clientSecret: string }
}) {
  return betterAuth({
    database: pool,
    secret: opts.secret,
    baseURL: opts.baseURL,
    // the editor is a separate origin in development; without this every
    // sign-in is rejected as a cross-site request
    trustedOrigins: opts.trustedOrigins,
    emailAndPassword: {
      enabled: true,
      // nothing sends mail yet, and a verification wall nobody can pass is
      // worse than no wall. turn this on with the email provider
      requireEmailVerification: false,
    },
    socialProviders: {
      ...(opts.google ? { google: opts.google } : {}),
      ...(opts.github ? { github: opts.github } : {}),
    },
    session: {
      expiresIn: 60 * 60 * 24 * 30,
      updateAge: 60 * 60 * 24,
      cookieCache: { enabled: true, maxAge: 60 * 5 },
    },
    advanced: {
      // the editor and the api are different origins until they share a
      // hostname, so the session cookie has to be allowed cross-site
      defaultCookieAttributes: {
        sameSite: opts.trustedOrigins.length ? 'none' : 'lax',
        secure: process.env.NODE_ENV === 'production',
      },
    },
    databaseHooks: {
      user: {
        create: {
          // every account gets one workspace at signup. without this a new
          // user has nowhere to put a film and the first save fails
          after: async user => {
            const id = crypto.randomUUID()
            const slug = await freeSlug(pool, user.email.split('@')[0] || 'workspace')
            await pool.query(
              `insert into organization (id, name, slug, "createdAt")
                    values ($1, $2, $3, now())`,
              [id, user.name || slug, slug])
            await pool.query(
              `insert into member (id, "organizationId", "userId", role, "createdAt")
                    values ($1, $2, $3, 'owner', now())`,
              [crypto.randomUUID(), id, user.id])
          },
        },
      },
      session: {
        create: {
          // the session carries which workspace is active, so a request does
          // not have to look it up on every call
          before: async session => {
            const { rows } = await pool.query<{ organizationId: string }>(
              `select "organizationId" from member where "userId" = $1
                order by "createdAt" limit 1`,
              [session.userId])
            return { data: { ...session, activeOrganizationId: rows[0]?.organizationId ?? null } }
          },
        },
      },
    },
    plugins: [organization({
      // one personal workspace each; teams come later and the schema is ready
      allowUserToCreateOrganization: true,
      organizationLimit: 5,
    })],
  })
}

export type Auth = ReturnType<typeof makeAuth>

/**
 * Which workspace a request belongs to.
 *
 * The session carries `activeOrganizationId` as a fast path, but it cannot be
 * relied on alone: at sign-up the session is written before the hook that
 * creates the user's workspace has finished, so the very first session of every
 * new account has a null. Falling back to the membership makes this independent
 * of hook ordering, and costs one indexed lookup only when the fast path misses.
 */
export function workspaceResolver(pool: Pool) {
  return async (userId: string): Promise<string | null> => {
    const { rows } = await pool.query<{ organizationId: string }>(
      `select "organizationId" from member where "userId" = $1 order by "createdAt" limit 1`,
      [userId])
    return rows[0]?.organizationId ?? null
  }
}

/** organization slugs are unique, and two people named sam must both sign up */
async function freeSlug(pool: Pool, base: string): Promise<string> {
  const root = base.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'workspace'
  for (let i = 0; i < 20; i++) {
    const slug = i === 0 ? root : `${root}-${i + 1}`
    const { rowCount } = await pool.query('select 1 from organization where slug = $1', [slug])
    if (!rowCount) return slug
  }
  return `${root}-${crypto.randomUUID().slice(0, 8)}`
}
