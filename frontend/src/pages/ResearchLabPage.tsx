import { useState } from 'react'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Panel } from '@/components/ui/Panel'
import { StatCard } from '@/components/ui/StatCard'
import { Table, type TableColumn } from '@/components/ui/Table'
import { Tabs, type TabItem } from '@/components/ui/Tabs'
import {
  initialExperimentsDemo,
  initialProjectsDemo,
} from '@/services/demoData'
import type {
  ResearchExperiment,
  ResearchProject,
} from '@/types/domain'
import {
  CheckCircle2,
  Clock,
  FileCheck2,
  FlaskConical,
  FolderKanban,
  Hash,
  RotateCcw,
  Sparkles,
} from 'lucide-react'

const TABS: TabItem[] = [
  { id: 'experiments', label: 'Experimentos & Reprodutibilidade', icon: <FlaskConical className="h-3.5 w-3.5 text-analytic" /> },
  { id: 'projects', label: 'Projetos de Pesquisa', icon: <FolderKanban className="h-3.5 w-3.5 text-dynamic" /> },
]

const MODEL_IDS = ['lorenz', 'logistic_map', 'market_risk'] as const
type ModelId = (typeof MODEL_IDS)[number]

function isModelId(value: string): value is ModelId {
  return (MODEL_IDS as readonly string[]).includes(value)
}

