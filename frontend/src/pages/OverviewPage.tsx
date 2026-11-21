import { Link } from 'react-router-dom'
import { AsyncBoundary } from '@/components/AsyncBoundary'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { EmptyState } from '@/components/ui/EmptyState'
import { Panel } from '@/components/ui/Panel'
import { useAuth } from '@/hooks/useAuth'
import { useHealth } from '@/hooks/useHealth'
import { ApiError } from '@/services/apiClient'
import { ArrowRight, FlaskConical, LineChart, Waypoints } from 'lucide-react'

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

      {/* Foundation system status and experiments panel */}
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

      {/* Quick Launch Cards to Active Modules */}
      <div className="grid gap-4 md:grid-cols-3">
        <Link
          to="/risco"
          className="group flex flex-col justify-between rounded-md border border-line bg-panel p-4 transition-colors hover:border-analytic/60"
        >
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="p-1.5 rounded bg-analytic/10 text-analytic border border-analytic/20">
                <LineChart className="h-4 w-4" />
              </span>
              <Badge variant="active">Mercados</Badge>
            </div>
            <h3 className="text-xs font-semibold text-fg group-hover:text-analytic transition-colors">
              Mercado & Análise de Risco
            </h3>
            <p className="mt-1 text-[11px] text-fg-muted">
              Séries temporais, volatilidade anualizada, drawdown e VaR/CVaR 95%.
            </p>
          </div>
          <div className="mt-3 flex items-center gap-1 text-[11px] font-medium text-analytic">
            Acessar retornos <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-1" />
          </div>
        </Link>

        <Link
          to="/dinamica/logistico"
          className="group flex flex-col justify-between rounded-md border border-line bg-panel p-4 transition-colors hover:border-dynamic/60"
        >
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="p-1.5 rounded bg-dynamic/10 text-dynamic border border-dynamic/20">
                <Waypoints className="h-4 w-4" />
              </span>
              <Badge variant="active">Dinâmica</Badge>
            </div>
            <h3 className="text-xs font-semibold text-fg group-hover:text-dynamic transition-colors">
              Sistemas Dinâmicos & Caos
            </h3>
            <p className="mt-1 text-[11px] text-fg-muted">
              Mapa logístico 1D e atrator de Lorenz 3D com limiar de Hopf.
            </p>
          </div>
          <div className="mt-3 flex items-center gap-1 text-[11px] font-medium text-dynamic">
            Simular órbitas <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-1" />
          </div>
        </Link>

        <Link
          to="/projetos"
          className="group flex flex-col justify-between rounded-md border border-line bg-panel p-4 transition-colors hover:border-pos/60"
        >
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="p-1.5 rounded bg-pos/10 text-pos border border-pos/20">
                <FlaskConical className="h-4 w-4" />
              </span>
              <Badge variant="active">Pesquisa</Badge>
            </div>
            <h3 className="text-xs font-semibold text-fg group-hover:text-pos transition-colors">
              Laboratório de Pesquisa
            </h3>
            <p className="mt-1 text-[11px] text-fg-muted">
              Governança de hipóteses obrigatórias, semente e reprodução idêntica.
            </p>
          </div>
          <div className="mt-3 flex items-center gap-1 text-[11px] font-medium text-pos">
            Acessar laboratório <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-1" />
          </div>
        </Link>
      </div>
    </div>
  )
}
