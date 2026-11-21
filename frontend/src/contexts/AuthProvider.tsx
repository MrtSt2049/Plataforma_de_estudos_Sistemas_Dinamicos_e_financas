import type { Session } from '@supabase/supabase-js'
import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { authErrorMessage } from '@/lib/authMessages'
import { getSupabase } from '@/services/supabase'
import { AuthContext, type AuthContextValue } from './AuthContext'

/**
 * Holds the Supabase session for the whole app.
 *
 * The screens only use it for the experience (what to show). Authorization is the
 * backend's job: it validates the token on every request (RULE 025).
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null)
  const [ready, setReady] = useState(false)
  const [recovering, setRecovering] = useState(false)

  useEffect(() => {
    // Supabase emits INITIAL_SESSION right after subscribing, so this one listener is
    // the single source of truth. Nothing else is called from inside the callback.
    const { data } = getSupabase().auth.onAuthStateChange((event, next) => {
      setSession(next)
      setReady(true)
      if (event === 'PASSWORD_RECOVERY') setRecovering(true)
      if (event === 'SIGNED_OUT') setRecovering(false)
    })
    return () => data.subscription.unsubscribe()
  }, [])

  const value = useMemo<AuthContextValue>(() => {
    const auth = getSupabase().auth
    return {
      ready,
      session,
      user: session?.user ?? null,
      recovering,
      signIn: async (email, password) => {
        const { error } = await auth.signInWithPassword({ email, password })
        return error ? { ok: false, message: authErrorMessage(error) } : { ok: true }
      },
      signUp: async (email, password) => {
        const { data, error } = await auth.signUp({
          email,
          password,
          options: { emailRedirectTo: window.location.origin },
        })
        if (error) return { ok: false, message: authErrorMessage(error) }
        // With e-mail confirmation on, no session comes back until the link is opened.
        return { ok: true, needsConfirmation: data.session === null }
      },
      signOut: async () => {
        await auth.signOut()
      },
      requestPasswordReset: async (email) => {
        const { error } = await auth.resetPasswordForEmail(email, {
          redirectTo: `${window.location.origin}/update-password`,
        })
        return error ? { ok: false, message: authErrorMessage(error) } : { ok: true }
      },
      updatePassword: async (password) => {
        const { error } = await auth.updateUser({ password })
        if (error) return { ok: false, message: authErrorMessage(error) }
        setRecovering(false)
        return { ok: true }
      },
    }
  }, [ready, session, recovering])

  return <AuthContext value={value}>{children}</AuthContext>
}
