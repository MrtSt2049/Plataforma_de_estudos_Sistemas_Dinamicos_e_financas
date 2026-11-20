# ADR 0005 — Fonte online de preços: Yahoo Finance, fora do motor

- **Status:** aceita.
- **Data:** 2026-11-20
- **Resolve:** a proposta pendente do [ADR 0002](0002-camada-de-dados-de-mercado.md) (fonte externa da 0.1) e a decisão sobre onde colocar um provedor online, que aquele ADR deixou em aberto.

## Contexto

O ADR 0002 definiu a interface `PriceProvider`, o esquema canônico e o pipeline de padronização, verificação e limpeza, mas deixou a **fonte externa** em aberto e pediu que a escolha fosse registrada junto com uma decisão sobre a RULE 002, que proíbe o motor de depender de APIs HTTP. O responsável pelo projeto escolheu o **yfinance**.

## Problema

1. O yfinance acessa a API do Yahoo por HTTP. Onde esse código deve morar sem violar a RULE 002?
2. Como manter o contrato de erros do `PriceProvider` (RULE 010) com uma biblioteca que, por padrão, esconde falhas?
3. Como tratar a fonte não oficial sem comprometer a reprodutibilidade (RULE 017)?

## Alternativas consideradas

| Alternativa | Avaliação |
|---|---|
| **A. Provedor dentro do motor, com exceção à RULE 002 só para o subpacote `quantlab.data.providers`** | Uso mais simples (`from quantlab.data import ...`). Mas enfraquece uma regra obrigatória, que só o responsável pode alterar (hierarquia de regras), e faz o motor importar uma biblioteca de rede. |
| **B. Provedor dentro do motor, com o download injetado** (o motor só transforma, quem chama fornece uma função de download) | Respeita a RULE 002, mas empurra a chamada ao yfinance para quem usa, e cada usuário reescreveria o tratamento de erros. |
| **C. Provedor num pacote separado que depende do motor** (escolhida) | O motor continua sem nenhuma dependência de rede. A dependência vai em um sentido só: o conector importa o motor e implementa o `PriceProvider`. Nenhuma regra é alterada. |
| **D. Esperar o backend Django e colocar a coleta lá** | O backend ainda não existe, e o motor ficaria sem fonte online utilizável na 0.1. |

## Decisão

- Criar o pacote **`quantlab_connectors`** em `connectors/`, **fora de `engine/quantlab`**, com o módulo `quantlab_connectors.yahoo` e a classe `YahooPriceProvider`, que implementa `quantlab.data.PriceProvider`.
- O motor **não importa** `quantlab_connectors`, `yfinance` nem `curl_cffi`. O teste de arquitetura (`tests/test_architecture.py`) passa a barrar esses três nomes dentro de `engine/quantlab`.
- O yfinance é uma dependência **opcional** (extra `yahoo`: `uv sync --extra yahoo`) e entra no grupo de desenvolvimento para os testes. O pacote `quantlab_connectors` não importa nenhum conector automaticamente, então só quem usa o Yahoo precisa do extra, e a falta dele gera uma mensagem que explica como instalar.
- A validação de símbolo, que o provedor de CSV já tinha, foi movida para `quantlab.data.providers.base` (`SYMBOL_PATTERN` e `validate_symbol`) para os dois provedores a compartilharem (RULE 003). A mensagem de erro não mudou.
- `PriceProvider.available_symbols()` passa a documentar que fontes web abertas **levantam `NotImplementedError`**. O Yahoo não tem catálogo, e devolver uma tupla vazia sugeriria que a fonte não entrega nada.

### Comportamento do provedor

- `adjusted` é obrigatório e sem valor padrão (RULE 040). `True` usa `auto_adjust=True` do Yahoo (preços ajustados por desdobramentos e dividendos). `False` usa `auto_adjust=False`. O Yahoo decide quais eventos tratar como desdobramento, então `False` não garante o preço efetivamente negociado.
- O contrato de datas é **inclusivo** nos dois extremos. O `end` do yfinance é exclusivo, então o provedor pede `end + 1 dia` e depois filtra pela data de cada barra.
- Sem nenhuma data, o yfinance devolve **só o último mês**. O provedor pede `period="max"` para que "sem limites" signifique o histórico completo.
- Datas de barras diárias mantêm a data local da bolsa (o fuso é descartado sem converter para UTC), como em `standardize_ohlcv`.
- Os dados chegam como o Yahoo entrega. Duplicatas e valores ausentes **não** são removidos: isso continua sendo papel de `check_ohlcv_integrity` e `clean_ohlcv`.
- A moeda vem dos metadados do Yahoo e é `None` quando ausente ou inválida. O Yahoo usa códigos como `GBp` (pence), que não são ISO 4217.

