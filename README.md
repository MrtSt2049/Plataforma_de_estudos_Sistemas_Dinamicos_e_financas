# QuantLab

**Quantitative Finance & Computational Dynamics**

![Status](https://img.shields.io/badge/status-fase%201%20em%20andamento-yellow)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)

Um laboratório para estudar finanças quantitativas e sistemas dinâmicos no mesmo código. A ideia é ter um lugar onde dá para formular uma hipótese, rodar um experimento e repetir o resultado meses depois, com os mesmos dados, parâmetros e sementes aleatórias.

O foco do projeto é o motor matemático. Interface, API e banco de dados vêm depois que os cálculos estiverem corretos e testados.

## Por que juntar as duas áreas

Finanças quantitativas e sistemas dinâmicos usam a mesma base: álgebra linear, estatística, otimização e integração numérica. Um retorno logarítmico e uma órbita do mapa logístico acabam passando pelas mesmas bibliotecas, pelos mesmos testes numéricos e pelo mesmo registro de experimentos. Faz mais sentido manter uma base só.

Uma pergunta que serve de exemplo para o tipo de pesquisa que quero fazer aqui: existe relação entre regimes de volatilidade e mudanças de estabilidade em um modelo dinâmico de mercado? Dá para atacar isso com dados reais, um modelo estatístico e uma simulação, tudo dentro do projeto.

## Estado atual

O motor científico começou a ser construído. O ambiente, a estrutura do pacote e os primeiros algoritmos existem e têm testes rodando.

| O que | Situação |
|---|---|
| Arquitetura e stack | Definidas ([ADR 0001](docs/adr/0001-empacotamento-do-motor-e-ambiente.md)) |
| Regras de desenvolvimento | Escritas (`.agents/rules/`) |
| Design da interface | Primeira versão em `Assets/` |
| Motor científico (Fase 1) | Em andamento: ambiente com `uv`, validação de entradas, retornos, volatilidade e mapa logístico, todos com testes |
| Backend, banco e frontend | Planejados, ainda sem código |

Implementado no motor até agora:

| Módulo | Funções | Documentação matemática |
|---|---|---|
| `quantlab.analysis` | `simple_returns`, `log_returns`, `cumulative_returns`, `historical_volatility`, `annualized_volatility` | [Retornos e volatilidade](docs/math/retornos-e-volatilidade.md) |
| `quantlab.dynamics` | `logistic_map`, `simulate_logistic_map`, `logistic_fixed_points`, `logistic_lyapunov_exponent`, `classify_map_fixed_point`, `detect_period` | [Mapa logístico](docs/math/mapa-logistico.md) |

Vou atualizar esta tabela conforme as fases forem saindo do papel. Nenhum item é marcado como pronto antes de ter código e testes rodando.

## O que a versão 0.1 vai ter

A 0.1 é só o motor científico, em quatro módulos.

**Market Data**
- Download de dados históricos e consulta de ativos
- Limpeza de valores ausentes e duplicados
- Validação de integridade e padronização das séries

**Quantitative Analysis**
- Retornos simples, logarítmicos e acumulados
- Volatilidade histórica e anualizada
- Sharpe Ratio e Maximum Drawdown
- VaR e CVaR históricos
- Correlação e covariância

**Dynamical Systems**
- Mapa logístico e sistema de Lorenz
- Simulação de trajetórias e visualização de órbitas
- Experimentos variando parâmetros
- Análise inicial de estabilidade

**Research Core**
- Registro de experimentos e dos seus parâmetros
- Controle de sementes aleatórias
- Hipóteses documentadas junto dos resultados

Ficam de fora da 0.1: redes neurais, integração com corretoras, microsserviços e qualquer infraestrutura distribuída. Otimização de portfólios, backtesting e econometria entram nas fases seguintes.

## Arquitetura

Quatro peças, cada uma com uma responsabilidade:

- **Scientific Engine** (`engine/quantlab`): biblioteca Python com os algoritmos. Não importa Django, Supabase, nada de HTTP e nada de interface. Roda em script, notebook Jupyter, teste ou dentro do backend.
- **Backend** (Django + Django REST Framework): regras de negócio, validação de requisições, permissões e orquestração do motor. Nenhum cálculo científico mora em view, serializer ou model.
- **Supabase**: autenticação, PostgreSQL e Storage.
- **Frontend** (React + TypeScript): dashboards, gráficos e painel de experimentos. Consome a API do Django.

### Autenticação

O Supabase Auth é o único sistema de identidade. O fluxo:

1. O usuário faz login no frontend pelo Supabase e recebe um JWT.
2. O frontend manda o token no header `Authorization`.
3. O Django valida assinatura, expiração, emissor e claims, seguindo a configuração oficial do Supabase.
4. A requisição segue com a identidade já verificada.

O Django não mantém um segundo cadastro de usuários.

### Segurança dos dados

Dados privados têm dono explícito e ficam protegidos por Row Level Security no PostgreSQL. Um detalhe que pesa na arquitetura: conexões com credencial privilegiada ignoram o RLS. Por isso o Django aplica autorização própria nas operações que usam esse tipo de conexão, e o RLS fica como segunda camada. A chave `service_role` nunca vai para o frontend.

### Onde cada dado fica

| Tipo | Onde |
|---|---|
| Cadastros, experimentos, parâmetros, metadados | PostgreSQL (Supabase) |
| Séries históricas e matrizes grandes | Parquet, consultado com DuckDB |
| CSVs, relatórios, exportações | Supabase Storage |

Séries longas não viram milhares de linhas no Postgres sem uma boa razão.

## Stack

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.12+ |
| Ambiente e dependências | uv |
| Computação numérica | NumPy, SciPy, Pandas |
| Matemática simbólica | SymPy |
| Dados analíticos | Parquet + DuckDB |
| Visualização | Plotly, Matplotlib |
| Backend | Django, Django REST Framework, drf-spectacular |
| Frontend | React + TypeScript |
| Auth, banco e arquivos | Supabase (Auth, PostgreSQL, Storage) |
| Testes | Pytest |
| Qualidade | Ruff, Mypy |
| Tarefas assíncronas (futuro) | Celery + Redis |

A fonte dos dados de mercado para a 0.1 ainda está em aberto. Quando eu escolher, a decisão entra como ADR, com as alternativas e o motivo.

## Estrutura do repositório

Esta é a estrutura prevista. Hoje existem `engine/quantlab/` (com `analysis/` e `dynamics/`), `tests/`, `docs/`, `Assets/` e `.agents/`. Os outros diretórios serão criados quando a fase correspondente começar.

```
quantlab/
├── backend/
│   ├── config/settings/      # base, development, production
│   ├── apps/
│   │   ├── accounts/         # validação do JWT do Supabase, permissões
│   │   ├── market_data/
│   │   ├── quantitative_analysis/
│   │   ├── portfolio/
│   │   ├── strategies/
│   │   ├── dynamical_systems/
│   │   └── research/
│   └── tests/
├── engine/quantlab/          # motor científico, independente do Django
│   ├── data/                 # providers/ e processing/
│   ├── analysis/
│   ├── portfolio/
│   ├── strategies/
│   ├── dynamics/
│   └── research/
├── frontend/src/             # components, pages, services, hooks, contexts, types
├── supabase/                 # migrations/, policies/ (RLS), seed.sql
├── notebooks/
├── examples/
├── tests/
├── docs/                     # inclui docs/adr/
├── data/
├── Assets/                   # design da interface
└── .agents/                  # regras e skills usadas pelo assistente de IA no desenvolvimento
```

## Como documento a matemática

Cada algoritmo relevante vai ter a definição do problema, a notação, as hipóteses, as condições de validade, o método numérico e as limitações. Dois exemplos do nível de detalhe que pretendo manter:

**Retorno logarítmico e volatilidade anualizada**

$$r_t = \ln\left(\frac{P_t}{P_{t-1}}\right), \qquad \sigma_{\text{anual}} = \sigma_{\text{diária}} \sqrt{252}$$

`P_t` é o preço de fechamento no dia `t`. A conversão por $\sqrt{252}$ supõe retornos independentes e identicamente distribuídos, com 252 pregões por ano. Essa suposição falha em períodos de volatilidade agrupada, e o motor vai deixar isso documentado.

**Mapa logístico**

$$x_{t+1} = r \, x_t (1 - x_t), \qquad x_t \in [0,1], \; r \in [0,4]$$

O ponto fixo $x^* = 1 - 1/r$ é estável para $1 < r < 3$, porque a derivada ali vale $2 - r$ e $|2 - r| < 1$. A cascata de duplicação de período começa em $r = 3$ e acumula perto de $r \approx 3{,}57$, onde o comportamento caótico aparece. Esses valores servem de teste: a simulação precisa reproduzi-los.

Uma observação sobre interpretação: simular um modelo caótico de preços mostra o que o modelo faz. Não prova que o mercado real seja determinístico ou caótico.

## Como rodar

Pré-requisito: [uv](https://docs.astral.sh/uv/). Ele instala o Python certo (3.13, fixado em `.python-version`) e as versões exatas do `uv.lock`.

```bash
uv sync                 # cria .venv com o motor e as ferramentas de desenvolvimento
uv run pytest --cov     # testes com cobertura
uv run ruff check .     # lint
uv run ruff format .    # formatação
uv run mypy             # tipagem (modo strict)
```

Exemplo de uso do motor:

```python
import pandas as pd

from quantlab.analysis import annualized_volatility, cumulative_returns, log_returns, simple_returns
from quantlab.dynamics import detect_period, logistic_fixed_points, simulate_logistic_map

prices = pd.Series(
    [100.0, 101.5, 99.8, 102.3, 103.1],
    index=pd.bdate_range("2025-01-06", periods=5),
)
cumulative_returns(simple_returns(prices)).iloc[-1]  # ≈ 0.031 (3,1% no período)
annualized_volatility(log_returns(prices))  # ≈ 0.282

for point in logistic_fixed_points(2.5):
    print(point.location, point.multiplier, point.stability)
# 0.0 2.5 unstable
# 0.6 -0.4999999999999999 stable    (o valor exato é 2 - r = -0.5; a diferença é arredondamento)

orbit = simulate_logistic_map(r=3.5, x0=0.2, n_steps=22_000)[20_000:]
detect_period(orbit)  # 4
```

Os valores nos comentários foram obtidos executando o código acima (os marcados com ≈ estão arredondados). A volatilidade anualizada de 4 retornos é só ilustração: uma amostra tão curta não estima nada com confiança.

O que já vale para qualquer pessoa que clonar o repositório:

- Credenciais ficam em variáveis de ambiente. O `.env.example` vai ter só os nomes e valores fictícios.
- `.env`, tokens, chaves, bancos locais e dados privados não entram no Git.
- Desenvolvimento e produção usam projetos Supabase separados.

## Roadmap

- [ ] **Fase 1, fundação científica:** ambiente com `uv`, estrutura do motor, primeiros algoritmos, testes
- [ ] **Fase 2, análise quantitativa:** provedores de dados, indicadores, risco, correlação, visualizações
- [ ] **Fase 3, sistemas dinâmicos:** sistemas discretos e contínuos, estabilidade, bifurcações, caos
- [ ] **Fase 4, infraestrutura e backend:** projeto Supabase, Auth, validação de JWT no Django, RLS, APIs, Storage
- [ ] **Fase 5, frontend:** React, integração com Auth e API, dashboards e painel de experimentos
- [ ] **Fase 6, pesquisa avançada:** otimização de portfólios, econometria, backtesting, modelos estocásticos, Machine Learning

Não coloquei prazos. O tempo de cada fase depende da profundidade matemática que eu decidir dar a ela.

## Convenções

- **Testes:** todo módulo científico tem testes com casos normais, extremos, entradas inválidas, valores ausentes e não finitos, e comparação com soluções analíticas conhecidas quando elas existem.
- **Código:** type hints, funções pequenas, Ruff e Mypy.
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`).
- **Branches:** `main`, `develop`, `feature/*` e `fix/*`.
- **Versões:** [Semantic Versioning](https://semver.org/lang/pt-BR/) a partir da primeira versão publicada.
- **Decisões de arquitetura:** registradas em `docs/adr/`, cada uma com contexto, alternativas, decisão e consequências.
- **Resultados:** nenhum número entra na documentação sem ter sido executado. Exemplos hipotéticos são marcados como tal.

## Aviso

O QuantLab é um projeto de estudo e pesquisa. Nada aqui é recomendação de investimento, e resultados de backtests ou simulações não garantem desempenho futuro.

## Licença

Distribuído sob a [licença MIT](LICENSE). Você pode usar, copiar, modificar e redistribuir o código, desde que mantenha o aviso de copyright e a licença nas cópias.

## Referências

- [Python](https://docs.python.org/)
- [Django](https://docs.djangoproject.com/) e [Django REST Framework](https://www.django-rest-framework.org/)
- [Supabase](https://supabase.com/docs) e [PostgreSQL](https://www.postgresql.org/docs/)
- [NumPy](https://numpy.org/doc/), [SciPy](https://docs.scipy.org/), [Pandas](https://pandas.pydata.org/docs/), [SymPy](https://www.sympy.org/)
- [DuckDB](https://duckdb.org/docs/)
