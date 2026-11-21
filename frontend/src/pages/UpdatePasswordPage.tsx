import { useState, type SubmitEvent } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { AuthLayout } from '@/components/layout/AuthLayout'
import { Button } from '@/components/ui/Button'
import { ErrorState } from '@/components/ui/ErrorState'
import { Input } from '@/components/ui/Input'
import { useAuth } from '@/hooks/useAuth'
import { passwordError } from '@/lib/validation'

/** Reached from the link in the recovery e-mail, which signs the user in temporarily. */
export default function UpdatePasswordPage() {
  const { updatePassword, recovering } = useAuth()
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [busy, setBusy] = useState(false)
  const [failure, setFailure] = useState<string | null>(null)
  const [done, setDone] = useState(false)

  const passwordProblem = submitted ? passwordError(password) : undefined
  const confirmationProblem = submitted && confirmation !== password ? 'As senhas não são iguais.' : undefined

  async function onSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitted(true)
    setFailure(null)
    if (passwordError(password) || confirmation !== password) return
    setBusy(true)
    const result = await updatePassword(password)
    setBusy(false)
    if (result.ok) setDone(true)
    else setFailure(result.message)
  }

  if (done) {
    return (
      <AuthLayout
        title="Senha atualizada"
        footer={
          <Link to="/" className="text-analytic-text underline">
            Ir para o início
          </Link>
        }
      >
        <p role="status">Sua senha foi alterada.</p>
      </AuthLayout>
    )
  }

  // Someone who is simply signed in has no reason to be here: a password change needs the recovery link.
  if (!recovering) return <Navigate to="/" replace />

  return (
    <AuthLayout title="Nova senha">
      <form onSubmit={(event) => void onSubmit(event)} noValidate className="flex flex-col gap-4">
        <Input
          label="Nova senha"
          type="password"
          autoComplete="new-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          hint="Pelo menos 8 caracteres."
          {...(passwordProblem ? { error: passwordProblem } : {})}
        />
        <Input
          label="Repita a nova senha"
          type="password"
          autoComplete="new-password"
          value={confirmation}
          onChange={(event) => setConfirmation(event.target.value)}
          {...(confirmationProblem ? { error: confirmationProblem } : {})}
        />
        {failure && <ErrorState title="Não foi possível atualizar" message={failure} />}
        <Button type="submit" loading={busy}>
          Salvar senha
        </Button>
      </form>
    </AuthLayout>
  )
}
