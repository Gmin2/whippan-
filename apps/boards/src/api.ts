/**
 * Every call to our own API goes through here.
 *
 * The editor and the API are separate origins, so the session cookie only
 * travels with `credentials: 'include'`. Putting that in one place rather than
 * on ten call sites means a new endpoint cannot quietly forget it and get a 401
 * that looks like a bug in the endpoint.
 */
export const API = import.meta.env.VITE_API_BASE ?? ''

export function api(path: string, init?: RequestInit): Promise<Response> {
  return fetch(`${API}${path}`, { ...init, credentials: 'include' })
}

/** the API's answer to "who is this", or null when nobody is signed in */
export interface Me {
  user: { id: string; email: string; name: string; image: string | null } | null
  workspace: string | null
  /** the social providers this deployment actually has credentials for */
  providers: ('google' | 'github')[]
}

/** null when this deployment has no accounts at all, as in local development */
export async function session(): Promise<Me | null> {
  const res = await api('/api/me')
  if (res.status === 404) return null
  if (!res.ok) throw new Error(`session: ${res.status}`)
  return await res.json() as Me
}

export async function signIn(email: string, password: string): Promise<void> {
  await post('/api/auth/sign-in/email', { email, password })
}

export async function signUp(email: string, password: string, name: string): Promise<void> {
  await post('/api/auth/sign-up/email', { email, password, name })
}

export async function signOut(): Promise<void> {
  await api('/api/auth/sign-out', { method: 'POST' })
}

/** where the browser goes to hand off to google or github */
export const oauthUrl = (provider: 'google' | 'github', next: string) =>
  `${API}/api/auth/sign-in/social?provider=${provider}&callbackURL=${encodeURIComponent(next)}`

async function post(path: string, body: unknown): Promise<void> {
  const res = await api(path, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (res.ok) return
  const out = await res.json().catch(() => ({})) as { message?: string; error?: string }
  // better auth reports the useful part in `message`
  throw new Error(out.message || out.error || `sign in failed (${res.status})`)
}
