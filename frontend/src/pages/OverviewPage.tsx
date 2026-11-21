import { AsyncBoundary } from '@/components/AsyncBoundary'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { EmptyState } from '@/components/ui/EmptyState'
import { Panel } from '@/components/ui/Panel'
import { useAuth } from '@/hooks/useAuth'
import { useHealth } from '@/hooks/useHealth'
import { ApiError } from '@/services/apiClient'

function apiNotConfigured(error: unknown) {
  if (error instanceof ApiError && error.code === 'api_not_configured') {
    return (
      <EmptyState
        title="API não configurada"
        description="Defina VITE_API_BASE_URL no .env da raiz e reinicie o servidor de desenvolvimento para conectar o backend."
      />
    )
  }
  return null
}

/** Only real numbers appear here: nothing synthetic (the design's DEMO rule). */
export default function OverviewPage() {
  const { user } = useAuth()
  const health = useHealth()

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-xl font-semibold">Visão geral</h1>
        <p className="text-fg-muted">
          Conectado como <span className="text-fg">{user?.email}</span>
        </p>
      </header>

      <div className="grid gap-4 xl:grid-cols-2">
        <Panel title="Estado do sistema">
          <AsyncBoundary
            query={health}
            empty={null}
            errorOverride={apiNotConfigured}
          >
            {(data) => (
              <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-1">
                <dt className="text-fg-muted">API</dt>
                <dd className="num">{data.status}</dd>
                <dt className="text-fg-muted">Versão</dt>
                <dd className="num">{data.version}</dd>
              </dl>
            )}
          </AsyncBoundary>
        </Panel>

        <Panel title="Experimentos recentes" aside={<Badge variant="queued">em breve</Badge>}>
          <EmptyState
            title="Nenhum experimento ainda"
            description="Experimentos registram a hipótese, os parâmetros e a semente, para você poder reproduzir uma execução."
            action={<Button disabled>Novo experimento</Button>}
          />
        </Panel>
      </div>
    </div>
  )
}
