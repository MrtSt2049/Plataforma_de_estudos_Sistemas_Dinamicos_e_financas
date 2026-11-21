/**
 * Domain types for QuantLab Quantitative Finance and Computational Dynamics.
 * Mirrors the canonical schemas of the Scientific Engine and Research Core.
 */

export interface PricePoint {
  date: string
  close: number
  return?: number
  drawdown?: number
}

export interface MarketMetrics {
  symbol: string
  lastPrice: number
  priceChange: number
  priceChangePct: number
  annualizedVolatility: number
  sharpeRatio: number
  maxDrawdown: number
  var95: number
  cvar95: number
  dataHash: string
  period: string
}

export interface LogisticOrbitPoint {
  step: number
  x: number
}

export interface LogisticSimulationResult {
  r: number
  x0: number
  nSteps: number
  lyapunovExponent: number
  isChaotic: boolean
  orbit: LogisticOrbitPoint[]
  fixedPoints: number[]
}

export interface LorenzPoint3D {
  t: number
  x: number
  y: number
  z: number
}

export interface LorenzSimulationResult {
  sigma: number
  rho: number
  beta: number
  hopfThreshold: number
  isAboveHopf: boolean
  points: LorenzPoint3D[]
  cPlus: [number, number, number] | null
  cMinus: [number, number, number] | null
}

export interface ResearchProject {
  id: string
  name: string
  description: string
  experimentsCount: number
  createdAt: string
}

export interface ResearchExperiment {
  id: string
  projectId: string
  name: string
  hypothesis: string
  model: 'logistic_map' | 'lorenz' | 'market_risk'
  parameters: Record<string, number | string | boolean>
  seed: number
  dataHash: string | null
  engineVersion: string
  createdAt: string
  lastRun?: ExperimentExecutionRun
}

export interface ExperimentExecutionRun {
  id: string
  experimentId: string
  startedAt: string
  executionTimeMs: number
  metrics: Record<string, number>
  environment: Record<string, string>
  status: 'completed' | 'failed'
}
