import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { renderWithAuth, fakeSession } from '@/test/renderWithAuth'
import MarketAnalysisPage from './MarketAnalysisPage'
import DynamicalSystemsPage from './DynamicalSystemsPage'
import ResearchLabPage from './ResearchLabPage'
import OverviewPage from './OverviewPage'

describe('MarketAnalysisPage', () => {
  it('renders default metrics and charts for PETR4.SA', () => {
    renderWithAuth(<MarketAnalysisPage />)

    expect(screen.getByText('Mercado & Análise Quantitativa')).toBeInTheDocument()
    expect(screen.getByText('Último Fechamento')).toBeInTheDocument()
    expect(screen.getByText('Volatilidade Anualizada')).toBeInTheDocument()
    expect(screen.getByText('Índice Sharpe')).toBeInTheDocument()
    expect(screen.getByText('Drawdown Máximo')).toBeInTheDocument()
    expect(screen.getByText('VaR Histórico 95%')).toBeInTheDocument()
    expect(screen.getByText('Trajetória de Preços')).toBeInTheDocument()
    expect(screen.getByText('Curva Submersa de Drawdown')).toBeInTheDocument()
  })

  it('allows switching symbol to VALE3.SA or SPY', async () => {
    renderWithAuth(<MarketAnalysisPage />)

    const valeBtn = screen.getByRole('button', { name: 'VALE3.SA' })
    await userEvent.click(valeBtn)

    expect(screen.getByText(/Série temporal de preços de fechamento para VALE3.SA/)).toBeInTheDocument()
  })
})

describe('DynamicalSystemsPage', () => {
  it('renders logistic map tab by default with Lyapunov exponent and orbit chart', () => {
    renderWithAuth(<DynamicalSystemsPage />)

    expect(screen.getByText('Sistemas Dinâmicos & Teoria do Caos')).toBeInTheDocument()
    expect(screen.getByText('Expoente de Lyapunov (λ)')).toBeInTheDocument()
    expect(screen.getByText('Órbita Discreta do Mapa Logístico')).toBeInTheDocument()
  })

  it('updates parameter when clicking preset r=2.8 (Estável)', async () => {
    renderWithAuth(<DynamicalSystemsPage />)

    const presetBtn = screen.getByRole('button', { name: 'r=2.8 (Estável)' })
    await userEvent.click(presetBtn)

    expect(screen.getByText(/Regular \(λ ≤ 0\)/)).toBeInTheDocument()
  })

  it('allows switching to Lorenz system tab and displays Hopf threshold', async () => {
    renderWithAuth(<DynamicalSystemsPage />)

    const lorenzTab = screen.getByRole('button', { name: /Atrator de Lorenz/i })
    await userEvent.click(lorenzTab)

    expect(screen.getByText('Limiar de Hopf (ρ_H)')).toBeInTheDocument()
    expect(screen.getByText('Ponto de Equilíbrio C⁺')).toBeInTheDocument()
    expect(screen.getByText('Ponto de Equilíbrio C⁻')).toBeInTheDocument()
    expect(screen.getByText('Runge-Kutta 4ª Ordem')).toBeInTheDocument()
  })
})

describe('ResearchLabPage', () => {
  it('displays tracked experiments and their mandatory hypotheses', () => {
    renderWithAuth(<ResearchLabPage />)

    expect(screen.getByText('Laboratório de Pesquisa Científica')).toBeInTheDocument()
    expect(screen.getByText(/Lorenz Hopf Bifurcation at canonical rho=28/)).toBeInTheDocument()
    expect(screen.getByText(/Análise de Risco PETR4.SA — VaR 95%/)).toBeInTheDocument()
  })

  it('triggers deterministic reproduction verification with tolerance zero', async () => {
    renderWithAuth(<ResearchLabPage />)

    const reproduceBtns = screen.getAllByRole('button', { name: /Reproduzir/i })
    await userEvent.click(reproduceBtns[0]!)

    await waitFor(
      () => {
        expect(screen.getByText('Δ = 0.000000')).toBeInTheDocument()
      },
      { timeout: 1500 }
    )
  })

  it('requires hypothesis when creating a new experiment', async () => {
    renderWithAuth(<ResearchLabPage />)

    const newExpBtn = screen.getByRole('button', { name: /Novo Experimento/i })
    await userEvent.click(newExpBtn)

    expect(screen.getByText('Cadastrar Novo Experimento Imutável')).toBeInTheDocument()

    // Filling title but leaving hypothesis empty
    const titleInput = screen.getByLabelText(/Título do Experimento/)
    await userEvent.type(titleInput, 'Teste de Hipótese Vazia')

    const submitBtn = screen.getByRole('button', { name: /Salvar e Registrar Execução/i })
    await userEvent.click(submitBtn)

    // Form prevents empty hypothesis
    expect(screen.getByText(/A hipótese é estritamente obrigatória/i)).toBeInTheDocument()
  })
})

describe('OverviewPage', () => {
  it('renders system status and quick links', () => {
    const session = fakeSession('pesquisador@quantlab.ai')
    renderWithAuth(<OverviewPage />, { auth: { session, user: session.user } })

    expect(screen.getByText('Visão geral')).toBeInTheDocument()
    expect(screen.getByText('pesquisador@quantlab.ai')).toBeInTheDocument()
    expect(screen.getByText('Estado do sistema')).toBeInTheDocument()
    expect(screen.getByText('Experimentos recentes')).toBeInTheDocument()
  })
})
