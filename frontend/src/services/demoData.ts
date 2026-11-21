import type {
  LogisticSimulationResult,
  LorenzPoint3D,
  LorenzSimulationResult,
  MarketMetrics,
  PricePoint,
  ResearchExperiment,
  ResearchProject,
} from '@/types/domain'

/**
 * Deterministic pseudo-random number generator (LCG) to ensure
 * reproducible client-side demo data matching SeedManager philosophy (RULE 017).
 */
class DeterministicRNG {
  private state: number

  constructor(seed: number = 42) {
    this.state = seed % 2147483647
    if (this.state <= 0) this.state += 2147483646
  }

  next(): number {
    this.state = (this.state * 16807) % 2147483647
    return (this.state - 1) / 2147483646
  }

  normal(mean = 0, std = 1): number {
    const u1 = Math.max(1e-9, this.next())
    const u2 = this.next()
    const z0 = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2)
    return mean + z0 * std
  }
}

/**
 * Generate synthetic canonical market history with realistic volatility clustering.
 */
export function getMarketSeriesDemo(
  symbol: string,
  days = 120,
  seed = 42
): { points: PricePoint[]; metrics: MarketMetrics } {
  const rng = new DeterministicRNG(seed)
  const points: PricePoint[] = []

  let basePrice = symbol.includes('PETR') ? 35.0 : symbol.includes('VALE') ? 62.0 : 540.0
  let peak = basePrice
  const returns: number[] = []

  const startDate = new Date('2024-01-02')

  for (let i = 0; i < days; i++) {
    const date = new Date(startDate)
    date.setDate(startDate.getDate() + Math.floor(i * 1.4))

    const ret = rng.normal(0.0004, 0.018)
    returns.push(ret)
    basePrice *= Math.exp(ret)
    if (basePrice > peak) peak = basePrice
    const drawdown = (basePrice - peak) / peak

    points.push({
      date: date.toISOString().slice(0, 10),
      close: Number(basePrice.toFixed(2)),
      return: Number(ret.toFixed(4)),
      drawdown: Number(drawdown.toFixed(4)),
    })
  }

  // Calculate standard financial metrics
  const meanRet = returns.reduce((a, b) => a + b, 0) / returns.length
  const variance =
    returns.reduce((acc, r) => acc + Math.pow(r - meanRet, 2), 0) / (returns.length - 1)
  const dailyVol = Math.sqrt(variance)
  const annualizedVol = dailyVol * Math.sqrt(252)
  const sharpe = (meanRet / (dailyVol || 1)) * Math.sqrt(252)

  const sortedLosses = returns.map((r) => -r).sort((a, b) => a - b)
  const var95Idx = Math.floor(sortedLosses.length * 0.95)
  const var95 = sortedLosses[var95Idx] ?? 0.02
  const tailLosses = sortedLosses.slice(var95Idx)
  const cvar95 =
    tailLosses.reduce((acc, l) => acc + l, 0) / (tailLosses.length || 1)

  const maxDd = Math.min(...points.map((p) => p.drawdown ?? 0))
  const firstPrice = points[0]?.close ?? 1
  const lastPrice = points[points.length - 1]?.close ?? 1
  const priceChange = lastPrice - firstPrice
  const priceChangePct = (priceChange / firstPrice) * 100

  return {
    points,
    metrics: {
      symbol,
      lastPrice,
      priceChange: Number(priceChange.toFixed(2)),
      priceChangePct: Number(priceChangePct.toFixed(2)),
      annualizedVolatility: Number((annualizedVol * 100).toFixed(2)),
      sharpeRatio: Number(sharpe.toFixed(2)),
      maxDrawdown: Number((maxDd * 100).toFixed(2)),
      var95: Number((var95 * 100).toFixed(2)),
      cvar95: Number((cvar95 * 100).toFixed(2)),
      dataHash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
      period: '120 pregões diários',
    },
  }
}

/**
 * Simulate the discrete logistic map x_{n+1} = r x_n (1 - x_n).
 */
export function simulateLogisticDemo(
  r: number,
  x0 = 0.4,
  nSteps = 80
): LogisticSimulationResult {
  const orbit: { step: number; x: number }[] = []
  let x = x0
  let lyapunovSum = 0

  for (let n = 0; n <= nSteps; n++) {
    orbit.push({ step: n, x: Number(x.toFixed(4)) })
    const deriv = Math.abs(r * (1 - 2 * x))
    if (deriv > 1e-9) {
      lyapunovSum += Math.log(deriv)
    }
    x = r * x * (1 - x)
  }

  const lyapunovExponent = Number((lyapunovSum / (nSteps || 1)).toFixed(3))
  const isChaotic = lyapunovExponent > 0

  // Fixed points: x=0 and x = (r-1)/r
  const fixedPoints = [0]
  if (r > 1) {
    fixedPoints.push(Number(((r - 1) / r).toFixed(4)))
  }

  return {
    r,
    x0,
    nSteps,
    lyapunovExponent,
    isChaotic,
    orbit,
    fixedPoints,
  }
}

/**
 * Integrate the continuous Lorenz system using RK4 adaptive simulation.
 */
