import { useState, useMemo } from 'react'
import { Badge } from '@/components/ui/Badge'
import { StatCard } from '@/components/ui/StatCard'
import { Panel } from '@/components/ui/Panel'
import { Table, type TableColumn } from '@/components/ui/Table'
import { ScientificChart, type ChartDataPoint } from '@/components/charts/ScientificChart'
import { getMarketSeriesDemo } from '@/services/demoData'
import type { PricePoint } from '@/types/domain'
import { ShieldCheck, Calendar, Hash, ArrowUpDown } from 'lucide-react'

const SYMBOLS = [
  { symbol: 'PETR4.SA', label: 'Petrobras PN (PETR4.SA)' },
  { symbol: 'VALE3.SA', label: 'Vale ON (VALE3.SA)' },
  { symbol: 'SPY', label: 'SPDR S&P 500 ETF (SPY)' },
]

export default function MarketAnalysisPage() {
  const [selectedSymbol, setSelectedSymbol] = useState('PETR4.SA')
  const [selectedPeriod, setSelectedPeriod] = useState<number>(120)

  const { points, metrics } = useMemo(() => {
    return getMarketSeriesDemo(selectedSymbol, selectedPeriod, 42)
  }, [selectedSymbol, selectedPeriod])

  const priceChartData: ChartDataPoint[] = useMemo(() => {
    return points.map((p) => ({
      x: p.date,
      y: p.close,
      label: p.date,
    }))
  }, [points])

  const drawdownChartData: ChartDataPoint[] = useMemo(() => {
    return points.map((p) => ({
      x: p.date,
      y: Number(((p.drawdown ?? 0) * 100).toFixed(2)),
      label: p.date,
    }))
  }, [points])

  const returnsChartData: ChartDataPoint[] = useMemo(() => {
    return points.slice(1).map((p) => ({
      x: p.date,
      y: Number(((p.return ?? 0) * 100).toFixed(2)),
      label: p.date,
    }))
  }, [points])

  const tableColumns: TableColumn<PricePoint>[] = [
    {
      header: 'Data',
      accessor: (item) => <span className="font-mono text-fg">{item.date}</span>,
    },
    {
      header: 'Fechamento',
      align: 'right',
      accessor: (item) => (
        <span className="font-mono font-medium">
          R$ {item.close.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
        </span>
      ),
    },
    {
      header: 'Retorno Diário',
      align: 'right',
      accessor: (item) => {
        const ret = (item.return ?? 0) * 100
        const isPos = ret >= 0
        return (
          <span
            className={`font-mono font-medium ${
              isPos ? 'text-pos' : 'text-neg-text'
            }`}
          >
            {isPos ? `▲ +${ret.toFixed(2)}%` : `▼ ${ret.toFixed(2)}%`}
          </span>
        )
      },
    },
    {
      header: 'Drawdown Submerso',
      align: 'right',
      accessor: (item) => {
        const dd = (item.drawdown ?? 0) * 100
        return (
          <span className="font-mono text-fg-muted">
            {dd === 0 ? '0.00%' : `${dd.toFixed(2)}%`}
          </span>
        )
      },
    },
  ]

  const recentPoints = useMemo(() => {
    return [...points].reverse().slice(0, 10)
  }, [points])

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-semibold text-fg">Mercado & Análise Quantitativa</h1>
            <Badge variant="active">Motor 0.1</Badge>
          </div>
          <p className="text-xs text-fg-muted mt-1">
            Séries canônicas determinísticas com cálculo de volatilidade agrupada, VaR/CVaR e drawdown máximo.
          </p>
        </div>

        {/* Symbol and Period Controls */}
        <div className="flex items-center gap-2">
          <div className="flex rounded-md border border-line bg-surface p-1">
            {SYMBOLS.map((s) => (
              <button
                key={s.symbol}
                type="button"
                onClick={() => setSelectedSymbol(s.symbol)}
                className={`rounded px-3 py-1 text-xs font-medium transition-colors ${
                  selectedSymbol === s.symbol
                    ? 'bg-panel text-fg shadow-sm'
                    : 'text-fg-muted hover:text-fg'
                }`}
              >
                {s.symbol}
              </button>
            ))}
          </div>

          <div className="flex rounded-md border border-line bg-surface p-1">
            {[60, 120, 252].map((days) => (
              <button
                key={days}
                type="button"
                onClick={() => setSelectedPeriod(days)}
                className={`rounded px-2.5 py-1 font-mono text-xs font-medium transition-colors ${
                  selectedPeriod === days
                    ? 'bg-panel text-fg shadow-sm'
                    : 'text-fg-muted hover:text-fg'
                }`}
              >
                {days}d
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Audit & Hash bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-line bg-panel px-4 py-2 text-xs">
        <div className="flex items-center gap-2 text-fg-muted">
          <Calendar className="h-3.5 w-3.5 text-analytic" />
          <span>Amostragem: <span className="font-mono text-fg">{metrics.period}</span></span>
        </div>
        <div className="flex items-center gap-2 text-fg-muted">
          <Hash className="h-3.5 w-3.5 text-dynamic" />
          <span>Data Hash (RULE 017):</span>
          <code className="font-mono text-[11px] text-fg bg-surface px-1.5 py-0.5 rounded border border-line">
            {metrics.dataHash.slice(0, 16)}...
          </code>
          <ShieldCheck className="h-4 w-4 text-pos" />
        </div>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <StatCard
          label="Último Fechamento"
          value={`R$ ${metrics.lastPrice.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`}
          change={{
            value: `${Math.abs(metrics.priceChangePct)}%`,
            positive: metrics.priceChangePct >= 0,
          }}
          helperText={`Δ R$ ${metrics.priceChange > 0 ? '+' : ''}${metrics.priceChange.toFixed(2)}`}
        />
        <StatCard
          label="Volatilidade Anualizada"
          value={metrics.annualizedVolatility.toFixed(2)}
          unit="%"
          helperText="Janela anualizada (√252)"
        />
        <StatCard
          label="Índice Sharpe"
          value={metrics.sharpeRatio.toFixed(2)}
          badge={
            <Badge variant={metrics.sharpeRatio > 1.0 ? 'active' : 'queued'}>
              {metrics.sharpeRatio > 1.0 ? 'Atrativo' : 'Moderado'}
            </Badge>
          }
          helperText="Excesso retorno / Risco total"
        />
        <StatCard
          label="Drawdown Máximo"
          value={`${metrics.maxDrawdown.toFixed(2)}%`}
          change={{
            value: `${Math.abs(metrics.maxDrawdown).toFixed(2)}%`,
            positive: false,
          }}
          helperText="Queda máxima do pico"
        />
        <StatCard
          label="VaR Histórico 95%"
          value={`${metrics.var95.toFixed(2)}%`}
          helperText={`CVaR 95%: ${metrics.cvar95.toFixed(2)}%`}
          badge={<Badge variant="queued">1 dia</Badge>}
        />
      </div>

      {/* Main Charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        <ScientificChart
          title="Trajetória de Preços"
          subtitle={`Série temporal de preços de fechamento para ${selectedSymbol}`}
          data={priceChartData}
          color="#3B82F6"
          type="area"
          unit="BRL"
          height={260}
        />

        <ScientificChart
          title="Curva Submersa de Drawdown"
          subtitle="Distância percentual em relação ao topo histórico alcançado"
          data={drawdownChartData}
          color="#EA3943"
          type="area"
          unit="%"
          height={260}
          baselineZero
        />
      </div>

      {/* Returns series & Recent data table */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-1">
          <ScientificChart
            title="Retornos Diários (%)"
            subtitle={`Variação log/aritmética com corte VaR 95% (-${metrics.var95}%)`}
            data={returnsChartData}
            color="#8B5CF6"
            type="line"
            unit="%"
            height={260}
          />
        </div>

        <div className="lg:col-span-2">
          <Panel
            title="Amostragem Recente de Pregões"
            aside={
              <span className="flex items-center gap-1 text-xs text-fg-muted font-mono">
                <ArrowUpDown className="h-3 w-3" /> 10 pregões mais recentes
              </span>
            }
          >
            <Table
              columns={tableColumns}
              data={recentPoints}
              keyExtractor={(item) => item.date}
            />
          </Panel>
        </div>
      </div>
    </div>
  )
}
