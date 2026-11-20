# ADR 0007 — Chaves do Supabase, validação de JWT por JWKS e variáveis do frontend

- **Status:** aceita. A autenticação segue a RULE 025. O frontend segue o plano original (Vite), confirmado pelas variáveis `VITE_*` do `.env` do responsável.
- **Data:** 2026-11-20

## Contexto

O projeto Supabase de desenvolvimento foi criado em 2026-11-19 e o `.env` local foi configurado. O que foi observado em 2026-11-20:

- **Chaves.** O `.env` tem a URL do projeto, uma chave `anon` no formato antigo (JWT assinado com HS256) e uma chave nova `sb_publishable_...`. Chegou a ter também uma chave `sb_secret_...` e o segredo JWT, ambos removidos pelo responsável.
- **Assinatura de tokens.** O endereço público de chaves do projeto (`/auth/v1/.well-known/jwks.json`) respondeu 200 e publica **uma chave EC, ES256, curva P-256**. Isso indica que o projeto usa chaves de assinatura assimétricas. A chave `anon` antiga tinha assinatura HS256 válida com o segredo JWT antigo, ou seja, o segredo legado existia e ainda assina as chaves antigas.
- **Frontend.** Por um tempo o `.env` usou `NEXT_PUBLIC_*`, nomes do roteiro do Supabase para Next.js, e o `package.json` na raiz instalou `@supabase/ssr`. O responsável voltou para `VITE_SUPABASE_URL` e `VITE_SUPABASE_PUBLISHABLE_KEY`.

Não foi verificado qual chave assina os tokens de **usuário** emitidos pelo Supabase Auth, porque isso exige um token real. A aba "JWT Signing Keys" do painel mostra a chave atual.

## Problema

1. Como o Django deve validar os tokens, conforme a RULE 025 ("estratégia compatível com a configuração atual do projeto")?
2. Que credenciais precisam existir no ambiente agora, e quais não devem existir?
3. Como o frontend recebe a configuração pública do Supabase?

## Alternativas consideradas

| Tema | Alternativa | Avaliação |
|---|---|---|
| Validação de JWT | **A. JWKS com lista fixa de algoritmos (ES256)** | Usa só chaves públicas, nada secreto no backend, e acompanha a rotação de chaves pelo `kid`. É o que o plano (item 4.2) já previa. |
| | B. Segredo compartilhado HS256 | Exige guardar um segredo que também forja chaves antigas com qualquer papel, inclusive `service_role`. Não corresponde à configuração atual de assinatura. |
| | C. Consultar o Supabase Auth a cada requisição | Uma chamada de rede por requisição e dependência de disponibilidade. |
| Frontend | **A. Vite + React + TypeScript** (plano original) | SPA estática, simples de publicar. A sessão fica no navegador, e basta o `supabase-js`. |
| | B. Next.js | Descartada: o responsável voltou para as variáveis `VITE_*`. Exigiria um servidor Node em produção e o `@supabase/ssr`. |

## Decisão

### Autenticação

- O backend valida o token com as **chaves públicas do projeto (JWKS)**, escolhendo a chave pelo `kid` do cabeçalho, com cache e nova busca limitada quando aparecer um `kid` desconhecido.
- **Lista fixa de algoritmos: apenas `ES256`.** `none`, `HS*` e `RS*` são rejeitados, o que evita a confusão de algoritmo (um atacante apresentar um token HS256 assinado com a chave pública).
- São verificados assinatura, expiração (`exp`), emissor (`iss`), audiência (`aud`) e o `sub` como UUID do usuário (RULE 026). Pela documentação do Supabase, os valores esperados são `iss = <SUPABASE_URL>/auth/v1` e `aud = authenticated`. **Isso deve ser confirmado com um token real na Fase 4**, e a biblioteca de JWT também será escolhida lá.
- **Nenhum segredo de assinatura é guardado.** O `SUPABASE_JWT_SECRET` saiu do `.env` e do `.env.example`.

### Credenciais no ambiente

- O `.env.example` espelha o `.env`: só o que está em uso. Chave secreta (`sb_secret_...`, que substitui a `service_role`), buckets e Redis ficam **comentados**, com a fase em que entram (3.2 e 6).
- A chave secreta ignora o RLS: só o backend a usa, nunca em variável `VITE_` (RULE 028).
- Só variáveis `VITE_*` chegam ao navegador: `VITE_SUPABASE_URL` e `VITE_SUPABASE_PUBLISHABLE_KEY`, ambos valores públicos. Quando o frontend chamar o Django, entra `VITE_API_BASE_URL`.
- `SUPABASE_ANON_KEY` (backend) ainda é a chave antiga. Quando o backend passar a usar a `sb_publishable_`, é possível desativar as chaves antigas no painel, o que torna inútil o segredo legado. Essa é uma ação do responsável no painel do Supabase.

## Consequências

- O `package.json` e o `node_modules/` estão na **raiz** do repositório, e o plano prevê o frontend em `frontend/`. A mudança de lugar fica para quando o app existir. O `@supabase/ssr`, instalado ali, não é necessário no Vite. O `.gitignore` agora ignora `node_modules/` e `.next/`.
- O plano de desenvolvimento (item 4.2) e o README descrevem a validação por JWKS com `ES256`.
- **Pendências do responsável:** (1) trocar `SUPABASE_ANON_KEY` pela chave publishable e desativar as chaves antigas no painel; (2) preencher `DATABASE_URL`, que continua com valor de exemplo; (3) conferir em "JWT Signing Keys" qual chave assina os tokens de usuário.
