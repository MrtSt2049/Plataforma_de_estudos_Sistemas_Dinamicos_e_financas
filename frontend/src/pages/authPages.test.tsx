import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { renderWithAuth } from '@/test/renderWithAuth'
import ForgotPasswordPage from './ForgotPasswordPage'
import LoginPage from './LoginPage'
import SignupPage from './SignupPage'
import UpdatePasswordPage from './UpdatePasswordPage'

describe('LoginPage', () => {
  it('asks for valid fields before calling the server', async () => {
    const { auth } = renderWithAuth(<LoginPage />)
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))
    expect(await screen.findByText('Informe um e-mail válido.')).toBeInTheDocument()
    expect(screen.getByText('Informe a senha.')).toBeInTheDocument()
    expect(auth.signIn).not.toHaveBeenCalled()
  })

  it('signs in with the trimmed e-mail', async () => {
    const { auth } = renderWithAuth(<LoginPage />)
    await userEvent.type(screen.getByLabelText('E-mail'), '  a@b.co ')
    await userEvent.type(screen.getByLabelText('Senha'), 'senha-forte')
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))
    expect(auth.signIn).toHaveBeenCalledWith('a@b.co', 'senha-forte')
  })

  it('shows the failure and lets the user try again', async () => {
    const signIn = vi.fn(() => Promise.resolve({ ok: false as const, message: 'E-mail ou senha incorretos.' }))
    renderWithAuth(<LoginPage />, { auth: { signIn } })
    await userEvent.type(screen.getByLabelText('E-mail'), 'a@b.co')
    await userEvent.type(screen.getByLabelText('Senha'), 'errada')
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('E-mail ou senha incorretos.')
    expect(screen.getByRole('button', { name: 'Entrar' })).toBeEnabled()
  })

  it('blocks a second submit while the first one runs', async () => {
    let finish: (value: { ok: true }) => void = () => {}
    const signIn = vi.fn(() => new Promise<{ ok: true }>((resolve) => (finish = resolve)))
    renderWithAuth(<LoginPage />, { auth: { signIn } })
    await userEvent.type(screen.getByLabelText('E-mail'), 'a@b.co')
    await userEvent.type(screen.getByLabelText('Senha'), 'senha-forte')
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))
    expect(screen.getByRole('button', { name: 'Entrar' })).toBeDisabled()
    finish({ ok: true })
    await waitFor(() => expect(screen.getByRole('button', { name: 'Entrar' })).toBeEnabled())
    expect(signIn).toHaveBeenCalledTimes(1)
  })

  it('links to sign-up and to password recovery', () => {
    renderWithAuth(<LoginPage />)
    expect(screen.getByRole('link', { name: 'Criar conta' })).toHaveAttribute('href', '/signup')
    expect(screen.getByRole('link', { name: 'Esqueci minha senha' })).toHaveAttribute('href', '/forgot-password')
  })
})

describe('SignupPage', () => {
  async function fill(email: string, password: string, confirmation: string) {
    await userEvent.type(screen.getByLabelText('E-mail'), email)
    await userEvent.type(screen.getByLabelText('Senha'), password)
    await userEvent.type(screen.getByLabelText('Repita a senha'), confirmation)
    await userEvent.click(screen.getByRole('button', { name: 'Criar conta' }))
  }

  it('validates the fields and the confirmation without calling the server', async () => {
    const { auth } = renderWithAuth(<SignupPage />)
    await fill('ruim', 'curta', 'outra')
    expect(await screen.findByText('Informe um e-mail válido.')).toBeInTheDocument()
    expect(screen.getAllByText(/Use pelo menos 8 caracteres/).length).toBeGreaterThan(0)
    expect(screen.getByText('As senhas não são iguais.')).toBeInTheDocument()
    expect(auth.signUp).not.toHaveBeenCalled()
  })

  it('asks the user to confirm the e-mail without revealing whether the account exists', async () => {
    const { auth } = renderWithAuth(<SignupPage />)
    await fill('a@b.co', 'senha-forte', 'senha-forte')
    expect(auth.signUp).toHaveBeenCalledWith('a@b.co', 'senha-forte')
    expect(await screen.findByRole('status')).toHaveTextContent('Se o endereço a@b.co puder receber uma conta')
  })

  it('shows the failure', async () => {
    const signUp = vi.fn(() => Promise.resolve({ ok: false as const, message: 'O cadastro está desativado neste ambiente.' }))
    renderWithAuth(<SignupPage />, { auth: { signUp } })
    await fill('a@b.co', 'senha-forte', 'senha-forte')
    expect(await screen.findByRole('alert')).toHaveTextContent('desativado')
  })

  it('does not show the confirmation notice when no confirmation is needed', async () => {
    const signUp = vi.fn(() => Promise.resolve({ ok: true as const, needsConfirmation: false }))
    renderWithAuth(<SignupPage />, { auth: { signUp } })
    await fill('a@b.co', 'senha-forte', 'senha-forte')
    await waitFor(() => expect(signUp).toHaveBeenCalled())
    expect(screen.queryByText(/Confirme seu e-mail/)).not.toBeInTheDocument()
  })
})

