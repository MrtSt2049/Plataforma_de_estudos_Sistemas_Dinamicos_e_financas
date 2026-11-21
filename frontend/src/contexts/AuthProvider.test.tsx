import { act, render, renderHook, screen } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useAuth } from '@/hooks/useAuth'
import { AuthProvider } from './AuthProvider'

const fake = vi.hoisted(() => {
  type Listener = (event: string, session: unknown) => void
  const state: { listener: Listener | null; unsubscribe: () => void } = { listener: null, unsubscribe: () => {} }
  const auth = {
    onAuthStateChange: vi.fn(),
    signInWithPassword: vi.fn(),
    signUp: vi.fn(),
    signOut: vi.fn(),
    resetPasswordForEmail: vi.fn(),
    updateUser: vi.fn(),
  }
  return { auth, state }
})

vi.mock('@/services/supabase', () => ({ getSupabase: () => ({ auth: fake.auth }) }))

const session = { access_token: 'token', user: { id: 'u1', email: 'a@b.co' } }

function emit(event: string, next: unknown) {
  act(() => fake.state.listener?.(event, next))
}

function wrapper({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>
}

beforeEach(() => {
  fake.state.listener = null
  fake.state.unsubscribe = vi.fn()
  fake.auth.onAuthStateChange.mockImplementation((callback: (event: string, session: unknown) => void) => {
    fake.state.listener = callback
    return { data: { subscription: { unsubscribe: fake.state.unsubscribe } } }
  })
  fake.auth.signInWithPassword.mockResolvedValue({ error: null })
  fake.auth.signUp.mockResolvedValue({ data: { session: null }, error: null })
  fake.auth.signOut.mockResolvedValue({ error: null })
  fake.auth.resetPasswordForEmail.mockResolvedValue({ error: null })
  fake.auth.updateUser.mockResolvedValue({ error: null })
})

describe('AuthProvider', () => {
  it('is not ready until Supabase reports the initial session', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    expect(result.current.ready).toBe(false)
    expect(result.current.session).toBeNull()
    emit('INITIAL_SESSION', null)
    expect(result.current.ready).toBe(true)
    expect(result.current.user).toBeNull()
  })

  it('exposes the session and the user once signed in, and clears them on sign out', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    emit('INITIAL_SESSION', session)
    expect(result.current.user?.email).toBe('a@b.co')
    emit('SIGNED_OUT', null)
    expect(result.current.session).toBeNull()
    expect(result.current.user).toBeNull()
  })

  it('stops listening when it unmounts', () => {
    const { unmount } = renderHook(() => useAuth(), { wrapper })
    unmount()
    expect(fake.state.unsubscribe).toHaveBeenCalledTimes(1)
  })

  it('signs in with the credentials', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    await expect(result.current.signIn('a@b.co', 'senha-forte')).resolves.toEqual({ ok: true })
    expect(fake.auth.signInWithPassword).toHaveBeenCalledWith({ email: 'a@b.co', password: 'senha-forte' })
  })

  it('translates a sign-in error instead of showing the raw one', async () => {
    fake.auth.signInWithPassword.mockResolvedValue({ error: { code: 'invalid_credentials', status: 400, message: 'Invalid login credentials' } })
    const { result } = renderHook(() => useAuth(), { wrapper })
    await expect(result.current.signIn('a@b.co', 'errada')).resolves.toEqual({ ok: false, message: 'E-mail ou senha incorretos.' })
  })

  it('reports that the e-mail must be confirmed when sign-up returns no session', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    await expect(result.current.signUp('a@b.co', 'senha-forte')).resolves.toEqual({ ok: true, needsConfirmation: true })
    expect(fake.auth.signUp).toHaveBeenCalledWith({
      email: 'a@b.co',
      password: 'senha-forte',
      options: { emailRedirectTo: window.location.origin },
    })
  })

  it('does not ask for confirmation when sign-up already returns a session', async () => {
    fake.auth.signUp.mockResolvedValue({ data: { session }, error: null })
    const { result } = renderHook(() => useAuth(), { wrapper })
    await expect(result.current.signUp('a@b.co', 'senha-forte')).resolves.toEqual({ ok: true, needsConfirmation: false })
  })

  it('translates a sign-up error', async () => {
    fake.auth.signUp.mockResolvedValue({ data: { session: null }, error: { code: 'weak_password', status: 422 } })
    const { result } = renderHook(() => useAuth(), { wrapper })
    const outcome = await result.current.signUp('a@b.co', '123')
    expect(outcome.ok).toBe(false)
    if (!outcome.ok) expect(outcome.message).toMatch(/fraca/)
  })

  it('signs out', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    await result.current.signOut()
    expect(fake.auth.signOut).toHaveBeenCalledTimes(1)
  })

  it('asks for the recovery e-mail pointing back at the update page', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    await expect(result.current.requestPasswordReset('a@b.co')).resolves.toEqual({ ok: true })
    expect(fake.auth.resetPasswordForEmail).toHaveBeenCalledWith('a@b.co', {
      redirectTo: `${window.location.origin}/update-password`,
    })
  })

  it('reports a failure to send the recovery e-mail', async () => {
    fake.auth.resetPasswordForEmail.mockResolvedValue({ error: { code: 'over_email_send_rate_limit', status: 429 } })
    const { result } = renderHook(() => useAuth(), { wrapper })
    const outcome = await result.current.requestPasswordReset('a@b.co')
    expect(outcome).toMatchObject({ ok: false })
  })

  it('knows when the user arrives from a recovery link, and forgets it after the password changes', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    emit('PASSWORD_RECOVERY', session)
    expect(result.current.recovering).toBe(true)
    await act(async () => {
      await result.current.updatePassword('nova-senha-forte')
    })
    expect(fake.auth.updateUser).toHaveBeenCalledWith({ password: 'nova-senha-forte' })
    expect(result.current.recovering).toBe(false)
  })

  it('keeps the recovery state when the new password is refused', async () => {
    fake.auth.updateUser.mockResolvedValue({ error: { code: 'same_password', status: 422 } })
    const { result } = renderHook(() => useAuth(), { wrapper })
    emit('PASSWORD_RECOVERY', session)
    let outcome: Awaited<ReturnType<typeof result.current.updatePassword>> | undefined
    await act(async () => {
      outcome = await result.current.updatePassword('igual')
    })
    expect(outcome).toMatchObject({ ok: false })
    expect(result.current.recovering).toBe(true)
  })

  it('forgets the recovery state on sign out', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    emit('PASSWORD_RECOVERY', session)
    emit('SIGNED_OUT', null)
    expect(result.current.recovering).toBe(false)
  })
})

describe('useAuth', () => {
  it('fails clearly outside the provider', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    function Probe() {
      useAuth()
      return null
    }
    expect(() => render(<Probe />)).toThrow(/inside <AuthProvider>/)
    spy.mockRestore()
    expect(screen.queryByText('x')).not.toBeInTheDocument()
  })
})
