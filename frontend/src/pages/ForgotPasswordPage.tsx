import { useState, type SubmitEvent } from 'react'
import { Link } from 'react-router-dom'
import { AuthLayout } from '@/components/layout/AuthLayout'
import { Button } from '@/components/ui/Button'
import { ErrorState } from '@/components/ui/ErrorState'
import { Input } from '@/components/ui/Input'
import { useAuth } from '@/hooks/useAuth'
import { emailError } from '@/lib/validation'

export default function ForgotPasswordPage() {
  const { requestPasswordReset } = useAuth()
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [busy, setBusy] = useState(false)
  const [failure, setFailure] = useState<string | null>(null)
  const [sent, setSent] = useState(false)

  const emailProblem = submitted ? emailError(email) : undefined
  const back = (
    <Link to="/login" className="text-analytic-text underline">
      Voltar para entrar
    </Link>
  )

  async function onSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitted(true)
    setFailure(null)
    if (emailError(email)) return
    setBusy(true)
    const result = await requestPasswordReset(email.trim())
    setBusy(false)
    if (result.ok) setSent(true)
    else setFailure(result.message)
  }

  if (sent) {
    return (
      <AuthLayout title="Verifique seu e-mail" footer={back}>
        {/* The same text whether or not the address exists, so the page does not reveal who has an account. */}
        <p role="status">Se o endereço informado tiver uma conta, enviamos um link para criar uma nova senha.</p>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout title="Recuperar senha" footer={back}>
      <form onSubmit={(event) => void onSubmit(event)} noValidate className="flex flex-col gap-4">
        <Input
          label="E-mail"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          {...(emailProblem ? { error: emailProblem } : {})}
        />
        {failure && <ErrorState title="Não foi possível enviar" message={failure} />}
        <Button type="submit" loading={busy}>
          Enviar link
        </Button>
      </form>
    </AuthLayout>
  )
}
