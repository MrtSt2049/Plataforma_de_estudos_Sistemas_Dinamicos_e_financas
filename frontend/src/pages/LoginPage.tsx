import { useState, type SubmitEvent } from 'react'
import { Link } from 'react-router-dom'
import { AuthLayout } from '@/components/layout/AuthLayout'
import { Button } from '@/components/ui/Button'
import { ErrorState } from '@/components/ui/ErrorState'
import { Input } from '@/components/ui/Input'
import { useAuth } from '@/hooks/useAuth'
import { emailError } from '@/lib/validation'

export default function LoginPage() {
  const { signIn } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [busy, setBusy] = useState(false)
  const [failure, setFailure] = useState<string | null>(null)

  const emailProblem = submitted ? emailError(email) : undefined
  const passwordProblem = submitted && password === '' ? 'Informe a senha.' : undefined

  async function onSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitted(true)
    setFailure(null)
    if (emailError(email) || password === '') return
    setBusy(true)
    const result = await signIn(email.trim(), password)
    setBusy(false)
    // On success the session changes and PublicOnly sends the user into the app.
    if (!result.ok) setFailure(result.message)
  }

  return (
    <AuthLayout
      title="Entrar"
      footer={
        <>
          Ainda não tem conta?{' '}
          <Link to="/signup" className="text-analytic-text underline">
            Criar conta
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
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          {...(passwordProblem ? { error: passwordProblem } : {})}
        />
        {failure && <ErrorState title="Não foi possível entrar" message={failure} />}
        <Button type="submit" loading={busy}>
          Entrar
        </Button>
        <Link to="/forgot-password" className="text-center text-fg-muted underline">
          Esqueci minha senha
        </Link>
      </form>
    </AuthLayout>
  )
}
