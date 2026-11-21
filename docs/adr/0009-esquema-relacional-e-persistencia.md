# ADR 0009 — Esquema relacional, dono das migrações e acesso do backend

- **Status:** aceita. Um ponto fica em aberto até a fase S2 (como o papel do backend enxerga as linhas; ver "Pendências").
- **Data:** 2026-11-21
- **Decisões consolidadas:** D2, D3, D4 e D10 do [plano de implantação](../plano-de-implantacao.md) (seção 3).

## Contexto

O motor `0.1.0` produz registros de pesquisa como dicionários JSON (`Experiment.to_dict`, `ExperimentRun.to_dict`, [ADR 0006](0006-research-core.md)) e deixa a persistência para as camadas acima (RULE 001 e 002). A Fase 3 do [plano de desenvolvimento](../plano-de-desenvolvimento.md) previa as tabelas `projects`, `experiments`, `experiment_runs` e `dataset_records`, mas colocava `seed` e `data_hash` em `experiment_runs`.

Três sistemas podem querer criar tabelas no mesmo Postgres: as migrações do Supabase, o `migrate` do Django e o próprio painel. Tudo o que fica no esquema `public` pode ser alcançado pela API de dados (PostgREST), conforme as permissões concedidas. A RULE 006 exige registrar a decisão antes da primeira migração.

## Problema

1. Onde ficam `seed` e `data_hash`: na definição do experimento ou na execução?
2. Quem é dono do esquema do domínio: o Supabase ou o Django?
3. Com que identidade o Django acessa o banco, e qual o papel da RLS?
4. Onde ficam as tabelas internas do Django, para não serem expostas pela API de dados?

## Alternativas consideradas

| Decisão | Alternativa descartada | Motivo |
|---|---|---|
| `seed` e `data_hash` em `experiments` | Em `experiment_runs` (plano antigo, item 3.1) | No motor eles são campos de `Experiment`, e `ExperimentRun.reproduces` só compara execuções de experimentos com a mesma configuração (`_same_setup`: modelo, parâmetros, semente e dados). Guardá-los na execução permitiria execuções "do mesmo experimento" com sementes diferentes, o que o motor considera estudos distintos. |
| Migrações do Supabase são donas do esquema | Migrações do Django (`managed = True`) | As políticas RLS, os `GRANT` e as restrições `check` são SQL do Postgres e são testadas com pgTAP. Dois sistemas de migração para as mesmas tabelas divergem (RULE 029). |
| Papel dedicado `quantlab_backend`, com filtro por dono no Django e RLS como segunda camada | Django conectado como `postgres` | `postgres` tem privilégios muito acima do necessário; um erro no backend teria alcance total. |
| | Django assumindo o papel do usuário a cada requisição (`set role authenticated` + claims) | Mais seguro em tese, mas exige cuidado com o pooler e com transações. Fica como evolução, a avaliar depois do MVP. |
| Esquema `backend` para as tabelas do Django | Deixar as tabelas do Django em `public` | `django_migrations`, sessões e afins ficariam alcançáveis pela API de dados se algum `GRANT` padrão vazasse. |
| Navegador só lê pela API de dados; toda escrita passa pelo Django | Escrita direta do navegador com RLS de `insert`/`update` | A validação científica (semente no intervalo, parâmetros JSON, hash SHA-256, imutabilidade do experimento) mora no backend e no motor (RULE 038). Duplicá-la em políticas SQL violaria a RULE 003. |

## Decisão

### 1. Tabelas do domínio (esquema `public`)

