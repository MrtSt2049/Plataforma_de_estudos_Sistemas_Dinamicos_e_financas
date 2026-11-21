# ADR 0008 — Workflows com Inteligência Artificial e Agentes Autônomos

- **Status:** aceita.
- **Data:** 2026-11-21

## Contexto

O **QuantLab** atingiu a versão 0.1 com seu motor científico concluído e testado (`quantlab.data`, `quantlab.analysis`, `quantlab.dynamics`, `quantlab.visualization` e `quantlab.research`). A pesquisa quantitativa e o estudo de sistemas dinâmicos envolvem ciclos iterativos de formulação de hipóteses, coleta e limpeza de dados, calibração paramétrica, cálculo de métricas de risco, simulação de atratores e análise crítica dos resultados.

A introdução de **Workflows com Inteligência Artificial** visa automatizar e acelerar essas sequências de tarefas, interpretando contextos complexos e tomando decisões com pouca intervenção manual, mantendo a reprodutibilidade científica e o isolamento de camadas exigidos pelo projeto (RULE 001, RULE 002 e RULE 017).

## Problema

1. **Isolamento e Pureza do Motor (RULE 002):** Como introduzir fluxos inteligentes e agentes com LLMs sem contaminar o motor científico (`engine/quantlab`), que deve permanecer uma biblioteca matemática pura, sem dependências de rede, frameworks web ou APIs de IA?
2. **Reprodutibilidade Científica (RULE 017 e RULE 018):** Como garantir que decisões e conclusões geradas por modelos de IA (que possuem estocasticidade inerente) resultem em experimentos matematicamente auditáveis, com sementes determinísticas (`SeedManager`), impressão digital dos dados (`hash_data`) e métricas verificáveis?
3. **Estrutura do Workflow:** Como organizar o ciclo de vida de um fluxo de trabalho inteligente de forma padronizada, modular e extensível para suportar tanto agentes autônomos locais quanto orquestradores externos (como n8n)?

## Alternativas consideradas

| Decisão | Alternativa descartada | Motivo |
|---|---|---|
| Pacote dedicado `workflows/quantlab_workflows` fora do motor | Integrar chamadas de LLM dentro de `engine/quantlab` | Violação direta da RULE 001 e RULE 002. O motor deve rodar offline e ser determinístico. |
| Arquitetura em 5 elementos (Gatilho, Contexto, Decisão, Ação, Registro) | Scripts procedurais com prompts ad-hoc | Falta de auditabilidade, acoplamento desordenado e impossibilidade de reprodução. |
| Protocolo desacoplado de LLM com suporte a Mock, OpenAI, Anthropic, Gemini e Ollama | Acoplar a um único SDK proprietário de nuvem | Inviabiliza execução offline em testes, testes de regressão sem custo e modelos locais auto-hospedados. |
| Registro via `quantlab.research.Experiment` e `ExperimentRun` | Guardar apenas logs de texto das respostas dos agentes | Não permite comparação numérica posterior (`run.reproduces(...)`), violando o princípio do Research Core. |

## Decisão

### 1. Separação de Camadas

O módulo de workflows é criado no diretório `workflows/quantlab_workflows`, como um pacote satélite ao motor, similar ao `quantlab_connectors`:
- O pacote `quantlab_workflows` importa `quantlab` e `quantlab_connectors`.
- O motor `engine/quantlab` **nunca importa `quantlab_workflows`**. Essa restrição é verificada por análise de AST em `tests/test_architecture.py`.

### 2. A Estrutura dos 5 Elementos

Todo workflow inteligente no QuantLab é estruturado formalmente em 5 elementos:

1. **Gatilho (`TriggerEvent`):** O evento que dispara a execução. Pode ser manual (iniciado pelo pesquisador via prompt), temporal (cron diário/semanal), anomalia de mercado (volatilidade ou drawdown excedendo limiar) ou webhook externo.
2. **Contexto (`WorkflowContext`):** Dados de mercado canônicos validados com `CleaningReport`, parâmetros iniciais, hipótese em linguagem natural, séries temporais e impressão digital SHA-256 (`hash_data`).
3. **Decisão Inteligente (`AgentGraph` / `LLMProvider`):** Agentes com papéis especializados:
   - `HypothesisAgent`: traduz perguntas intuitivas em hipóteses científicas formais compatíveis com `quantlab.research.Experiment`.
   - `QuantAgent`: avalia métricas estatísticas (retornos, volatilidade, Sharpe, VaR/CVaR) e identifica regimes de cauda.
   - `DynamicsAgent`: avalia expoentes de Lyapunov, estabilidade de equilíbrios e dinâmica não linear.
   - `SynthesizerAgent`: compila o parecer analítico e julga se os dados sustentam ou refutam a hipótese.
4. **Ação (`WorkflowAction`):** Execução do cálculo matemático determinístico via `quantlab.research.run_experiment(experiment, fn)` e geração de visualizações interativas via `quantlab.visualization`.
5. **Registro (`WorkflowRecord`):** Persistência auditável do `ExperimentRun`, semente `SeedManager`, hash dos dados, transcrição do raciocínio dos agentes e serialização JSON-friendly via `to_dict()` e `from_dict()`.

### 3. Integração com Orquestradores Externos (n8n)

Para permitir automações visuais e integração com ferramentas corporativas (Slack, e-mail, feeds de notícias, cron):
- O QuantLab fornece templates de workflows para **n8n**, acionando endpoints do backend ou scripts CLI de workflows.
- O n8n gerencia os gatilhos externos e integrações de mensageria, delegando o processamento científico e a tomada de decisão agêntica aos módulos do QuantLab.

## Consequências

### Positivas
- Preservação integral do isolamento do motor científico (RULE 002).
- Garantia de reprodutibilidade: toda análise de IA culmina em um `ExperimentRun` imutável com `data_hash` e controle de sementes (RULE 017).
- Suporte a múltiplos provedores de LLM e execução de testes 100% offline via mocks sem custo de API.
- Facilidade de automação de rotinas de análise quantitativa e simulação dinâmica.

### Negativas / Limitações
- Chamadas a LLMs reais introduzem latência de rede e custos de token quando não executadas com modelos locais (Ollama).
- A calibração de prompts para hipóteses científicas exige rigor para evitar formulações vagas ou não refutáveis.