### Mapeamento de erros (RULE 010)

Por padrão o yfinance **registra a falha no log e devolve uma tabela vazia**, o que faria uma queda de rede parecer "sem dados no período". O provedor liga a opção global `yf.config.debug.hide_exceptions = False` apenas durante a chamada, restaura o valor anterior ao terminar e usa um travamento (`threading.Lock`) para a troca não competir entre threads. Efeito colateral aceito: buscas simultâneas no mesmo processo são serializadas, o que também evita estourar o limite de requisições do Yahoo.

O mapeamento foi definido a partir de chamadas reais (yfinance 1.8.0, 2026-11-20):

| Observado | Resultado |
|---|---|
| `HTTPError` 404 do `curl_cffi` (ticker inexistente, como `XXXX3.SA`) | `SymbolNotFoundError` |
| `YFTzMissingError` (ticker sem fuso, como `LEHMQ`) | `SymbolNotFoundError` |
| `YFPricesMissingError` (ticker válido, período sem pregão) | série **vazia** com colunas canônicas |
| `YFRateLimitError` | `DataSourceError` |
| Outros `YFException` e `OSError` (rede, tempo esgotado, HTTP diferente de 404) | `DataSourceError` |
| Conteúdo que não vira o esquema canônico | `DataSourceError` |
| Qualquer outra exceção | **não é traduzida**, propaga com o tipo original |

Só os tipos de falha observados são traduzidos. Esconder exceções desconhecidas atrás de um `DataSourceError` genérico violaria a RULE 010.

## Justificativa

A alternativa C é a única que mantém a RULE 002 intacta, entrega um provedor pronto para uso e não depende de um backend que ainda não existe. A mudança custa um pacote a mais e um `from quantlab_connectors.yahoo import ...` no lugar de um import do motor. Se o responsável preferir a alternativa A, a migração é mecânica: mover o módulo e abrir a exceção no teste de arquitetura, com a decisão registrada num novo ADR.

## Consequências

- **Fonte não oficial.** O yfinance usa endpoints do Yahoo sem contrato e pode quebrar sem aviso. Os termos de uso do Yahoo restringem uso comercial e redistribuição dos dados: o uso aqui é de estudo e pesquisa, e quem for além disso deve conferir os termos vigentes.
- **Reprodutibilidade.** O Yahoo revisa preços passados (por exemplo, ao aplicar um novo ajuste de dividendos). Para reproduzir um resultado meses depois é preciso guardar a série usada, ou ao menos o `data_hash` dela no Research Core, e não apenas o símbolo e as datas. Em 2024-01-02, por exemplo, a abertura de `PETR4.SA` veio como 25,80 com ajuste e 37,44 sem ajuste, na consulta de 2026-11-20: o mesmo pedido feito em outra data pode devolver números diferentes. O armazenamento em Parquet consultado com DuckDB, recomendado no ADR 0002, continua **pendente**.
- **Barra incompleta.** Com o mercado aberto, a última barra pode ainda estar em formação.
- **Testes.** Os testes unitários usam um `Ticker` falso, sem rede, que reproduz o comportamento observado. Há também testes de contrato contra o Yahoo real, marcados com `network` e **desligados por padrão** (`uv run pytest -m network`). Eles verificam forma e comportamento, nunca valores de preço. Foi um deles que revelou que `get_history_metadata()` devolve um `Mapping` que não é `dict`.
- **Dependência pesada.** O yfinance traz `curl_cffi`, `requests`, `lxml`, `protobuf` e outras. Por isso é um extra opcional.
- **Evolução.** Outros conectores (por exemplo, séries do Banco Central para a taxa livre de risco, citadas no ADR 0002) entram em `connectors/` pelo mesmo caminho: um módulo novo que implementa a interface do motor.
