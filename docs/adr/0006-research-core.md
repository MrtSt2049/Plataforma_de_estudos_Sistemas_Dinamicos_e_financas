# ADR 0006 — Research Core: sementes, experimentos e reprodução

- **Status:** aceita.
- **Data:** 2026-11-20

## Contexto

A RULE 017 exige que experimentos aleatórios permitam controlar a semente e que parâmetros, versões e dados sejam registrados. O README define o Research Core da 0.1 como registro de experimentos e parâmetros, controle de sementes e hipóteses documentadas junto dos resultados. O [plano de desenvolvimento](../plano-de-desenvolvimento.md) (item 1.2) prevê `SeedManager`, `Experiment` e `ExperimentRun`, e o esquema da Fase 3 já prevê as tabelas `experiments` e `experiment_runs`.

## Problema

1. Como derivar números aleatórios de uma única semente registrada, sem estado global e sem que uma mudança no experimento altere números já obtidos?
2. Como provar que os dados de entrada de um resultado são os mesmos meses depois, se a fonte (Yahoo) revisa preços passados?
3. Como registrar um experimento de forma imutável, serializável e sem acoplar o motor a banco de dados ou a framework (RULE 002)?
4. O que significa "reproduzir" um resultado em ponto flutuante?

## Alternativas consideradas

| Decisão | Alternativa descartada | Motivo |
|---|---|---|
| Fluxos nomeados a partir de `SeedSequence` com chave derivada de SHA-256 | `np.random.seed(...)` global | Estado global: qualquer chamada em outro lugar muda os números. |
| | `SeedSequence.spawn(n)` numerado pela ordem de criação | Acrescentar um fluxo no meio do código desloca todos os seguintes e invalida resultados já registrados. |
| | `hash(nome)` do Python como chave | É aleatorizado a cada processo (`PYTHONHASHSEED`), então a mesma semente daria números diferentes a cada execução. |
| Hash SHA-256 do conteúdo canônico dos dados | `pd.util.hash_pandas_object` | O algoritmo é detalhe interno do pandas e pode mudar entre versões, quebrando hashes já registrados. |
| | Hash de `pickle` ou de `to_parquet` | Dependem da versão das bibliotecas e de metadados irrelevantes. |
| `to_dict`/`from_dict` como fronteira de persistência | Gravar JSON, SQLite ou Parquet dentro do motor | O armazenamento é responsabilidade do backend e do Supabase (RULE 001 e 002). O motor entrega dados simples e quem está acima decide onde guardar. |

## Decisão

### `SeedManager` (`quantlab.research.seeds`)

- Recebe **uma semente raiz** (inteiro em `[0, 2^53 − 1]`) e entrega geradores `numpy.random.Generator` **nomeados**: `seeds.generator("ruido")`.
- O gerador é `default_rng(SeedSequence(semente, spawn_key=chave(nome)))`, onde `chave(nome)` são os 16 primeiros bytes do SHA-256 do nome, lidos como 4 inteiros de 32 bits. O `SeedSequence` foi projetado para que pares `(entropia, spawn_key)` distintos produzam fluxos independentes, mesmo com sementes vizinhas como 1, 2 e 3.
- Cada chamada devolve um gerador **no início** do fluxo: o resultado depende só de `(semente, nome)` e nunca de quantos números já foram sorteados.
- O limite `2^53 − 1` é o maior inteiro que o JavaScript representa sem perda. Como a semente vai para JSON e para a interface web em TypeScript, uma semente maior seria arredondada em silêncio no navegador e deixaria de reproduzir o experimento.

### `hash_data` (`quantlab.research.hashing`)

SHA-256 sobre três partes com prefixo de tamanho (cabeçalho com nomes, índice e valores), normalizadas para que **dados iguais deem hashes iguais**:

- valores convertidos para `float64` em ordem de bytes little-endian (então `1` e `1.0` são o mesmo dado);
- `-0.0` vira `0.0`, e todo NaN vira um único NaN, qualquer que seja o padrão de bits;
- índice de datas convertido para UTC e para nanossegundos, porque o pandas escolhe resoluções diferentes (`s`, `ms`, `us`, `ns`) entre versões;
- a ordem das linhas e das colunas, os nomes das colunas, do índice e da série e o formato de um array **fazem parte** do hash.