- `projects`, `experiments`, `experiment_runs` e `dataset_records`, com chaves `uuid` (`gen_random_uuid()`), `timestamptz`, `jsonb` para parâmetros, métricas e ambiente, e índice em toda chave estrangeira.
- `experiments` guarda `name`, `hypothesis` (não vazia), `model`, `parameters`, `seed` (`bigint` em `[0, 2^53 − 1]`, o `MAX_SEED` do motor), `data_hash` (opcional, `^[0-9a-f]{64}$`) e `engine_version`.
- `experiment_runs` guarda `metrics`, `environment`, `started_at` e `execution_time_ms` (`>= 0`), espelhando `ExperimentRun`.
- `dataset_records` guarda a proveniência de `PriceMetadata`, com `adjusted` e `frequency` obrigatórios (RULE 040), e `unique (user_id, data_hash)`.
- **Chaves estrangeiras compostas** `(experiment_id, user_id)` e `(project_id, user_id)`: uma execução nunca aponta para um experimento de outro usuário, mesmo que o backend erre.
- **Experimentos e execuções são imutáveis.** O Django não expõe `PUT`/`PATCH`, e o papel do backend **não tem `UPDATE`** em `experiments` nem em `experiment_runs`, o que impede qualquer alteração pela aplicação. Isso é mais simples que um gatilho (não há lógica a manter) e foi o que a migração inicial implementou. Mudar a configuração é criar outro experimento.

O SQL de referência está na fase S2 do plano de implantação. A primeira migração deve segui-lo.

### 2. Dono do esquema

- Só `supabase/migrations/` cria e altera tabelas do domínio, políticas e permissões.
- Os modelos do Django para essas tabelas usam `managed = False`.
- Migração aplicada nunca é editada; correção é migração nova.

### 3. Acesso

- **Navegador** (`anon`, `authenticated`): `revoke all` explícito e depois `grant select` só para `authenticated`. Políticas `to authenticated using ((select auth.uid()) = user_id)`. Nenhuma política de escrita. `anon` não lê nada.
- **Django** (`quantlab_backend`): `select, insert, update, delete` em `projects` e `dataset_records`; só `select, insert, delete` em `experiments` e `experiment_runs`. Nada além. O papel é criado **sem login**, e a senha é definida fora do Git ([runbook](../runbook-supabase.md)). Toda consulta filtra por `user_id` extraído do JWT validado ([ADR 0007](0007-chaves-supabase-jwks-e-frontend.md)), com teste automatizado que falha se uma rota esquecer o filtro.
- **Chave secreta** (`sb_secret_…`): só no servidor e só quando o Storage entrar (S4).

### 4. Esquema `backend`

```sql
create schema backend;
grant usage, create on schema backend to quantlab_backend;
alter role quantlab_backend set search_path = backend, public;
```

O `migrate` do Django cria as próprias tabelas em `backend`, que não é exposto pela API de dados.

## Pendências

- **Como `quantlab_backend` enxerga as linhas com RLS ativa.** Duas opções: (a) `alter role quantlab_backend bypassrls`, se o Supabase permitir isso num papel criado pelo usuário; (b) uma política `to quantlab_backend using (true) with check (true)` por tabela. Não verificado. Decidir na S2 testando no projeto de dev; a opção (b) funciona em qualquer caso e mantém a decisão visível no SQL.
- O papel `quantlab_backend` precisa aparecer no pooler. Conferir na S5 se o usuário `quantlab_backend.<ref>` autentica pelo pooler em modo sessão.

### Situação da migração inicial (2026-11-21)

- **Escolhida a opção (b)** para o papel do backend: uma política `to quantlab_backend using (true) with check (true)` por tabela.
- A migração `supabase/migrations/20261121120116_create_core_schema.sql` foi verificada num **Postgres 16 embutido e descartável**, com atalhos para `auth.users`, `auth.uid()` e os papéis `anon` e `authenticated`: 34 verificações, 0 falhas (RLS ativa, isolamento entre dois usuários nas quatro tabelas, anônimo sem leitura, navegador sem escrita, imutabilidade, chaves compostas, cada `check` e a cascata).
- **Não foi executada na pilha real do Supabase** (o Docker Desktop estava desligado) e **não foi aplicada** em nenhum projeto. O teste pgTAP em `supabase/tests/database/` está escrito, mas não foi executado.

## Consequências

### Positivas
- Paridade com o motor: uma linha de `experiments` é um `Experiment.to_dict()`, e `reproduces` tem os dados de que precisa.
- Isolamento entre usuários garantido em três camadas: filtro do Django, chave composta e RLS.
- Um só sistema de migração para o domínio, testável no CI com pgTAP.

### Negativas
- Mudar um modelo do Django exige escrever a migração SQL antes, à mão.
- O filtro por dono no Django é obrigatório e precisa de teste, porque `quantlab_backend` não é restringido pela RLS da mesma forma que `authenticated`.