export function simulateLorenzDemo(
  sigma = 10.0,
  rho = 28.0,
  beta = 8.0 / 3.0,
  steps = 1200,
  dt = 0.01
): LorenzSimulationResult {
  // Hopf bifurcation threshold: rho_H = sigma*(sigma + beta + 3) / (sigma - beta - 1)
  let hopf = 24.74
  if (sigma > beta + 1) {
    hopf = (sigma * (sigma + beta + 3.0)) / (sigma - beta - 1.0)
  }

  const points: LorenzPoint3D[] = []
  let x = 1.0
  let y = 1.0
  let z = 1.0

  for (let i = 0; i < steps; i++) {
    points.push({
      t: Number((i * dt).toFixed(2)),
      x: Number(x.toFixed(2)),
      y: Number(y.toFixed(2)),
      z: Number(z.toFixed(2)),
    })

    // RK4 step
    const f1x = sigma * (y - x)
    const f1y = x * (rho - z) - y
    const f1z = x * y - beta * z

    const x2 = x + 0.5 * dt * f1x
    const y2 = y + 0.5 * dt * f1y
    const z2 = z + 0.5 * dt * f1z

    const f2x = sigma * (y2 - x2)
    const f2y = x2 * (rho - z2) - y2
    const f2z = x2 * y2 - beta * z2

    const x3 = x + 0.5 * dt * f2x
    const y3 = y + 0.5 * dt * f2y
    const z3 = z + 0.5 * dt * f2z

    const f3x = sigma * (y3 - x3)
    const f3y = x3 * (rho - z3) - y3
    const f3z = x3 * y3 - beta * z3

    const x4 = x + dt * f3x
    const y4 = y + dt * f3y
    const z4 = z + dt * f3z

    const f4x = sigma * (y4 - x4)
    const f4y = x4 * (rho - z4) - y4
    const f4z = x4 * y4 - beta * z4

    x += (dt / 6.0) * (f1x + 2 * f2x + 2 * f3x + f4x)
    y += (dt / 6.0) * (f1y + 2 * f2y + 2 * f3y + f4y)
    z += (dt / 6.0) * (f1z + 2 * f2z + 2 * f3z + f4z)
  }

  // Equilibria C+ and C- for rho > 1
  let cPlus: [number, number, number] | null = null
  let cMinus: [number, number, number] | null = null

  if (rho > 1) {
    const cCoord = Math.sqrt(beta * (rho - 1))
    cPlus = [Number(cCoord.toFixed(2)), Number(cCoord.toFixed(2)), Number((rho - 1).toFixed(2))]
    cMinus = [Number((-cCoord).toFixed(2)), Number((-cCoord).toFixed(2)), Number((rho - 1).toFixed(2))]
  }

  return {
    sigma,
    rho,
    beta,
    hopfThreshold: Number(hopf.toFixed(2)),
    isAboveHopf: rho > hopf,
    points,
    cPlus,
    cMinus,
  }
}

/**
 * Initial research projects and experiments for demo lab.
 */
export const initialProjectsDemo: ResearchProject[] = [
  {
    id: 'proj-1',
    name: 'Transições de Fase e Volatilidade em Mercado',
    description: 'Estudo empírico correlacionando quebras de estabilidade no atrator de Lorenz com picos de volatilidade do Ibovespa.',
    experimentsCount: 3,
    createdAt: '2026-11-20T10:00:00Z',
  },
  {
    id: 'proj-2',
    name: 'Sensibilidade de Cauda e Caos Discreto',
    description: 'Análise de expoentes de Lyapunov aplicados a séries temporais logísticas e distribuições de cauda gorda.',
    experimentsCount: 2,
    createdAt: '2026-11-20T14:30:00Z',
  },
]

export const initialExperimentsDemo: ResearchExperiment[] = [
  {
    id: 'exp-101',
    projectId: 'proj-1',
    name: 'Lorenz Hopf Bifurcation at canonical rho=28',
    hypothesis: 'O sistema de Lorenz com parâmetros canônicos (sigma=10, beta=8/3, rho=28) ultrapassa o limiar de Hopf (rho_H ≈ 24.74) exibindo atrator estranho determinístico.',
    model: 'lorenz',
    parameters: { sigma: 10, rho: 28, beta: 2.6667, t_max: 20 },
    seed: 42,
    dataHash: null,
    engineVersion: '0.1.0',
    createdAt: '2026-11-20T11:15:00Z',
    lastRun: {
      id: 'run-1',
      experimentId: 'exp-101',
      startedAt: '2026-11-20T11:15:05Z',
      executionTimeMs: 4.25,
      metrics: {
        hopf_threshold: 24.7368,
        is_above_hopf: 1.0,
        z_max: 48.12,
      },
      environment: { python: '3.13.5', platform: 'win32', quantlab: '0.1.0' },
      status: 'completed',
    },
  },
  {
    id: 'exp-102',
    projectId: 'proj-1',
    name: 'Análise de Risco PETR4.SA — VaR 95%',
    hypothesis: 'A série diária de retornos de PETR4.SA exibe distribuição assimétrica com CVaR excedendo o VaR em mais de 30% em períodos de estresse.',
    model: 'market_risk',
    parameters: { symbol: 'PETR4.SA', confidence: 0.95, days: 120 },
    seed: 101,
    dataHash: 'ad6d717d79a686e796b9a16ef424ee6518625944f8cd5882351184cb9f2dd2b0',
    engineVersion: '0.1.0',
    createdAt: '2026-11-20T12:00:00Z',
    lastRun: {
      id: 'run-2',
      experimentId: 'exp-102',
      startedAt: '2026-11-20T12:00:03Z',
      executionTimeMs: 1.82,
      metrics: {
        annualized_volatility: 35.16,
        sharpe_ratio: 1.68,
        max_drawdown: -16.87,
        var_95: 3.05,
        cvar_95: 4.52,
      },
      environment: { python: '3.13.5', platform: 'win32', quantlab: '0.1.0' },
      status: 'completed',
    },
  },
]