Tipos não numéricos, booleanos, complexos e índices que não sejam datas, inteiros ou textos são rejeitados com `TypeError`, em vez de serem convertidos em silêncio.

### `Experiment`, `ExperimentRun`, `run_experiment` (`quantlab.research.experiment`)

- `Experiment` é a **definição** e é imutável: nome, **hipótese (obrigatória e não vazia)**, modelo, parâmetros, semente, `data_hash` opcional, versão do motor e data de criação em UTC. Os campos seguem o item 1.2 do plano. O mapeamento para as colunas de `experiments` e `experiment_runs` (o item 3.1 coloca `seed` e `data_hash` em `experiment_runs`) é decisão da Fase 3.
- Os parâmetros aceitam apenas valores compatíveis com JSON (`None`, `bool`, `int`, `float` finito, `str`, listas e dicionários com chaves `str`). Escalares e arrays do NumPy são convertidos. O experimento guarda uma cópia **profundamente somente leitura**: alterar o dicionário original depois não muda o experimento.
- `ExperimentRun` é uma **execução**: métricas (números finitos), versões de Python, plataforma, NumPy, SciPy, pandas e do motor, instante de início e duração em milissegundos.
- `run_experiment(experimento, funcao)` chama `funcao(parametros, seeds)` e registra o resultado. **Erros da função propagam sem alteração**: uma execução que falhou não vira resultado, e nenhuma falha é escondida (RULE 010).
- `to_dict()` e `from_dict()` produzem e leem apenas dicionários, listas, números, textos e datas ISO-8601, e `from_dict` valida tudo de novo. É a fronteira com as camadas de persistência.

### O que significa "reproduzir"

`run.reproduces(outra)` compara **as métricas** de duas execuções:

- A tolerância padrão é **zero** (igualdade exata). Para comparar entre máquinas ou versões de bibliotecas, o chamador passa `rtol` e `atol` explícitos (RULE 014). A regra é a de `math.isclose`.
- As duas execuções precisam ter o **mesmo modelo, parâmetros, semente e `data_hash`**. Caso contrário, a comparação levanta `InputValidationError`, porque métricas de experimentos diferentes não dizem nada sobre reprodutibilidade.
- Título, hipótese, data e **versão do motor ficam fora da comparação**: refazer um resultado antigo com um motor novo é justamente o uso esperado.
- `metric_differences` devolve quais métricas diferem, com os dois valores, e marca com `None` a que existe só de um lado.

## Consequências e limites

- **A reprodução depende da disciplina de quem escreve a função.** O motor entrega os fluxos, mas não impede que a função use `np.random.default_rng()` sem semente ou o estado global. Nesse caso a reprodução falha, e `reproduces` acusa a diferença (há um teste para isso). Ele não consegue provar que uma função é determinística, só detectar quando ela não é.
- **Igualdade exata entre plataformas não foi verificada.** Os testes rodaram no Windows, com Python 3.12 e 3.13. Funções da biblioteca matemática e do BLAS podem diferir nos últimos dígitos em outros sistemas ou processadores. Por isso o ambiente é registrado e a tolerância é explícita.
- **Estabilidade dos hashes.** Os valores de referência no teste (`tests/research/test_hashing.py`) e as saídas brutas do PCG64 (`test_seeds.py`) estão fixados como regressão: se mudarem, resultados já registrados deixam de reproduzir. A normalização da resolução de datas foi verificada entre `s`, `ms`, `us` e `ns` no pandas 3.1; outras versões do pandas não foram testadas.
- **`NumPy` não promete estabilidade de fluxo para `Generator`** entre versões. O `SeedSequence` e o PCG64 bruto são estáveis na prática, e os métodos de alto nível (`normal`, `uniform`) podem mudar o resultado entre versões do NumPy. A versão do NumPy fica registrada em `environment`.
- **Pendente, fora desta decisão:**
  - Referências a **artefatos** (gráficos, relatórios) das execuções e a serialização do `CleaningReport` junto do experimento. Pertencem à integração com o Storage (bucket `experiment-artifacts`, Fase 3). Por enquanto, o `data_hash` da série limpa já denuncia qualquer mudança de política de limpeza.
  - Persistência (banco, arquivos) e API: Fases 3 e 4.
  - Métricas não escalares (séries, matrizes): a 0.1 aceita só números finitos.
