import { useEffect, useState } from 'react'
import { oauthUrl, signIn, signUp } from '../api'

interface Props {
  /** which providers the server actually has credentials for */
  providers: ('google' | 'github')[]
  onDone(): void
}

/**
 * The gate.
 *
 * Deliberately the same surface as the rest of the editor rather than a
 * marketing page: the panel colour, the 12px type, the inset controls. The
 * first thing someone sees should look like the thing they came for.
 */
export default function SignIn({ providers, onDone }: Props) {
  const [mode, setMode] = useState<'in' | 'up'>('in')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => { setError(null) }, [mode])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      if (mode === 'up') await signUp(email.trim(), password, name.trim() || email.split('@')[0])
      else await signIn(email.trim(), password)
      onDone()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setBusy(false)
    }
  }

  const ok = /.+@.+\..+/.test(email) && password.length >= 8

  return (
    <div className="grid h-full w-full place-items-center bg-panel">
      <div className="w-[320px]">
        <div className="mb-6">
          <p className="text-[20px] font-medium">whippan</p>
          <p className="text-dim">json in, launch film out</p>
        </div>

        <div className="overflow-hidden rounded-[10px] border border-black/10 bg-surface">
          <div className="flex border-b border-hair">
            {(['in', 'up'] as const).map(m => (
              <button
                key={m}
                type="button"
                onClick={() => setMode(m)}
                className={`h-[34px] flex-1 transition-colors
                            ${mode === m ? 'bg-black/[0.045] font-medium' : 'text-dim hover:text-ink'}`}
              >
                {m === 'in' ? 'Sign in' : 'Create account'}
              </button>
            ))}
          </div>

          <form onSubmit={submit} className="space-y-2 p-3">
            {mode === 'up' && (
              <input
                value={name} onChange={e => setName(e.target.value)}
                placeholder="name" autoComplete="name"
                className="inset-control h-[30px] w-full bg-surface px-2 outline-none"
              />
            )}
            <input
              value={email} onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com" type="email" autoComplete="email" autoFocus
              className="inset-control h-[30px] w-full bg-surface px-2 outline-none"
            />
            <input
              value={password} onChange={e => setPassword(e.target.value)}
              placeholder="password" type="password"
              autoComplete={mode === 'up' ? 'new-password' : 'current-password'}
              className="inset-control h-[30px] w-full bg-surface px-2 outline-none"
            />
            {mode === 'up' && password.length > 0 && password.length < 8 && (
              <p className="text-[10px] text-faint">at least 8 characters</p>
            )}
            {error && (
              <p className="leading-relaxed text-[11px] text-[#c0392b]">{error}</p>
            )}
            <button
              type="submit" disabled={!ok || busy}
              className="h-[30px] w-full rounded-[6px] bg-[#5e92f4] text-white
                         transition-colors hover:bg-[#4d82e8] disabled:opacity-40"
            >
              {busy ? 'one moment' : mode === 'in' ? 'Sign in' : 'Create account'}
            </button>
          </form>

          {providers.length > 0 && (
            <div className="border-t border-hair p-3">
              <div className="grid gap-1.5" style={{
                gridTemplateColumns: `repeat(${providers.length}, minmax(0, 1fr))`,
              }}>
                {providers.map(p => (
                  <a
                    key={p}
                    href={oauthUrl(p, location.href)}
                    className="inset-control grid h-[30px] place-items-center capitalize
                               transition-colors hover:bg-black/[0.03]"
                  >
                    {p}
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>

        <p className="mt-3 leading-relaxed text-[10px] text-faint">
          your films are private to your workspace
        </p>
      </div>
    </div>
  )
}
