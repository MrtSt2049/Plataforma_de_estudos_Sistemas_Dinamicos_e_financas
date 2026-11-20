# ADR 0002 — Camada de dados de mercado e escolha da fonte externa

- **Status:** aceita. A interface e o provedor local foram aceitos em 2026-11-19. A fonte externa foi decidida em 2026-11-20: yfinance, num pacote fora do motor ([ADR 0005](0005-fonte-online-yahoo-finance.md)).
- **Data:** 2026-11-19

## Contexto

O módulo Market Data da versão 0.1 precisa baixar séries históricas, consultar ativos, limpar valores ausentes e duplicados, validar a integridade e padronizar as séries. O README deixa a fonte de dados da 0.1 em aberto até uma decisão registrada em ADR.

As funções de análise (retornos, risco, correlação) já existem e recebem `pandas.Series` ou `DataFrame` limpos. Falta a camada entre a fonte e essas funções.

## Problema

1. Como isolar a análise da fonte de dados, para que trocar de fonte não mude nenhum cálculo?
2. Onde e como limpar os dados sem esconder decisões que afetam os resultados?
3. Qual fonte externa usar na 0.1?

## Decisão (aceita): interface, esquema e processamento

- **Esquema canônico** (`quantlab.data.schema`): índice `DatetimeIndex` chamado `date`, sem fuso horário e ordenado. Colunas são um subconjunto de `open, high, low, close, volume`, sempre com `close`, em float64. Os metadados registram símbolo, fonte, frequência, moeda e se os preços são ajustados (RULE 040). O campo `adjusted` é obrigatório nos provedores e não tem valor padrão.
- **Interface `PriceProvider`** (um `Protocol`): `source`, `available_symbols()` e `fetch(symbol, start, end) -> PriceHistory`. O contrato de erros separa símbolo inexistente (`SymbolNotFoundError`), falha da fonte (`DataSourceError`, erro de infraestrutura) e requisição inválida (`InputValidationError`), conforme a RULE 010.
- **Provedor local `CsvPriceProvider`:** um arquivo CSV por símbolo, com mapeamento de colunas e suporte a arquivos no formato brasileiro (`;` e vírgula decimal). Ele permite trabalhar com dados exportados de qualquer fonte e serve de referência para os testes. O símbolo é validado para impedir acesso a caminhos fora do diretório (`../`).
- **Pipeline explícito em quatro passos:**
  1. `standardize_ohlcv` converte nomes, tipos, datas e ordem, sem remover nada;
  2. `check_ohlcv_integrity` relata problemas sem alterar os dados;
  3. `clean_ohlcv` aplica políticas **obrigatórias e explícitas** (`duplicates="first"|"last"`, `missing="drop"|"ffill"`) e devolve um relatório do que mudou;
  4. as funções de análise rejeitam dados sujos em vez de corrigi-los.

### Justificativa

A limpeza muda os números de todos os resultados seguintes. O preenchimento para frente, por exemplo, cria retornos zero e reduz a volatilidade. Por isso nenhuma etapa limpa dados de forma implícita, e o relatório de limpeza pode ser guardado junto do experimento (RULE 017). Problemas que exigem julgamento, como uma máxima abaixo da mínima ou um salto de 60% que pode ser um desdobramento não ajustado, são apenas relatados.

## Proposta original: fonte externa da 0.1 (resolvida no ADR 0005)

> **Atualização (2026-11-20):** o responsável escolheu o **yfinance**. A decisão, o mapeamento de erros e o local do código estão no [ADR 0005](0005-fonte-online-yahoo-finance.md). A análise abaixo é mantida como registro do que foi comparado.

O código da interface permite plugar qualquer uma das alternativas abaixo. Termos de uso, limites e cobertura mudam com o tempo e precisam ser conferidos no momento da decisão.

| Alternativa | Pontos a favor | Pontos contra |
|---|---|---|
| **yfinance** (cliente não oficial dos endpoints do Yahoo Finance) | Sem chave de API. Cobertura ampla, incluindo B3 (sufixo `.SA`) e índices. Fornece preços ajustados. | Não é uma API oficial: pode quebrar sem aviso. Os termos do Yahoo restringem uso e redistribuição. |
| **brapi.dev** | Foco em ativos da B3, API REST documentada. | Exige token. O plano gratuito tem limites de histórico e de requisições. |
| **Alpha Vantage, Tiingo e similares** | APIs oficiais, documentadas, com chave. | Exigem chave. Os planos gratuitos são restritos, e a cobertura da B3 varia. |
| **Banco Central (SGS)** | Oficial, gratuito, estável. | Não tem preços de ações. Serve para séries macro, como CDI e Selic, úteis como taxa livre de risco no Sharpe. É complementar, não substituto. |
| **Somente arquivos locais** (já implementado) | Reprodutível, sem dependência de rede nem de termos de terceiros. | O download é manual. |

**Critérios sugeridos:** cobertura dos ativos que serão estudados (B3, EUA, cripto), disponibilidade de preços ajustados, estabilidade da API, termos de uso compatíveis com um projeto público de estudo, e custo.

**Recomendação para discussão:** começar com arquivos locais, que já funcionam, e adicionar **um** provedor online escolhido por esses critérios. Os dados baixados devem ser gravados em Parquet (consultados com DuckDB, como prevê o README), o que torna cada experimento reprodutível mesmo que a fonte mude ou saia do ar.

## Consequências

- Trocar ou adicionar fontes exige apenas uma nova classe que implemente `PriceProvider`, sem tocar na análise.
- Cada provedor novo traz sua dependência (cliente HTTP ou biblioteca) e precisa de testes que não acessem a rede, com respostas gravadas.
- O teste de arquitetura (`tests/test_architecture.py`) proíbe bibliotecas HTTP no motor. Um provedor online exigia uma decisão explícita: abrir exceção para o subpacote `quantlab.data.providers` ou colocar os provedores online fora do motor. **Decidido no [ADR 0005](0005-fonte-online-yahoo-finance.md):** fora do motor, em `connectors/`, sem exceção à RULE 002.
