import { useState, type SubmitEvent } from 'react'
import { Link } from 'react-router-dom'
import { AuthLayout } from '@/components/layout/AuthLayout'
import { Button } from '@/components/ui/Button'
import { ErrorState } from '@/components/ui/ErrorState'
import { Input } from '@/components/ui/Input'
import { useAuth } from '@/hooks/useAuth'
import { emailError, passwordError } from '@/lib/validation'

export default function SignupPage() {
  const { signUp } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [busy, setBusy] = useState(false)
  const [failure, setFailure] = useState<string | null>(null)
  const [checkEmail, setCheckEmail] = useState(false)

  const emailProblem = submitted ? emailError(email) : undefined
  const passwordProblem = submitted ? passwordError(password) : undefined
  const confirmationProblem = submitted && confirmation !== password ? 'As senhas não são iguais.' : undefined

  async function onSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitted(true)
    setFailure(null)
    if (emailError(email) || passwordError(password) || confirmation !== password) return
    setBusy(true)
    const result = await signUp(email.trim(), password)
    setBusy(false)
    if (!result.ok) setFailure(result.message)
    else if (result.needsConfirmation) setCheckEmail(true)
    // Without confirmation a session exists already, and PublicOnly takes over.
  }

  if (checkEmail) {
    return (
      <AuthLayout
        title="Confirme seu e-mail"
        footer={
          <Link to="/login" className="text-analytic-text underline">
            Voltar para entrar
          </Link>
        }
      >
        <p role="status">
          Se o endereço <strong className="text-fg">{email.trim()}</strong> puder receber uma conta, enviamos um link de
          confirmação. Abra o e-mail e clique no link para ativar o acesso.
        </p>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout
      title="Criar conta"
      footer={
        <>
          Já tem conta?{' '}
          <Link to="/login" className="text-analytic-text underline">
            Entrar
          </Link>
        </>
      }
    >
      <form onSubmit={(event) => void onSubmit(event)} noValidate className="flex flex-col gap-4">
        <Input
          label="E-mail"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          {...(emailProblem ? { error: emailProblem } : {})}
        />
        <Input
          label="Senha"
          type="password"
          autoComplete="new-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          hint="Pelo menos 8 caracteres."
          {...(passwordProblem ? { error: passwordProblem } : {})}
        />
        <Input
          label="Repita a senha"
          type="password"
          autoComplete="new-password"
          value={confirmation}
          onChange={(event) => setConfirmation(event.target.value)}
          {...(confirmationProblem ? { error: confirmationProblem } : {})}
        />
        {failure && <ErrorState title="Não foi possível criar a conta" message={failure} />}
        <Button type="submit" loading={busy}>
          Criar conta
        </Button>
      </form>
    </AuthLayout>
  )
}
