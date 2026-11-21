import { useState, useMemo } from 'react'
import { Badge } from '@/components/ui/Badge'
import { StatCard } from '@/components/ui/StatCard'
import { Panel } from '@/components/ui/Panel'
import { Tabs, type TabItem } from '@/components/ui/Tabs'
import { ScientificChart, type ChartDataPoint } from '@/components/charts/ScientificChart'
import { simulateLogisticDemo, simulateLorenzDemo } from '@/services/demoData'
import { Activity, Flame, ShieldCheck, Orbit } from 'lucide-react'

const TABS: TabItem[] = [
  { id: 'logistic', label: 'Mapa Logístico (1D)', icon: <Orbit className="h-3.5 w-3.5 text-analytic" /> },
  { id: 'lorenz', label: 'Atrator de Lorenz (3D)', icon: <Activity className="h-3.5 w-3.5 text-dynamic" /> },
]

export default function DynamicalSystemsPage() {
  const [activeTab, setActiveTab] = useState('logistic')

  // Logistic Map state
  const [logisticR, setLogisticR] = useState(3.85)
  const [logisticX0, setLogisticX0] = useState(0.4)
  const [logisticSteps, setLogisticSteps] = useState(100)

  // Lorenz state
  const [lorenzSigma, setLorenzSigma] = useState(10.0)
  const [lorenzRho, setLorenzRho] = useState(28.0)
  const [lorenzBeta, setLorenzBeta] = useState(2.6667)

  // Logistic calculation
  const logisticResult = useMemo(() => {
    return simulateLogisticDemo(logisticR, logisticX0, logisticSteps)
  }, [logisticR, logisticX0, logisticSteps])

  const logisticChartData: ChartDataPoint[] = useMemo(() => {
    return logisticResult.orbit.map((pt) => ({
      x: pt.step,
      y: pt.x,
      label: `Passo ${pt.step}`,
    }))
  }, [logisticResult])

  // Lorenz calculation
  const lorenzResult = useMemo(() => {
    return simulateLorenzDemo(lorenzSigma, lorenzRho, lorenzBeta, 1200, 0.01)
  }, [lorenzSigma, lorenzRho, lorenzBeta])

  // 2D projection of Lorenz attractor: x(t) vs z(t) butterfly projection
  const lorenzProjectionData: ChartDataPoint[] = useMemo(() => {
    return lorenzResult.points.filter((_, idx) => idx % 4 === 0).map((pt) => ({
      x: pt.t,
      y: pt.z,
      label: `t=${pt.t}s (x=${pt.x})`,
    }))
  }, [lorenzResult])

  const lorenzXSeriesData: ChartDataPoint[] = useMemo(() => {
    return lorenzResult.points.filter((_, idx) => idx % 4 === 0).map((pt) => ({
      x: pt.t,
      y: pt.x,
      label: `t=${pt.t}s`,
    }))
  }, [lorenzResult])

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-2">
        <div className="flex items-center gap-2">
          <h1 className="text-xl font-semibold text-fg">Sistemas Dinâmicos & Teoria do Caos</h1>
          <Badge variant="active">Motor 0.1</Badge>
        </div>
        <p className="text-xs text-fg-muted">
          Modelos contínuos e discretos não lineares com cálculo exato de bifurcações, expoente de Lyapunov e pontos fixos.
        </p>
      </header>

      <Tabs tabs={TABS} activeTab={activeTab} onChange={setActiveTab} />

      {activeTab === 'logistic' && (
        <div className="flex flex-col gap-6">
          {/* Controls Bar */}
          <div className="grid gap-4 rounded-md border border-line bg-panel p-4 md:grid-cols-4 items-center">
            <div className="flex flex-col gap-1">
              <label className="text-xs text-fg-muted">Parâmetro de Crescimento (r)</label>
              <div className="flex items-center gap-2">
                <input
                  type="range"
                  min="0"
                  max="4"
                  step="0.01"
                  value={logisticR}
                  onChange={(e) => setLogisticR(parseFloat(e.target.value))}
                  className="w-full accent-analytic"
                />
                <span className="font-mono text-xs tabular-nums text-fg w-12 text-right">
                  {logisticR.toFixed(2)}
                </span>
              </div>
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-xs text-fg-muted">Condição Inicial (x₀)</label>
              <div className="flex items-center gap-2">
                <input
                  type="range"
                  min="0.01"
                  max="0.99"
                  step="0.01"
                  value={logisticX0}
                  onChange={(e) => setLogisticX0(parseFloat(e.target.value))}
                  className="w-full accent-analytic"
                />
                <span className="font-mono text-xs tabular-nums text-fg w-12 text-right">
                  {logisticX0.toFixed(2)}
                </span>
              </div>
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-xs text-fg-muted">Número de Iterações (N)</label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min="20"
                  max="200"
                  value={logisticSteps}
                  onChange={(e) => setLogisticSteps(Math.max(20, parseInt(e.target.value) || 50))}
                  className="w-full rounded border border-line bg-surface px-2 py-1 font-mono text-xs text-fg"
                />
              </div>
            </div>

            {/* Presets */}
            <div className="flex flex-wrap gap-1 md:justify-end">
              <button
                type="button"
                onClick={() => setLogisticR(2.8)}
                className="rounded border border-line bg-surface px-2 py-1 text-[11px] text-fg-muted hover:text-fg"
              >
                r=2.8 (Estável)
              </button>
              <button
                type="button"
                onClick={() => setLogisticR(3.2)}
                className="rounded border border-line bg-surface px-2 py-1 text-[11px] text-fg-muted hover:text-fg"
              >
                r=3.2 (Bif. 2)
              </button>
              <button
                type="button"
                onClick={() => setLogisticR(3.85)}
                className="rounded border border-line bg-surface px-2 py-1 text-[11px] text-fg-muted hover:text-fg"
              >
                r=3.85 (Caos)
              </button>
            </div>
          </div>

          {/* Metric Cards */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="Expoente de Lyapunov (λ)"
              value={logisticResult.lyapunovExponent.toFixed(3)}
              badge={
                <Badge variant={logisticResult.isChaotic ? 'warning' : 'active'}>
                  {logisticResult.isChaotic ? (
                    <span className="flex items-center gap-1"><Flame className="h-3 w-3" /> Caos (λ &gt; 0)</span>
                  ) : (
                    <span className="flex items-center gap-1"><ShieldCheck className="h-3 w-3" /> Regular (λ ≤ 0)</span>
                  )}
                </Badge>
              }
              helperText="Taxa assintótica de divergência orbital"
            />
            <StatCard
              label="Ponto Fixo Não Nulo (x*)"
              value={logisticResult.fixedPoints[1]?.toFixed(4) ?? '0.0000'}
              helperText="Solução algébrica x* = (r - 1) / r"
            />
            <StatCard
              label="Equação do Sistema"
              value="xₙ₊₁ = r · xₙ(1 - xₙ)"
              helperText="Mapeamento quadrático unitário [0, 1]"
            />
            <StatCard
              label="Iterações Computadas"
              value={logisticSteps}
              unit="passos"
              helperText="Determinismo de precisão IEEE-754"
            />
          </div>

          {/* Trajectory chart */}
          <ScientificChart
            title="Órbita Discreta do Mapa Logístico"
            subtitle={`Evolução de xₙ ao longo de ${logisticSteps} iterações para r=${logisticR} e x₀=${logisticX0}`}
            data={logisticChartData}
            color={logisticResult.isChaotic ? '#F5A623' : '#3B82F6'}
            type="line"
            unit="x"
            height={300}
          />
        </div>
      )}

      {activeTab === 'lorenz' && (
        <div className="flex flex-col gap-6">
          {/* Controls Bar */}
          <div className="grid gap-4 rounded-md border border-line bg-panel p-4 md:grid-cols-3 items-center">
            <div className="flex flex-col gap-1">
              <label className="text-xs text-fg-muted">Número de Prandtl (σ)</label>
              <div className="flex items-center gap-2">
                <input
                  type="range"
                  min="1"
                  max="20"
                  step="0.5"
                  value={lorenzSigma}
                  onChange={(e) => setLorenzSigma(parseFloat(e.target.value))}
                  className="w-full accent-dynamic"
                />
                <span className="font-mono text-xs tabular-nums text-fg w-10 text-right">
                  {lorenzSigma.toFixed(1)}
                </span>
              </div>
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-xs text-fg-muted">Número de Rayleigh (ρ)</label>
              <div className="flex items-center gap-2">
                <input
                  type="range"
                  min="0.5"
                  max="50"
                  step="0.5"
                  value={lorenzRho}
                  onChange={(e) => setLorenzRho(parseFloat(e.target.value))}
                  className="w-full accent-dynamic"
                />
                <span className="font-mono text-xs tabular-nums text-fg w-10 text-right">
                  {lorenzRho.toFixed(1)}
                </span>
              </div>
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-xs text-fg-muted">Razão de Aspecto Geométrico (β)</label>
              <div className="flex items-center gap-2">
                <input
                  type="range"
                  min="0.5"
                  max="5"
                  step="0.1"
                  value={lorenzBeta}
                  onChange={(e) => setLorenzBeta(parseFloat(e.target.value))}
                  className="w-full accent-dynamic"
                />
                <span className="font-mono text-xs tabular-nums text-fg w-10 text-right">
                  {lorenzBeta.toFixed(2)}
                </span>
              </div>
            </div>
          </div>

          {/* Metric Cards */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="Limiar de Hopf (ρ_H)"
              value={lorenzResult.hopfThreshold.toFixed(2)}
              badge={
                <Badge variant={lorenzResult.isAboveHopf ? 'warning' : 'active'}>
                  {lorenzResult.isAboveHopf ? 'Caótico (ρ > ρ_H)' : 'Subcrítico'}
                </Badge>
              }
              helperText="Bifurcação de Hopf subcrítica"
            />
            <StatCard
              label="Ponto de Equilíbrio C⁺"
              value={
                lorenzResult.cPlus
                  ? `(${lorenzResult.cPlus[0]}, ${lorenzResult.cPlus[1]}, ${lorenzResult.cPlus[2]})`
                  : 'Nenhum'
              }
              helperText="C⁺ = (√(β(ρ-1)), √(β(ρ-1)), ρ-1)"
            />
            <StatCard
              label="Ponto de Equilíbrio C⁻"
              value={
                lorenzResult.cMinus
                  ? `(${lorenzResult.cMinus[0]}, ${lorenzResult.cMinus[1]}, ${lorenzResult.cMinus[2]})`
                  : 'Nenhum'
              }
              helperText="C⁻ = (-√(β(ρ-1)), -√(β(ρ-1)), ρ-1)"
            />
            <StatCard
              label="Integrador Numérico"
              value="Runge-Kutta 4ª Ordem"
              helperText="Passo dt = 0.01, 1200 iterações"
            />
          </div>

          {/* Charts */}
          <div className="grid gap-6 lg:grid-cols-2">
            <ScientificChart
              title="Trajetória da Variável Convectiva z(t)"
              subtitle="Evolução temporal do gradiente térmico vertical"
              data={lorenzProjectionData}
              color="#8B5CF6"
              type="line"
              unit="z"
              height={280}
            />

            <ScientificChart
              title="Série Temporal da Variável x(t)"
              subtitle="Taxa de convecção do fluido ao longo do tempo"
              data={lorenzXSeriesData}
              color="#3B82F6"
              type="line"
              unit="x"
              height={280}
            />
          </div>

          <Panel title="Estrutura Algébrica do Sistema">
            <div className="grid gap-4 text-xs text-fg-muted sm:grid-cols-3 font-mono">
              <div className="rounded border border-line bg-surface p-3">
                <p className="text-fg font-semibold">ẋ = σ(y - x)</p>
                <p className="mt-1 text-[11px] text-fg-muted">Condução térmica e viscosidade</p>
              </div>
              <div className="rounded border border-line bg-surface p-3">
                <p className="text-fg font-semibold">ẏ = x(ρ - z) - y</p>
                <p className="mt-1 text-[11px] text-fg-muted">Diferença de temperatura horizontal</p>
              </div>
              <div className="rounded border border-line bg-surface p-3">
                <p className="text-fg font-semibold">ż = xy - βz</p>
                <p className="mt-1 text-[11px] text-fg-muted">Distorção do perfil de temperatura</p>
              </div>
            </div>
          </Panel>
        </div>
      )}
    </div>
  )
}