describe('ForgotPasswordPage', () => {
  it('validates the e-mail', async () => {
    const { auth } = renderWithAuth(<ForgotPasswordPage />)
    await userEvent.click(screen.getByRole('button', { name: 'Enviar link' }))
    expect(await screen.findByText('Informe um e-mail válido.')).toBeInTheDocument()
    expect(auth.requestPasswordReset).not.toHaveBeenCalled()
  })

  it('gives the same answer whether or not the account exists', async () => {
    const { auth } = renderWithAuth(<ForgotPasswordPage />)
    await userEvent.type(screen.getByLabelText('E-mail'), 'alguem@example.com')
    await userEvent.click(screen.getByRole('button', { name: 'Enviar link' }))
    expect(auth.requestPasswordReset).toHaveBeenCalledWith('alguem@example.com')
    expect(await screen.findByRole('status')).toHaveTextContent('Se o endereço informado tiver uma conta')
  })

  it('shows a failure to send', async () => {
    const requestPasswordReset = vi.fn(() => Promise.resolve({ ok: false as const, message: 'Muitas tentativas em pouco tempo.' }))
    renderWithAuth(<ForgotPasswordPage />, { auth: { requestPasswordReset } })
    await userEvent.type(screen.getByLabelText('E-mail'), 'a@b.co')
    await userEvent.click(screen.getByRole('button', { name: 'Enviar link' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Muitas tentativas')
  })
})

describe('UpdatePasswordPage', () => {
  it('sends anyone who did not come from a recovery link back to the start', () => {
    renderWithAuth(<UpdatePasswordPage />, { route: '/update-password', auth: { recovering: false } })
    expect(screen.queryByLabelText('Nova senha')).not.toBeInTheDocument()
  })

  it('validates the new password and its confirmation', async () => {
    const { auth } = renderWithAuth(<UpdatePasswordPage />, { auth: { recovering: true } })
    await userEvent.type(screen.getByLabelText('Nova senha'), 'curta')
    await userEvent.type(screen.getByLabelText('Repita a nova senha'), 'outra')
    await userEvent.click(screen.getByRole('button', { name: 'Salvar senha' }))
    expect(await screen.findByText('As senhas não são iguais.')).toBeInTheDocument()
    expect(auth.updatePassword).not.toHaveBeenCalled()
  })

  it('saves the new password', async () => {
    const { auth } = renderWithAuth(<UpdatePasswordPage />, { auth: { recovering: true } })
    await userEvent.type(screen.getByLabelText('Nova senha'), 'nova-senha-forte')
    await userEvent.type(screen.getByLabelText('Repita a nova senha'), 'nova-senha-forte')
    await userEvent.click(screen.getByRole('button', { name: 'Salvar senha' }))
    expect(auth.updatePassword).toHaveBeenCalledWith('nova-senha-forte')
    expect(await screen.findByText('Sua senha foi alterada.')).toBeInTheDocument()
  })

  it('shows why the password was refused', async () => {
    const updatePassword = vi.fn(() => Promise.resolve({ ok: false as const, message: 'A nova senha precisa ser diferente da atual.' }))
    renderWithAuth(<UpdatePasswordPage />, { auth: { recovering: true, updatePassword } })
    await userEvent.type(screen.getByLabelText('Nova senha'), 'senha-igual-1')
    await userEvent.type(screen.getByLabelText('Repita a nova senha'), 'senha-igual-1')
    await userEvent.click(screen.getByRole('button', { name: 'Salvar senha' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('diferente da atual')
  })
})
