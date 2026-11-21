import { render } from '@testing-library/react'
import type { ReactElement } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { vi } from 'vitest'
import { AuthContext, type AuthContextValue } from '@/contexts/AuthContext'
import { createQueryClient } from '@/queryClient'

export function fakeAuth(overrides: Partial<AuthContextValue> = {}): AuthContextValue {
  return {
    ready: true,
    session: null,
    user: null,
    recovering: false,
    signIn: vi.fn(() => Promise.resolve({ ok: true as const })),
    signUp: vi.fn(() => Promise.resolve({ ok: true as const, needsConfirmation: true })),
    signOut: vi.fn(() => Promise.resolve()),
    requestPasswordReset: vi.fn(() => Promise.resolve({ ok: true as const })),
    updatePassword: vi.fn(() => Promise.resolve({ ok: true as const })),
    ...overrides,
  }
}

/** A signed-in session, with only the fields the screens read. */
export function fakeSession(email = 'pesquisadora@example.com'): NonNullable<AuthContextValue['session']> {
  const user = { id: 'user-1', email } as NonNullable<AuthContextValue['user']>
  return { access_token: 'token', user } as NonNullable<AuthContextValue['session']>
}

export function renderWithAuth(
  ui: ReactElement,
  options: { auth?: Partial<AuthContextValue>; route?: string | { pathname: string; state?: unknown } } = {},
) {
  const auth = fakeAuth(options.auth)
  const queryClient = createQueryClient()
  const result = render(
    <QueryClientProvider client={queryClient}>
      <AuthContext value={auth}>
        <MemoryRouter initialEntries={[options.route ?? '/']}>{ui}</MemoryRouter>
      </AuthContext>
    </QueryClientProvider>,
  )
  return { auth, ...result }
}
