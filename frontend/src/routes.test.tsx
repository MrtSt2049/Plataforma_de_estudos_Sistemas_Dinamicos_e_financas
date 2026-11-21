import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AppRoutes } from '@/routes'
import { ApiError } from '@/services/apiClient'
import { fakeSession, renderWithAuth } from '@/test/renderWithAuth'

const health = vi.hoisted(() => ({
  current: { status: 'pending', data: undefined, error: null, refetch: () => {} } as {
    status: 'pending' | 'error' | 'success'
    data: { status: string; version: string } | undefined
    error: unknown
    refetch: () => unknown
  },
}))

vi.mock('@/hooks/useHealth', () => ({ useHealth: () => health.current }))

beforeEach(() => {
  health.current = { status: 'success', data: { status: 'ok', version: '0.2.0' }, error: null, refetch: () => {} }
})

describe('route guards', () => {
  it('shows a placeholder, not the login page, while the session is being checked', () => {
    renderWithAuth(<AppRoutes />, { route: '/', auth: { ready: false } })
    expect(screen.getByRole('status', { name: 'Verificando sessão' })).toBeInTheDocument()
    expect(screen.queryByText('Entrar')).not.toBeInTheDocument()
  })

  it('sends visitors without a session to the login page', async () => {
    renderWithAuth(<AppRoutes />, { route: '/' })
    expect(await screen.findByRole('heading', { name: 'Entrar' })).toBeInTheDocument()
  })

  it('lets a signed-in user see the app', async () => {
    renderWithAuth(<AppRoutes />, { route: '/', auth: { session: fakeSession(), user: fakeSession().user } })
    expect(await screen.findByRole('heading', { name: 'Visão geral' })).toBeInTheDocument()
  })

  it.each(['/login', '/signup', '/forgot-password'])('sends a signed-in user away from %s', async (route) => {
    renderWithAuth(<AppRoutes />, { route, auth: { session: fakeSession(), user: fakeSession().user } })
    expect(await screen.findByRole('heading', { name: 'Visão geral' })).toBeInTheDocument()
  })

  it('sends a user who opened a recovery link to the new-password page', async () => {
    renderWithAuth(<AppRoutes />, { route: '/login', auth: { session: fakeSession(), user: fakeSession().user, recovering: true } })
    expect(await screen.findByRole('heading', { name: 'Nova senha' })).toBeInTheDocument()
  })

  it('protects the new-password page from visitors', async () => {
    renderWithAuth(<AppRoutes />, { route: '/update-password' })
    expect(await screen.findByRole('heading', { name: 'Entrar' })).toBeInTheDocument()
  })

  it('shows a not-found page for unknown addresses', async () => {
    renderWithAuth(<AppRoutes />, { route: '/nao-existe' })
    expect(await screen.findByText('Página não encontrada')).toBeInTheDocument()
  })
})

describe('app shell', () => {
  const signedIn = { session: fakeSession('ana@example.com'), user: fakeSession('ana@example.com').user }

  it('shows the user and signs out', async () => {
    const { auth } = renderWithAuth(<AppRoutes />, { route: '/', auth: signedIn })
    expect((await screen.findAllByText('ana@example.com')).length).toBeGreaterThan(0)
    await userEvent.click(screen.getByRole('button', { name: 'Sair' }))
    expect(auth.signOut).toHaveBeenCalledTimes(1)
  })

  it('lists only the screens that exist as links, and marks the rest as coming soon', async () => {
    renderWithAuth(<AppRoutes />, { route: '/', auth: signedIn })
    const nav = (await screen.findAllByRole('navigation', { name: 'Principal' }))[0]
    expect(nav).toBeDefined()
    expect(screen.getAllByRole('link', { name: /Visão geral/ }).length).toBeGreaterThan(0)
    expect(screen.queryByRole('link', { name: /Dados de mercado/ })).not.toBeInTheDocument()
    expect(screen.getAllByText('Dados de mercado')[0]?.closest('[aria-disabled="true"]')).not.toBeNull()
  })

  it('opens and closes the menu on small screens', async () => {
    renderWithAuth(<AppRoutes />, { route: '/', auth: signedIn })
    const open = await screen.findByRole('button', { name: 'Abrir menu' })
    expect(open).toHaveAttribute('aria-expanded', 'false')
    await userEvent.click(open)
    expect(screen.getByRole('button', { name: 'Abrir menu' })).toHaveAttribute('aria-expanded', 'true')
    await userEvent.click(screen.getByRole('button', { name: 'Fechar menu' }))
    expect(screen.queryByRole('button', { name: 'Fechar menu' })).not.toBeInTheDocument()
  })

  it('closes the menu after navigating', async () => {
    renderWithAuth(<AppRoutes />, { route: '/', auth: signedIn })
    await userEvent.click(await screen.findByRole('button', { name: 'Abrir menu' }))
    const links = screen.getAllByRole('link', { name: /Visão geral/ })
    await userEvent.click(links[links.length - 1] as HTMLElement)
    expect(screen.queryByRole('button', { name: 'Fechar menu' })).not.toBeInTheDocument()
  })
})

describe('overview: the four states', () => {
  const signedIn = { session: fakeSession(), user: fakeSession().user }

  it('loading', async () => {
    health.current = { status: 'pending', data: undefined, error: null, refetch: () => {} }
    renderWithAuth(<AppRoutes />, { route: '/', auth: signedIn })
    expect(await screen.findByRole('status', { name: 'Carregando' })).toBeInTheDocument()
  })

  it('success', async () => {
    renderWithAuth(<AppRoutes />, { route: '/', auth: signedIn })
    expect(await screen.findByText('0.2.0')).toBeInTheDocument()
  })

  it('error, with a retry', async () => {
    const refetch = vi.fn()
    health.current = { status: 'error', data: undefined, error: new ApiError('A API respondeu com erro 503.', 503, 'http_error'), refetch }
    renderWithAuth(<AppRoutes />, { route: '/', auth: signedIn })
    expect(await screen.findByText('A API respondeu com erro 503.')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Tentar de novo' }))
    expect(refetch).toHaveBeenCalledTimes(1)
  })

  it('empty: the API is not configured yet', async () => {
    health.current = { status: 'error', data: undefined, error: new ApiError('x', 0, 'api_not_configured'), refetch: () => {} }
    renderWithAuth(<AppRoutes />, { route: '/', auth: signedIn })
    expect(await screen.findByText('API não configurada')).toBeInTheDocument()
    expect(screen.getByText(/VITE_API_BASE_URL/)).toBeInTheDocument()
  })

  it('shows the empty experiments panel and never synthetic numbers', async () => {
    renderWithAuth(<AppRoutes />, { route: '/', auth: signedIn })
    expect(await screen.findByText('Nenhum experimento ainda')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Novo experimento' })).toBeDisabled()
    expect(screen.queryByText('DEMO')).not.toBeInTheDocument()
  })
})
