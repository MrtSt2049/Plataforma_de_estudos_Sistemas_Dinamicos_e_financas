import { Link } from 'react-router-dom'
import { EmptyState } from '@/components/ui/EmptyState'

export default function NotFoundPage() {
  return (
    <main className="grid min-h-screen place-items-center px-4">
      <EmptyState
        title="Página não encontrada"
        description="O endereço não existe ou a tela ainda não foi construída."
        action={
          <Link to="/" className="text-analytic-text underline">
            Ir para o início
          </Link>
        }
      />
    </main>
  )
}