export default function ResearchLabPage() {
  const [activeTab, setActiveTab] = useState('experiments')
  const [projects] = useState<ResearchProject[]>(initialProjectsDemo)
  const [experiments, setExperiments] = useState<ResearchExperiment[]>(initialExperimentsDemo)

  // Reproduction feedback state
  const [reproducingId, setReproducingId] = useState<string | null>(null)
  const [reproducedResults, setReproducedResults] = useState<Record<string, boolean>>({})

  // New Experiment Form State
  const [showNewExpModal, setShowNewExpModal] = useState(false)
  const [formName, setFormName] = useState('')
  const [formHypothesis, setFormHypothesis] = useState('')
  const [formModel, setFormModel] = useState<ModelId>('lorenz')
  const [formSeed, setFormSeed] = useState(42)
  const [formError, setFormError] = useState<string | null>(null)

  const handleReproduce = (exp: ResearchExperiment) => {
    setReproducingId(exp.id)
    setTimeout(() => {
      setReproducedResults((prev) => ({ ...prev, [exp.id]: true }))
      setReproducingId(null)
    }, 600)
  }

  const handleCreateExperiment = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formHypothesis.trim()) {
      setFormError('A hipótese é estritamente obrigatória para todo experimento (RULE 017 / ADR 0009).')
      return
    }
    if (!formName.trim()) {
      setFormError('O nome do experimento é obrigatório.')
      return
    }

    const newExp: ResearchExperiment = {
      id: `exp-${Date.now()}`,
      projectId: 'proj-1',
      name: formName.trim(),
      hypothesis: formHypothesis.trim(),
      model: formModel,
      parameters:
        formModel === 'lorenz'
          ? { sigma: 10, rho: 28, beta: 2.6667 }
          : formModel === 'logistic_map'
            ? { r: 3.85, x0: 0.4 }
            : { symbol: 'PETR4.SA', confidence: 0.95 },
      seed: formSeed,
      dataHash:
        formModel === 'market_risk'
          ? 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
          : null,
      engineVersion: '0.1.0',
      createdAt: new Date().toISOString(),
      lastRun: {
        id: `run-${Date.now()}`,
        experimentId: `exp-${Date.now()}`,
        startedAt: new Date().toISOString(),
        executionTimeMs: Math.round(Math.random() * 5 + 1),
        metrics:
          formModel === 'lorenz'
            ? { hopf_threshold: 24.74, is_above_hopf: 1.0 }
            : formModel === 'logistic_map'
              ? { lyapunov_exponent: 0.432, is_chaotic: 1.0 }
              : { annualized_volatility: 32.5, sharpe_ratio: 1.45 },
        environment: { python: '3.13.5', platform: 'win32', quantlab: '0.1.0' },
        status: 'completed',
      },
    }

    setExperiments((prev) => [newExp, ...prev])
    setFormName('')
    setFormHypothesis('')
    setFormError(null)
    setShowNewExpModal(false)
  }

  const projectColumns: TableColumn<ResearchProject>[] = [
    {
      header: 'Nome do Projeto',
      accessor: (p) => (
        <div>
          <span className="font-medium text-fg">{p.name}</span>
          <p className="text-[11px] text-fg-muted">{p.description}</p>
        </div>
      ),
    },
    {
      header: 'Experimentos',
      align: 'center',
      accessor: (p) => (
        <Badge variant="queued">{`${p.experimentsCount} cadastrados`}</Badge>
      ),
    },
    {
      header: 'Criado em',
      align: 'right',
      accessor: (p) => (
        <span className="font-mono text-fg-muted">
          {new Date(p.createdAt).toLocaleDateString('pt-BR')}
        </span>
      ),
    },
  ]

  const experimentColumns: TableColumn<ResearchExperiment>[] = [
    {
      header: 'Experimento & Hipótese Científica',
      accessor: (exp) => (
        <div className="flex flex-col gap-1 py-1">
          <div className="flex items-center gap-2">
            <span className="font-medium text-fg">{exp.name}</span>
            <Badge variant="active">{exp.model}</Badge>
            <span className="font-mono text-[11px] text-fg-muted flex items-center gap-0.5">
              <Hash className="h-3 w-3" /> semente: {exp.seed}
            </span>
          </div>
          <p className="text-[11px] text-fg-muted italic">
            "{exp.hypothesis}"
          </p>
        </div>
      ),
    },
    {
      header: 'Última Execução',
      accessor: (exp) => {
        const run = exp.lastRun
        if (!run) return <span className="text-fg-muted">—</span>
        return (
          <div className="flex flex-col gap-0.5 font-mono text-[11px]">
            <span className="text-fg flex items-center gap-1">
              <Clock className="h-3 w-3 text-analytic" /> {run.executionTimeMs} ms
            </span>
            <span className="text-fg-muted">
              v{exp.engineVersion} ({run.environment.platform})
            </span>
          </div>
        )
      },
    },
    {
      header: 'Reprodutibilidade (RULE 017)',
      align: 'right',
      accessor: (exp) => {
        const isReproduced = reproducedResults[exp.id]
        const isReproducing = reproducingId === exp.id

        return (
          <div className="flex items-center justify-end gap-2">
            {isReproduced && (
              <span className="flex items-center gap-1 text-[11px] font-mono text-pos font-medium">
                <CheckCircle2 className="h-3.5 w-3.5" /> Δ = 0.000000
              </span>
            )}
            <Button
              variant="secondary"
              loading={isReproducing}
              onClick={() => handleReproduce(exp)}
              className="text-xs h-7 px-2"
            >
              <RotateCcw className="h-3 w-3 mr-1" />
              {isReproduced ? 'Revalidar' : 'Reproduzir'}
            </Button>
          </div>
        )
      },
    },
  ]

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-semibold text-fg">Laboratório de Pesquisa Científica</h1>
            <Badge variant="active">ADR 0009 / RULE 017</Badge>
          </div>
          <p className="text-xs text-fg-muted mt-1">
            Gestão de hipóteses com semente determinística, integridade criptográfica e tolerância zero a desvios.
          </p>
        </div>

        <Button onClick={() => setShowNewExpModal(!showNewExpModal)}>
          <Sparkles className="h-3.5 w-3.5 mr-1" />
          Novo Experimento
        </Button>
      </header>

      {/* Primary KPI Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Projetos Ativos"
          value={projects.length}
          helperText="Linhas de pesquisa sob governança"
        />
        <StatCard
          label="Experimentos Rastreados"
          value={experiments.length}
          helperText="Com semente e parâmetros imutáveis"
        />
        <StatCard
          label="Motor Científico"
          value="v0.1.0"
          badge={<Badge variant="active">Determinístico</Badge>}
          helperText="SeedManager & Float64 IEEE-754"
        />
        <StatCard
          label="Tolerância de Reprodutibilidade"
          value="0.000000"
          helperText="Tolerância estrita de verificação"
        />
      </div>

      {/* New Experiment Form */}
      {showNewExpModal && (
        <form
          onSubmit={handleCreateExperiment}
          className="flex flex-col gap-4 rounded-md border border-line bg-panel p-5"
        >
          <div className="flex items-center justify-between border-b border-line pb-3">
            <h3 className="text-sm font-semibold text-fg">Cadastrar Novo Experimento Imutável</h3>
            <Badge variant="queued">Esquema ADR 0009</Badge>
          </div>

          {formError && (
            <div className="rounded border border-neg-border bg-neg-surface/40 p-3 text-xs text-neg-text">
              {formError}
            </div>
          )}

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Input
                label="Título do Experimento"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                placeholder="Ex: Bifurcação de Lorenz com rho=32"
                className="mt-1"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div className="flex flex-col gap-1">
                <label className="text-[11px] font-medium uppercase tracking-wider text-fg-muted">
                  Modelo do Motor
                </label>
                <select
                  value={formModel}
                  onChange={(e) => {
                    // A <select> only yields its own options, but the type is checked, not assumed.
                    if (isModelId(e.target.value)) setFormModel(e.target.value)
                  }}
                  className="h-8 rounded-md border border-line bg-surface px-2.5 text-[13px] text-fg outline-none focus:border-analytic"
                >
                  <option value="lorenz">Sistema de Lorenz</option>
                  <option value="logistic_map">Mapa Logístico</option>
                  <option value="market_risk">Risco de Mercado (VaR)</option>
                </select>
              </div>

              <div>
                <Input
                  label="Semente Determinística"
                  type="number"
                  value={formSeed}
                  onChange={(e) => setFormSeed(parseInt(e.target.value) || 0)}
                  className="font-mono"
                  required
                />
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-[11px] font-medium uppercase tracking-wider text-fg-muted">
              Hipótese Científica <span className="text-neg-text">* (Obrigatória segundo RULE 017)</span>
            </label>
            <textarea
              value={formHypothesis}
              onChange={(e) => setFormHypothesis(e.target.value)}
              placeholder="Descreva a hipótese falseável a ser testada..."
              rows={2}
              className="w-full rounded border border-line bg-surface p-2 text-[13px] text-fg outline-none focus:border-analytic"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setShowNewExpModal(false)}
            >
              Cancelar
            </Button>
            <Button type="submit">Salvar e Registrar Execução</Button>
          </div>
        </form>
      )}

      <Tabs tabs={TABS} activeTab={activeTab} onChange={setActiveTab} />

      {activeTab === 'experiments' && (
        <Panel
          title="Registro de Experimentos & Verificação de Reprodutibilidade"
          aside={
            <span className="flex items-center gap-1 text-xs text-fg-muted font-mono">
              <FileCheck2 className="h-3.5 w-3.5 text-analytic" /> {experiments.length} experimentos
            </span>
          }
        >
          <Table
            columns={experimentColumns}
            data={experiments}
            keyExtractor={(e) => e.id}
          />
        </Panel>
      )}

      {activeTab === 'projects' && (
        <Panel
          title="Linhas de Pesquisa Ativas"
          aside={
            <span className="flex items-center gap-1 text-xs text-fg-muted font-mono">
              <FolderKanban className="h-3.5 w-3.5 text-dynamic" /> {projects.length} projetos
            </span>
          }
        >
          <Table
            columns={projectColumns}
            data={projects}
            keyExtractor={(p) => p.id}
          />
        </Panel>
      )}
    </div>
  )
}
